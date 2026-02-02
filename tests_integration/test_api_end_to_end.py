"""
Integration test for the FastAPI backend (Phases 1–5 via HTTP).

Uses TestClient and a fake Groq client to verify the full pipeline
without hitting the real Groq API.
"""

from __future__ import annotations

from unittest import mock

from fastapi.testclient import TestClient

from api_backend.main import app


client = TestClient(app)


@mock.patch("api_backend.main.GroqAPIClient")
def test_api_recommendations_end_to_end_with_fake_llm(mock_groq_client) -> None:
    fake_llm = mock_groq_client.return_value
    fake_llm.generate.return_value = """
    [
      {"name": "API Demo Place", "city": "bangalore",
       "price_for_two": 900, "rating": 4.3,
       "cuisines": "Indian", "reason": "API integration test"}
    ]
    """

    resp = client.post(
        "/recommendations",
        json={"city": "Bangalore", "price_text": "800"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    assert data["recommendations"][0]["name"] == "API Demo Place"

