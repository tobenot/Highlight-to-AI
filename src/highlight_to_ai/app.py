from __future__ import annotations

import logging
import threading
import time

from .clipboard import ClipboardService
from .config import ConfigService, RuntimeConfig
from .feedback import FeedbackService
from .hotkey import HotkeyListener
from .input_control import InputService
from .llm import LLMClient
from .orchestrator import TaskOrchestrator
from .prompt import PromptService
from .tray import TrayController



class AppRuntime:
    def __init__(self, logger: logging.Logger, config_service: ConfigService | None = None) -> None:
        self._logger = logger
        self._config_service = config_service or ConfigService()
        self._hotkey_listener: HotkeyListener | None = None
        self._tray: TrayController | None = None
        self._config: RuntimeConfig | None = None
        self._stop_event = threading.Event()


    def start(self) -> None:
        config = self._config_service.load()
        self._config = config
        self._logger.info(
            "config loaded path=%s base_url=%s model=%s api_key=%s",
            config.path,
            config.api.base_url,
            config.api.model,
            config.api.masked_key,
        )

        feedback = FeedbackService(config.app)
        clipboard = ClipboardService()
        input_service = InputService()
        llm = LLMClient(config.api)
        prompt = PromptService(config.prompt)
        orchestrator = TaskOrchestrator(
            app_config=config.app,
            clipboard=clipboard,
            input_service=input_service,
            llm=llm,
            prompt=prompt,
            feedback=feedback,
            logger=self._logger,
        )

        self._hotkey_listener = HotkeyListener(
            config=config.hotkey,
            on_trigger=orchestrator.run_async,
            logger=self._logger,
        )
        self._hotkey_listener.start()

        self._tray = TrayController(
            app_name="Highlight-to-AI",
            hotkey=config.hotkey.trigger,
            config_path=config.path,
            on_quit=self.request_stop,
            logger=self._logger,
        )

        print("Highlight-to-AI 已启动")
        print(f"配置文件：{config.path}")
        print(f"快捷键：{config.hotkey.trigger}")
        print("程序已进入后台，可在系统托盘中退出。")

        if self._tray.available:
            self._tray.run()
            self._stop_event.set()
            return

        self._logger.warning("tray dependency unavailable, running without tray")
        while not self._stop_event.is_set():
            time.sleep(0.3)


    def request_stop(self) -> None:
        self._stop_event.set()
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
            self._hotkey_listener = None

    def stop(self) -> None:
        self._stop_event.set()
        if self._tray is not None:
            self._tray.stop()
            self._tray = None
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
        self._logger.info("app stopped")

