"""
Integration test for the CLI entry point (Phases 1–5).

This test runs the CLI with a fake Groq client and checks that the
output includes the expected recommendation text structure.
"""

from __future__ import annotations

from unittest import mock

import pytest

import cli as cli_module


def test_cli_end_to_end_with_fake_llm(capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch GroqAPIClient inside the cli module to avoid real API calls and
    # bypass API key checks.
    class FakeGroqClient:
        def generate(self, prompt: str) -> str:
            return """
            [
              {"name": "CLI Demo Place", "city": "bangalore",
               "price_for_two": 800, "rating": 4.5,
               "cuisines": "Indian", "reason": "CLI integration test"}
            ]
            """

    monkeypatch.setattr(cli_module, "GroqAPIClient", lambda: FakeGroqClient())

    # Act: run CLI main with sample args.
    cli_module.main(["Bangalore", "800"])

    # Assert: captured output contains formatted recommendations.
    captured = capsys.readouterr()
    out = captured.out
    assert "Loaded" in out
    assert "Top restaurant recommendations:" in out
    assert "CLI Demo Place" in out

