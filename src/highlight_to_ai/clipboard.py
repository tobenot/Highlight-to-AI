from __future__ import annotations

import time

from .errors import ClipboardTimeoutError


class ClipboardService:
    def __init__(self) -> None:
        try:
            import pyperclip
        except ImportError as exc:
            raise RuntimeError("缺少依赖 pyperclip，请先运行：pip install -e .") from exc
        self._pyperclip = pyperclip

    def get_text_safe(self) -> str:
        try:
            return self._pyperclip.paste() or ""
        except Exception:
            return ""

    def set_text(self, text: str) -> None:
        self._pyperclip.copy(text)

    def wait_for_change(self, previous_text: str, timeout_seconds: float) -> str:
        deadline = time.monotonic() + timeout_seconds
        last_text = previous_text

        while time.monotonic() < deadline:
            current = self.get_text_safe()
            if current != previous_text:
                return current
            last_text = current
            time.sleep(0.03)

        raise ClipboardTimeoutError("复制选中文本超时，请确认已选中文本且当前应用允许复制")
