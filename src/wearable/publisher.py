from __future__ import annotations

import json
import logging
import time

from .config import WearableCfg
from .bno085 import BnoData

log = logging.getLogger(__name__)


class ImuPublisher:
    """
    publishes IMU sensor data over ZMQ PUB
    follows the same pattern as PosePublisher in localize.py
    """

    def __init__(self, cfg: WearableCfg) -> None:
        import zmq

        self._zmq      = zmq
        self._cfg      = cfg
        self._topic    = cfg.imu_sink.topic.encode("utf-8")
        self._socket   = zmq.Context.instance().socket(zmq.PUB)
        self._socket.setsockopt(zmq.SNDHWM, cfg.imu_sink.sndhwm)
        self._socket.setsockopt(zmq.LINGER, cfg.imu_sink.linger_ms)

        if cfg.imu_sink.bind:
            self._socket.bind(cfg.imu_sink.endpoint)
        else:
            self._socket.connect(cfg.imu_sink.endpoint)

        mode = "bind" if cfg.imu_sink.bind else "connect"
        log.info(
            "IMU publisher: %s %s topic=%s",
            mode,
            cfg.imu_sink.endpoint,
            cfg.imu_sink.topic,
        )

        self.drop_count = 0

    def publish(self, data: BnoData, button_pressed: bool) -> None:
        event: dict[str, object] = {
            "schema":         "uwb.sensors",
            "schema_version": 1,
            "timestamp":      time.time(),
            "device_id":      self._cfg.device_id,
            "button_pressed": button_pressed,
        }

        if data.valid:
            event["bno085"] = {
                "rotation_vector": {
                    "i":        data.quat_i,
                    "j":        data.quat_j,
                    "k":        data.quat_k,
                    "real":     data.quat_real,
                    "accuracy": data.quat_accuracy,
                },
                "game_rotation_vector": {
                    "i":    data.game_quat_i,
                    "j":    data.game_quat_j,
                    "k":    data.game_quat_k,
                    "real": data.game_quat_real,
                },
                "linear_acceleration": {
                    "x": data.lin_acc_x,
                    "y": data.lin_acc_y,
                    "z": data.lin_acc_z,
                },
                "accelerometer": {
                    "x": data.acc_x,
                    "y": data.acc_y,
                    "z": data.acc_z,
                },
                "gyroscope": {
                    "x": data.gyro_x,
                    "y": data.gyro_y,
                    "z": data.gyro_z,
                },
                "gravity": {
                    "x": data.grav_x,
                    "y": data.grav_y,
                    "z": data.grav_z,
                },
                "steps":            data.steps,
                "stability":        data.stability,
                "is_moving":        data.is_moving,
                "motion_magnitude": data.motion_magnitude,
            }

        payload = json.dumps(event, separators=(",", ":")).encode("utf-8")
        try:
            self._socket.send_multipart(
                [self._topic, payload],
                flags=self._zmq.NOBLOCK,
            )
            if self._cfg.console:
                moving = "moving" if (data.valid and data.is_moving) else "still"
                btn    = " BUTTON" if button_pressed else ""
                log.info(
                    "IMU device=%s %s mag=%.3f%s",
                    self._cfg.device_id,
                    moving,
                    data.motion_magnitude if data.valid else 0.0,
                    btn,
                )
        except self._zmq.Again:
            self.drop_count += 1
            if self.drop_count == 1 or (self.drop_count % 100) == 0:
                log.warning(
                    "IMU PUB dropping events due to backpressure (drops=%d)",
                    self.drop_count,
                )

    def close(self) -> None:
        self._socket.close()