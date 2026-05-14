from __future__ import annotations

import platform
import time


class InputService:
    def __init__(self) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("缺少依赖 pyautogui，请先运行：pip install -e .") from exc
        self._pyautogui = pyautogui
        self._modifier = "command" if platform.system() == "Darwin" else "ctrl"
        self._pyautogui.PAUSE = 0.03

    def copy(self) -> None:
        self._pyautogui.hotkey(self._modifier, "c")
        time.sleep(0.05)

    def paste(self) -> None:
        self._pyautogui.hotkey(self._modifier, "v")
