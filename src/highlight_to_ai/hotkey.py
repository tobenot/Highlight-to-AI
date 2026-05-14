from __future__ import annotations

import logging
from collections.abc import Callable

from .config import HotkeyConfig
from .errors import ConfigError


class HotkeyListener:
    def __init__(self, config: HotkeyConfig, on_trigger: Callable[[], object], logger: logging.Logger) -> None:
        self._config = config
        self._on_trigger = on_trigger
        self._logger = logger
        self._listener = None

    def start(self) -> None:
        try:
            from pynput import keyboard
        except ImportError as exc:
            raise ConfigError("缺少依赖 pynput，请先运行：pip install -e .") from exc

        try:
            self._listener = keyboard.GlobalHotKeys({self._config.trigger: self._handle_trigger})
            self._listener.start()
        except Exception as exc:
            raise ConfigError(f"注册全局快捷键失败：{self._config.trigger}") from exc

        self._logger.info("hotkey listener started trigger=%s", self._config.trigger)

    def join(self) -> None:
        if self._listener is not None:
            self._listener.join()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _handle_trigger(self) -> None:
        self._logger.info("hotkey triggered")
        self._on_trigger()
