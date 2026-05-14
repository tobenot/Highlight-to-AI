from __future__ import annotations

from .config import ApiConfig
from .errors import ConfigError, EmptyLLMResultError, LLMRequestError


class LLMClient:
    def __init__(self, config: ApiConfig) -> None:
        if not config.api_key:
            raise ConfigError("API Key 为空，请在 config.toml 或环境变量中配置")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ConfigError("缺少依赖 openai，请先运行：pip install -e .") from exc

        self._config = config
        kwargs = {"api_key": config.api_key, "timeout": config.timeout_seconds}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self._client = OpenAI(**kwargs)

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=messages,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
            content = response.choices[0].message.content if response.choices else None
        except Exception as exc:
            raise LLMRequestError(f"LLM 请求失败：{exc}") from exc

        result = (content or "").strip()
        if not result:
            raise EmptyLLMResultError("模型返回了空内容")
        return result
