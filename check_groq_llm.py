"""
Quick sanity check for Phase 4 Groq LLM integration.

This script sends a very small test prompt to Groq using GroqAPIClient
and prints the raw response text. It is meant for manual testing only
and is not used in the main pipeline.

Usage (PowerShell):
  cd "C:\\Users\\1008\\Desktop\\Nextleap\\Build Hour 1"
  $env:GROQ_API_KEY = "YOUR_GROQ_KEY_HERE"
  python check_groq_llm.py
"""

from __future__ import annotations

from phase4_recommendation.llm_client import GroqAPIClient


def main() -> None:
    try:
        client = GroqAPIClient()  # reads GROQ_API_KEY
    except ValueError as exc:
        print("GroqAPIClient could not be created (missing API key):")
        print(f"  {exc}")
        return

    prompt = "Say hello and confirm that the Groq LLM is reachable. Reply in one short sentence."
    print("Sending test prompt to Groq...")
    try:
        response = client.generate(prompt)
    except Exception as exc:  # pragma: no cover - manual diagnostic script
        print("Error while calling Groq API:")
        print(f"  {exc}")
        return

    print("\nGroq LLM response:")
    print(response)


if __name__ == "__main__":
    main()

