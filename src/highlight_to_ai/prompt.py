from __future__ import annotations

from .config import PromptConfig


class PromptService:
    def __init__(self, config: PromptConfig) -> None:
        self._config = config

    def build_messages(self, selected_text: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._config.system},
            {"role": "user", "content": selected_text},
        ]
