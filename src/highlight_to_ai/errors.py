class HighlightToAIError(Exception):
    """Base exception for Highlight-to-AI."""


class ConfigError(HighlightToAIError):
    """Raised when configuration is invalid."""


class EmptySelectionError(HighlightToAIError):
    """Raised when no text is selected or copied."""


class ClipboardTimeoutError(HighlightToAIError):
    """Raised when clipboard content does not update in time."""


class LLMRequestError(HighlightToAIError):
    """Raised when LLM request fails."""


class EmptyLLMResultError(HighlightToAIError):
    """Raised when LLM returns empty content."""
