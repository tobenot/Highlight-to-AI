from __future__ import annotations

import platform
import time

from .config import AppConfig


class FeedbackService:
    def __init__(self, config: AppConfig) -> None:
        self._enabled = config.beep
        self._is_windows = platform.system() == "Windows"

    def start(self) -> None:
        self._beep(880, 70)

    def success(self) -> None:
        self._beep(988, 70)
        time.sleep(0.04)
        self._beep(1175, 70)

    def failure(self) -> None:
        self._beep(220, 180)

    def busy(self) -> None:
        self._beep(440, 80)

    def _beep(self, frequency: int, duration_ms: int) -> None:
        if not self._enabled:
            return
        try:
            if self._is_windows:
                import winsound

                winsound.Beep(frequency, duration_ms)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass
