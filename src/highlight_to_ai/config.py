from __future__ import annotations

import os
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ConfigError

APP_NAME = "Highlight-to-AI"
CONFIG_ENV = "HIGHLIGHT_TO_AI_CONFIG"
API_KEY_ENV = "HIGHLIGHT_TO_AI_API_KEY"
BASE_URL_ENV = "HIGHLIGHT_TO_AI_BASE_URL"

DEFAULT_SYSTEM_PROMPT = (
    "你是一个极简的文本处理引擎。用户会给你一段文本，其中包含处理指令和待处理内容。"
    "请直接执行指令，并只输出最终处理结果。不要输出解释，不要寒暄，不要包含‘好的’‘以下是’等前置话术。"
)

DEFAULT_CONFIG_TOML = f'''[app]
language = "zh-CN"
restore_clipboard = true
beep = true
copy_timeout_seconds = 1.0
paste_delay_seconds = 0.15

[hotkey]
trigger = "<f3>"

[api]
base_url = "https://api.deepseek.com"
api_key = ""
model = "deepseek-chat"
timeout_seconds = 15
max_tokens = 2048
temperature = 0.3

[prompt]
system = "{DEFAULT_SYSTEM_PROMPT}"
'''


@dataclass(frozen=True)
class AppConfig:
    language: str
    restore_clipboard: bool
    beep: bool
    copy_timeout_seconds: float
    paste_delay_seconds: float


@dataclass(frozen=True)
class HotkeyConfig:
    trigger: str


@dataclass(frozen=True)
class ApiConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
    max_tokens: int
    temperature: float

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return "<empty>"
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:3]}***{self.api_key[-4:]}"


@dataclass(frozen=True)
class PromptConfig:
    system: str


@dataclass(frozen=True)
class RuntimeConfig:
    app: AppConfig
    hotkey: HotkeyConfig
    api: ApiConfig
    prompt: PromptConfig
    path: Path


class ConfigService:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or get_default_config_path()

    def ensure_config_exists(self) -> None:
        if self.config_path.exists():
            return
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        example_path = Path.cwd() / "config.example.toml"
        if example_path.exists():
            shutil.copyfile(example_path, self.config_path)
        else:
            self.config_path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")

    def load(self) -> RuntimeConfig:
        self.ensure_config_exists()
        try:
            data = tomllib.loads(self.config_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"配置文件 TOML 格式错误：{self.config_path}") from exc
        except OSError as exc:
            raise ConfigError(f"无法读取配置文件：{self.config_path}") from exc

        app = _section(data, "app")
        hotkey = _section(data, "hotkey")
        api = _section(data, "api")
        prompt = _section(data, "prompt")

        api_key = (
            os.getenv(API_KEY_ENV)
            or os.getenv("OPENAI_API_KEY")
            or _str(api, "api_key", "")
        )
        base_url = (
            os.getenv(BASE_URL_ENV)
            or os.getenv("OPENAI_BASE_URL")
            or _str(api, "base_url", "https://api.deepseek.com")
        )

        config = RuntimeConfig(
            app=AppConfig(
                language=_str(app, "language", "zh-CN"),
                restore_clipboard=_bool(app, "restore_clipboard", True),
                beep=_bool(app, "beep", True),
                copy_timeout_seconds=_float(app, "copy_timeout_seconds", 1.0),
                paste_delay_seconds=_float(app, "paste_delay_seconds", 0.15),
            ),
            hotkey=HotkeyConfig(trigger=_str(hotkey, "trigger", "<f3>")),
            api=ApiConfig(
                base_url=base_url,
                api_key=api_key,
                model=_str(api, "model", "deepseek-chat"),
                timeout_seconds=_float(api, "timeout_seconds", 15.0),
                max_tokens=_int(api, "max_tokens", 2048),
                temperature=_float(api, "temperature", 0.3),
            ),
            prompt=PromptConfig(system=_str(prompt, "system", DEFAULT_SYSTEM_PROMPT)),
            path=self.config_path,
        )
        _validate(config)
        return config


def get_default_config_path() -> Path:
    if os.getenv(CONFIG_ENV):
        return Path(os.environ[CONFIG_ENV]).expanduser().resolve()

    local_config = Path.cwd() / "config.toml"
    if local_config.exists():
        return local_config.resolve()

    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "config.toml"

    return Path.home() / f".{APP_NAME}" / "config.toml"



def get_default_log_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "logs"
    return Path.home() / f".{APP_NAME}" / "logs"


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"配置节 [{name}] 必须是对象")
    return value


def _str(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ConfigError(f"配置项 {key} 必须是字符串")
    return value.strip() if key != "system" else value


def _bool(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"配置项 {key} 必须是布尔值")
    return value


def _float(data: dict[str, Any], key: str, default: float) -> float:
    value = data.get(key, default)
    if isinstance(value, int | float):
        return float(value)
    raise ConfigError(f"配置项 {key} 必须是数字")


def _int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if isinstance(value, int):
        return value
    raise ConfigError(f"配置项 {key} 必须是整数")


def _validate(config: RuntimeConfig) -> None:
    if not config.hotkey.trigger:
        raise ConfigError("快捷键 trigger 不能为空")
    if not config.api.model:
        raise ConfigError("模型 model 不能为空")
    if config.api.timeout_seconds <= 0:
        raise ConfigError("timeout_seconds 必须大于 0")
    if config.app.copy_timeout_seconds <= 0:
        raise ConfigError("copy_timeout_seconds 必须大于 0")
    if config.app.paste_delay_seconds < 0:
        raise ConfigError("paste_delay_seconds 不能小于 0")
    if config.api.max_tokens <= 0:
        raise ConfigError("max_tokens 必须大于 0")
