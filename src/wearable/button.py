from __future__ import annotations

import logging
from threading import Lock

log = logging.getLogger(__name__)


class ButtonReader:
    """Reads a momentary button on a Raspberry Pi GPIO pin via gpiozero."""

    def __init__(
        self,
        pin: int,
        *,
        pull_up: bool = True,
        bounce_time: float = 0.05,
    ) -> None:
        self._button = None
        self._pressed = False
        self._lock = Lock()

        try:
            from gpiozero import Button

            self._button = Button(
                pin,
                pull_up=pull_up,
                bounce_time=bounce_time,
            )
            self._button.when_pressed = self._mark_pressed
            log.info("button initialised on GPIO%d", pin)
        except Exception as e:
            log.error("button init failed on GPIO%d: %s", pin, e)

    def _mark_pressed(self) -> None:
        with self._lock:
            self._pressed = True

    def consume(self) -> bool:
        """Return True once for each press event since the last call."""
        with self._lock:
            pressed = self._pressed
            self._pressed = False
        return pressed

    def close(self) -> None:
        if self._button is not None:
            self._button.close()
