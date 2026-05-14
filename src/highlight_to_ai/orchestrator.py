from __future__ import annotations

import logging
import threading
import time
import uuid

from .clipboard import ClipboardService
from .config import AppConfig
from .errors import EmptySelectionError
from .feedback import FeedbackService
from .input_control import InputService
from .llm import LLMClient
from .prompt import PromptService


class TaskOrchestrator:
    def __init__(
        self,
        app_config: AppConfig,
        clipboard: ClipboardService,
        input_service: InputService,
        llm: LLMClient,
        prompt: PromptService,
        feedback: FeedbackService,
        logger: logging.Logger,
    ) -> None:
        self._config = app_config
        self._clipboard = clipboard
        self._input = input_service
        self._llm = llm
        self._prompt = prompt
        self._feedback = feedback
        self._logger = logger
        self._lock = threading.Lock()
        self._running = False

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def run_async(self) -> bool:
        with self._lock:
            if self._running:
                self._feedback.busy()
                return False
            self._running = True

        thread = threading.Thread(target=self._run_guarded, name="highlight-to-ai-worker", daemon=True)
        thread.start()
        return True

    def _run_guarded(self) -> None:
        started_at = time.monotonic()
        try:
            self._process_once()
            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            self._logger.info("task succeeded elapsed_ms=%s", elapsed_ms)
        except Exception:
            elapsed_ms = int((time.monotonic() - started_at) * 1000)
            self._logger.exception("task failed elapsed_ms=%s", elapsed_ms)
            self._feedback.failure()
        finally:
            with self._lock:
                self._running = False

    def _process_once(self) -> None:
        old_clipboard = self._clipboard.get_text_safe()
        sentinel = f"__HIGHLIGHT_TO_AI_SENTINEL_{uuid.uuid4()}__"
        should_restore = self._config.restore_clipboard

        self._feedback.start()
        try:
            self._clipboard.set_text(sentinel)
            self._input.copy()
            selected_text = self._clipboard.wait_for_change(
                previous_text=sentinel,
                timeout_seconds=self._config.copy_timeout_seconds,
            )
            selected_text = selected_text.strip()
            if not selected_text:
                raise EmptySelectionError("未复制到有效文本，请确认已选中文本")

            self._logger.info("selection captured chars=%s", len(selected_text))
            messages = self._prompt.build_messages(selected_text)
            result = self._llm.complete(messages).strip()
            self._logger.info("llm result received chars=%s", len(result))

            self._clipboard.set_text(result)
            self._input.paste()
            time.sleep(self._config.paste_delay_seconds)
            self._feedback.success()
        finally:
            if should_restore:
                try:
                    self._clipboard.set_text(old_clipboard)
                except Exception:
                    self._logger.exception("failed to restore clipboard")
