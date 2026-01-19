"""
LLM Client Abstraction.

Provides a unified interface for interacting with LLM providers:
- Ollama (local)
- LM Studio (local)
- Any OpenAI-compatible API

The client handles:
- Connection management
- Retry logic
- Response parsing
- Error handling
"""

from dataclasses import dataclass
from typing import Any, Optional
import logging

import httpx

from config.settings import LLMSettings


logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message structure."""

    role: str  # system | user | assistant
    content: str


@dataclass
class LLMResponse:
    """LLM response structure."""

    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    This client provides a consistent interface regardless of the
    underlying LLM provider (Ollama, LM Studio, etc.).

    Attributes:
        settings: LLM configuration settings
        _client: HTTP client for API requests
    """

    def __init__(self, settings: LLMSettings):
        """
        Initialize the LLM client.

        Args:
            settings: LLM configuration including provider and URL
        """
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url,
            timeout=settings.timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build request headers based on provider."""
        headers = {"Content-Type": "application/json"}

        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"

        return headers

    def _get_api_path(self, endpoint: str) -> str:
        """
        Get the API path for the endpoint based on provider.

        Args:
            endpoint: The endpoint type (chat, completion, models)

        Returns:
            str: The full API path
        """
        if self.settings.provider == "ollama":
            paths = {
                "chat": "/api/chat",
                "generate": "/api/generate",
                "models": "/api/tags",
            }
        else:
            # OpenAI-compatible (LM Studio, etc.)
            paths = {
                "chat": "/v1/chat/completions",
                "generate": "/v1/completions",
                "models": "/v1/models",
            }

        return paths.get(endpoint, f"/api/{endpoint}")

    def is_connected(self) -> bool:
        """
        Check if the LLM server is reachable.

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            response = self._client.get(self._get_api_path("models"))
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM connection check failed: {e}")
            return False

    def list_models(self) -> list[str]:
        """
        List available models.

        Returns:
            list[str]: List of model names
        """
        try:
            response = self._client.get(self._get_api_path("models"))
            response.raise_for_status()
            data = response.json()

            # Handle different response formats
            if self.settings.provider == "ollama":
                return [m["name"] for m in data.get("models", [])]
            else:
                return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stop: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a completion from a prompt.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            stop: Stop sequences

        Returns:
            str: Generated text
        """
        for attempt in range(self.settings.max_retries):
            try:
                if self.settings.provider == "ollama":
                    response = self._ollama_generate(prompt, max_tokens, temperature)
                else:
                    response = self._openai_complete(
                        prompt, max_tokens, temperature, stop
                    )

                return response.content

            except Exception as e:
                logger.warning(f"Completion attempt {attempt + 1} failed: {e}")
                if attempt == self.settings.max_retries - 1:
                    raise

        return ""

    def chat(
        self, messages: list[Message], max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        """
        Generate a chat completion.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            str: Assistant's response
        """
        for attempt in range(self.settings.max_retries):
            try:
                if self.settings.provider == "ollama":
                    response = self._ollama_chat(messages, max_tokens, temperature)
                else:
                    response = self._openai_chat(messages, max_tokens, temperature)

                return response.content

            except Exception as e:
                logger.warning(f"Chat attempt {attempt + 1} failed: {e}")
                if attempt == self.settings.max_retries - 1:
                    raise

        return ""

    def _ollama_generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        """Ollama generate API."""
        response = self._client.post(
            self._get_api_path("generate"),
            json={
                "model": self.settings.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=data.get("model", self.settings.model),
        )

    def _ollama_chat(
        self, messages: list[Message], max_tokens: int, temperature: float
    ) -> LLMResponse:
        """Ollama chat API."""
        response = self._client.post(
            self._get_api_path("chat"),
            json={
                "model": self.settings.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.settings.model),
        )

    def _openai_complete(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop: Optional[list[str]],
    ) -> LLMResponse:
        """OpenAI-compatible completion API."""
        response = self._client.post(
            self._get_api_path("generate"),
            json={
                "model": self.settings.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": stop,
            },
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [{}])
        return LLMResponse(
            content=choices[0].get("text", ""),
            model=data.get("model", self.settings.model),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
        )

    def _openai_chat(
        self, messages: list[Message], max_tokens: int, temperature: float
    ) -> LLMResponse:
        """OpenAI-compatible chat API."""
        response = self._client.post(
            self._get_api_path("chat"),
            json={
                "model": self.settings.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [{}])
        return LLMResponse(
            content=choices[0].get("message", {}).get("content", ""),
            model=data.get("model", self.settings.model),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
