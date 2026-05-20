from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ImuSinkCfg:
    enabled: bool = True
    endpoint: str = "tcp://127.0.0.1:5572"
    bind: bool = False
    topic: str = "sensors"
    sndhwm: int = 32
    linger_ms: int = 0


@dataclass(frozen=True)
class Bno085Cfg:
    i2c_bus: int | None = None
    fast_interval_ms: int = 10
    slow_interval_ms: int = 200
    motion_gyro_thresh: float = 0.05
    motion_linacc_thresh: float = 0.08
    motion_hold_frames: int = 10


@dataclass(frozen=True)
class WearableCfg:
    enabled: bool = True
    device_id: str = "PERFORMER"
    publish_rate_hz: float = 20.0
    console: bool = True
    imu_sink: ImuSinkCfg = ImuSinkCfg()
    button_pin: int = 17
    bno085: Bno085Cfg = Bno085Cfg()


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root for {path} must be a mapping")
    return data


def load_wearable_cfg(path: Path) -> WearableCfg:
    data = load_yaml_mapping(path)
    w = data.get("wearable", data)

    imu_in = w.get("imu_sink", {}) or {}
    imu_sink = ImuSinkCfg(
        enabled=bool(imu_in.get("enabled", True)),
        endpoint=str(imu_in.get("endpoint", "tcp://127.0.0.1:5572")),
        bind=bool(imu_in.get("bind", False)),
        topic=str(imu_in.get("topic", "imu")),
        sndhwm=int(imu_in.get("sndhwm", 32)),
        linger_ms=int(imu_in.get("linger_ms", 0)),
    )

    bno_in = w.get("bno085", {}) or {}
    i2c_bus_in = bno_in.get("i2c_bus")
    bno085 = Bno085Cfg(
        i2c_bus=None if i2c_bus_in is None else int(i2c_bus_in),
        fast_interval_ms=int(bno_in.get("fast_interval_ms", 10)),
        slow_interval_ms=int(bno_in.get("slow_interval_ms", 200)),
        motion_gyro_thresh=float(bno_in.get("motion_gyro_thresh", 0.05)),
        motion_linacc_thresh=float(bno_in.get("motion_linacc_thresh", 0.08)),
        motion_hold_frames=int(bno_in.get("motion_hold_frames", 10)),
    )

    return WearableCfg(
        enabled=bool(w.get("enabled", True)),
        device_id=str(w.get("device_id", "PERFORMER")),
        publish_rate_hz=float(w.get("publish_rate_hz", 20.0)),
        console=bool(w.get("console", True)),
        imu_sink=imu_sink,
        button_pin=int(w.get("button_pin", 17)),
        bno085=bno085,
    )
