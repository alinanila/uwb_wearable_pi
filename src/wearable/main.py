from __future__ import annotations

import argparse
import logging
import signal
import time
from pathlib import Path
from typing import Optional

from .config import load_wearable_cfg
from .bno085 import Bno085Reader
from .button import ButtonReader
from .publisher import ImuPublisher

HERE         = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "wearable.yaml"

log = logging.getLogger(__name__)


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="UWB wearable IMU publisher")
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="path to wearable.yaml (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )

    cfg = load_wearable_cfg(args.config)
    if not cfg.enabled:
        log.info("wearable is disabled in config (wearable.enabled=false); exiting")
        return

    log.info("initialising wearable device=%s", cfg.device_id)

    bno       = Bno085Reader(
        fast_interval_ms    = cfg.bno085.fast_interval_ms,
        slow_interval_ms    = cfg.bno085.slow_interval_ms,
        motion_gyro_thresh  = cfg.bno085.motion_gyro_thresh,
        motion_linacc_thresh= cfg.bno085.motion_linacc_thresh,
        motion_hold_frames  = cfg.bno085.motion_hold_frames,
    )
    button    = ButtonReader(pin=cfg.button_pin)
    publisher = ImuPublisher(cfg)

    publish_interval_s = 1.0 / cfg.publish_rate_hz

    stop = False

    def _sigint_handler(signum: int, frame: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _sigint_handler)

    log.info(
        "wearable started: rate=%.1fHz endpoint=%s topic=%s",
        cfg.publish_rate_hz,
        cfg.imu_sink.endpoint,
        cfg.imu_sink.topic,
    )

    try:
        while not stop:
            start = time.monotonic()

            imu_data       = bno.read()
            button_pressed = button.consume()

            if cfg.imu_sink.enabled:
                publisher.publish(imu_data, button_pressed)

            elapsed    = time.monotonic() - start
            sleep_time = publish_interval_s - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        publisher.close()
        button.close()
        log.info("wearable stopped")


if __name__ == "__main__":
    main()