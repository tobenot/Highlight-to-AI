from __future__ import annotations

import logging

from .clipboard import ClipboardService
from .config import ConfigService, RuntimeConfig
from .feedback import FeedbackService
from .hotkey import HotkeyListener
from .input_control import InputService
from .llm import LLMClient
from .orchestrator import TaskOrchestrator
from .prompt import PromptService


class AppRuntime:
    def __init__(self, logger: logging.Logger, config_service: ConfigService | None = None) -> None:
        self._logger = logger
        self._config_service = config_service or ConfigService()
        self._hotkey_listener: HotkeyListener | None = None
        self._config: RuntimeConfig | None = None

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

        print("Highlight-to-AI 已启动")
        print(f"配置文件：{config.path}")
        print(f"快捷键：{config.hotkey.trigger}")
        print("选中包含指令的文本后按快捷键即可处理。按 Ctrl+C 结束当前终端进程。")
        self._hotkey_listener.join()

    def stop(self) -> None:
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
        self._logger.info("app stopped")
