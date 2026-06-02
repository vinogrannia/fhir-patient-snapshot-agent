"""LLM provider adapters for patient snapshot generation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import load_dotenv


DEFAULT_LLM_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct"


class LlmProviderError(RuntimeError):
    """Raised when an LLM provider cannot generate a response."""


@dataclass(frozen=True)
class OpenAICompatibleChatProvider:
    """Minimal OpenAI-compatible chat completions client."""

    api_key: str
    base_url: str = DEFAULT_LLM_BASE_URL
    model: str = DEFAULT_LLM_MODEL
    timeout_seconds: float = 60.0
    max_tokens: int = 1200
    temperature: float = 0.2

    @classmethod
    def from_env(cls) -> "OpenAICompatibleChatProvider":
        load_dotenv()
        api_key = os.getenv("LLM_API_KEY") or os.getenv("NEBIUS_API_KEY")
        if not api_key:
            raise LlmProviderError("LLM_API_KEY or NEBIUS_API_KEY is not set.")

        return cls(
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
            model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
        )

    def generate(self, system_instructions: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LlmProviderError(
                f"LLM request failed: HTTP {exc.code} {exc.reason}. {detail}"
            ) from exc
        except URLError as exc:
            raise LlmProviderError(f"LLM request failed: {exc}") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LlmProviderError("LLM response was not JSON.") from exc

        text = extract_chat_completion_text(payload)
        if not text:
            raise LlmProviderError("LLM response did not contain message content.")

        return text


def extract_chat_completion_text(payload: dict[str, Any]) -> str:
    """Extract assistant text from an OpenAI-compatible chat completion payload."""

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()

    return ""
