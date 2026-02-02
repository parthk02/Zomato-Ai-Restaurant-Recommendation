"""
Abstractions and implementations for LLM access (Groq-backed).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import requests
from dotenv import load_dotenv

# Load environment variables from a .env file at project root (if present)
load_dotenv()


class LLMClient(Protocol):
    """
    Minimal protocol for an LLM client.

    Implementations should be synchronous and return the raw model text.
    """

    def generate(self, prompt: str) -> str:  # pragma: no cover - protocol
        ...


@dataclass
class GroqAPIClient:
    """
    Concrete LLM client that calls the Groq Chat Completions API.

    This implementation expects the API key to be provided via:
    - Explicit `api_key` argument, or
    - `GROQ_API_KEY` environment variable.
    """

    model: str = "llama-3.3-70b-versatile"
    api_key: str | None = None

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY env var or pass api_key explicitly."
            )

    def generate(self, prompt: str) -> str:
        """
        Call Groq's chat completions endpoint and return the model's text.
        """
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful restaurant recommendation assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }

        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            raise RuntimeError("Unexpected response format from Groq API.") from exc

