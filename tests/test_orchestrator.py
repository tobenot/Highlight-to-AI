import logging
import unittest

from highlight_to_ai.config import AppConfig
from highlight_to_ai.orchestrator import TaskOrchestrator


class FakeClipboard:
    def __init__(self) -> None:
        self.text = "old"
        self.values: list[str] = []

    def get_text_safe(self) -> str:
        return self.text

    def set_text(self, text: str) -> None:
        self.text = text
        self.values.append(text)

    def wait_for_change(self, previous_text: str, timeout_seconds: float) -> str:
        return "润色：hello"


class FakeInput:
    def __init__(self) -> None:
        self.copied = False
        self.pasted = False

    def copy(self) -> None:
        self.copied = True

    def paste(self) -> None:
        self.pasted = True


class FakeLLM:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "Hello polished"


class FakePrompt:
    def build_messages(self, selected_text: str) -> list[dict[str, str]]:
        return [{"role": "user", "content": selected_text}]


class FakeFeedback:
    def start(self) -> None:
        pass

    def success(self) -> None:
        pass

    def failure(self) -> None:
        pass

    def busy(self) -> None:
        pass


class OrchestratorTests(unittest.TestCase):
    def test_process_once_pastes_result_and_restores_clipboard(self) -> None:
        clipboard = FakeClipboard()
        input_service = FakeInput()
        orchestrator = TaskOrchestrator(
            app_config=AppConfig(
                language="zh-CN",
                restore_clipboard=True,
                beep=False,
                copy_timeout_seconds=1.0,
                paste_delay_seconds=0.0,
            ),
            clipboard=clipboard,  # type: ignore[arg-type]
            input_service=input_service,  # type: ignore[arg-type]
            llm=FakeLLM(),  # type: ignore[arg-type]
            prompt=FakePrompt(),  # type: ignore[arg-type]
            feedback=FakeFeedback(),  # type: ignore[arg-type]
            logger=logging.getLogger("test"),
        )

        orchestrator._process_once()

        self.assertTrue(input_service.copied)
        self.assertTrue(input_service.pasted)
        self.assertIn("Hello polished", clipboard.values)
        self.assertEqual(clipboard.values[-1], "old")


if __name__ == "__main__":
    unittest.main()
