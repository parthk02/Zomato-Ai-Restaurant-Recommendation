"""
Lightweight tests around GroqAPIClient configuration.

These tests do NOT hit the real Groq API; they only verify that the
client correctly reads the API key from environment or arguments.
"""

from __future__ import annotations

import os

import pytest

from phase4_recommendation.llm_client import GroqAPIClient


def test_groq_client_raises_without_api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GroqAPIClient()


def test_groq_client_uses_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")
    client = GroqAPIClient()
    assert client.api_key == "dummy-key"


def test_groq_client_prefers_explicit_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    client = GroqAPIClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"

