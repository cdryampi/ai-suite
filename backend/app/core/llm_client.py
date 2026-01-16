"""
LLM Client stub - minimal implementation.
"""

from dataclasses import dataclass


@dataclass
class LLMClient:
    """Stub LLM client."""

    def __init__(self, settings):
        self.settings = settings

    def is_connected(self):
        return False

    def complete(self, prompt, **kwargs):
        return "[LLM not configured]"
