from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class BnoData:
    """latest readings from BNO085"""
    # rotation vector (absolute, uses magnetometer)
    quat_i:        float = 0.0
    quat_j:        float = 0.0
    quat_k:        float = 0.0
    quat_real:     float = 1.0
    quat_accuracy: float = 0.0

    # game rotation vector (no magnetometer)
    game_quat_i:    float = 0.0
    game_quat_j:    float = 0.0
    game_quat_k:    float = 0.0
    game_quat_real: float = 1.0

    # linear acceleration — gravity removed (m/s^2)
    lin_acc_x: float = 0.0
    lin_acc_y: float = 0.0
    lin_acc_z: float = 0.0

    # raw accelerometer (m/s^2)
    acc_x: float = 0.0
    acc_y: float = 0.0
    acc_z: float = 0.0

    # gyroscope (rad/s)
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0

    # gravity vector (m/s^2)
    grav_x: float = 0.0
    grav_y: float = 0.0
    grav_z: float = 0.0

    # step counter
    steps: int = 0

    # stability classifier
    # 0=unknown 1=on_table 2=stationary 3=stable 4=motion
    stability: int = 0

    # computed motion state
    is_moving:        bool  = False
    motion_magnitude: float = 0.0

    valid: bool = False


class Bno085Reader:
    """
    reads BNO085 over I2C using CircuitPython adafruit_bno08x library
    computes motion state from gyro and linear acceleration
    """

    def __init__(
        self,
        i2c_bus: Optional[int] = None,
        fast_interval_ms: int = 10,
        slow_interval_ms: int = 200,
        motion_gyro_thresh: float = 0.05,
        motion_linacc_thresh: float = 0.08,
        motion_hold_frames: int = 10,
    ) -> None:
        self._i2c_bus            = i2c_bus
        self._fast_interval_ms   = fast_interval_ms
        self._slow_interval_ms   = slow_interval_ms
        self._gyro_thresh        = motion_gyro_thresh
        self._linacc_thresh      = motion_linacc_thresh
        self._hold_frames        = motion_hold_frames
        self._motion_hold_count  = 0
        self.ok                  = False
        self._bno                = None
        self._init()

    def _init(self) -> None:
        try:
            import board
            import busio
            from adafruit_bno08x import (
                BNO_REPORT_ROTATION_VECTOR,
                BNO_REPORT_GAME_ROTATION_VECTOR,
                BNO_REPORT_LINEAR_ACCELERATION,
                BNO_REPORT_ACCELEROMETER,
                BNO_REPORT_GYROSCOPE,
                BNO_REPORT_GRAVITY,
                BNO_REPORT_STEP_COUNTER,
                BNO_REPORT_STABILITY_CLASSIFIER,
            )
            from adafruit_bno08x.i2c import BNO08X_I2C

            if self._i2c_bus is None:
                i2c = busio.I2C(board.SCL, board.SDA)
                bus_label = "hardware I2C"
            else:
                from adafruit_extended_bus import ExtendedI2C as I2C

                i2c = I2C(self._i2c_bus)
                bus_label = f"/dev/i2c-{self._i2c_bus}"

            self._bno = BNO08X_I2C(i2c)

            fast_interval_us = self._fast_interval_ms * 1000
            slow_interval_us = self._slow_interval_ms * 1000

            self._bno.enable_feature(BNO_REPORT_ROTATION_VECTOR, fast_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_GAME_ROTATION_VECTOR, fast_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_LINEAR_ACCELERATION, fast_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_ACCELEROMETER, fast_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_GYROSCOPE, fast_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_GRAVITY, fast_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_STEP_COUNTER, slow_interval_us)
            time.sleep(0.02)
            self._bno.enable_feature(BNO_REPORT_STABILITY_CLASSIFIER, slow_interval_us)

            self.ok = True
            log.info("BNO085 initialised over %s", bus_label)

        except Exception as e:
            log.error("BNO085 init failed: %s", e)

    def read(self) -> BnoData:
        data = BnoData()
        if not self.ok or self._bno is None:
            return data

        try:
            qi, qj, qk, qr          = self._bno.quaternion
            ax, ay, az               = self._bno.acceleration
            lx, ly, lz               = self._bno.linear_acceleration
            gyx, gyy, gyz            = self._bno.gyro
            gvx, gvy, gvz            = self._bno.gravity
            gi, gj, gk, gr           = self._bno.game_quaternion

            data.quat_i        = qi
            data.quat_j        = qj
            data.quat_k        = qk
            data.quat_real     = qr
            data.quat_accuracy = 0.0

            data.game_quat_i    = gi
            data.game_quat_j    = gj
            data.game_quat_k    = gk
            data.game_quat_real = gr

            data.lin_acc_x = lx
            data.lin_acc_y = ly
            data.lin_acc_z = lz

            data.acc_x = ax
            data.acc_y = ay
            data.acc_z = az

            data.gyro_x = gyx
            data.gyro_y = gyy
            data.gyro_z = gyz

            data.grav_x = gvx
            data.grav_y = gvy
            data.grav_z = gvz

            data.steps     = self._bno.steps
            data.stability = self._bno.stability_classification

            # compute motion state
            gyro_mag   = math.sqrt(gyx**2 + gyy**2 + gyz**2)
            linacc_mag = math.sqrt(lx**2  + ly**2  + lz**2)
            data.motion_magnitude = max(gyro_mag, linacc_mag)

            motion_detected = (
                gyro_mag   > self._gyro_thresh or
                linacc_mag > self._linacc_thresh
            )

            if motion_detected:
                data.is_moving           = True
                self._motion_hold_count  = self._hold_frames
            elif self._motion_hold_count > 0:
                self._motion_hold_count -= 1
                data.is_moving           = True
            else:
                data.is_moving = False

            data.valid = True

        except Exception as e:
            log.warning("BNO085 read error: %s", e)

        return data
