import tempfile
import unittest
from pathlib import Path

from highlight_to_ai.config import ConfigService
from highlight_to_ai.prompt import PromptService


class ConfigPromptTests(unittest.TestCase):
    def test_config_service_loads_minimal_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                """
[app]
language = "zh-CN"
restore_clipboard = true
beep = false
copy_timeout_seconds = 1.0
paste_delay_seconds = 0.1

[hotkey]
trigger = "<f3>"

[api]
base_url = "https://example.com/v1"
api_key = "test-key"
model = "test-model"
timeout_seconds = 10
max_tokens = 128
temperature = 0.2

[prompt]
system = "只输出结果"
""".strip(),
                encoding="utf-8",
            )

            config = ConfigService(config_path).load()

        self.assertEqual(config.hotkey.trigger, "<f3>")
        self.assertEqual(config.api.base_url, "https://example.com/v1")
        self.assertEqual(config.api.model, "test-model")
        self.assertEqual(config.prompt.system, "只输出结果")

    def test_prompt_service_builds_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                """
[api]
api_key = "test-key"
model = "test-model"

[prompt]
system = "只输出结果"
""".strip(),
                encoding="utf-8",
            )
            config = ConfigService(config_path).load()

        messages = PromptService(config.prompt).build_messages("润色：hello")

        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "只输出结果"},
                {"role": "user", "content": "润色：hello"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
