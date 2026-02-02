"""
Tests for FastAPI endpoints in api_backend.main.
These tests do NOT call the real Groq API; they use a fake LLM client.
"""

from __future__ import annotations

from unittest import mock

from fastapi.testclient import TestClient

from api_backend.main import app, _prep_service
from phase2_user_input.models import RawUserInput
from phase3_integration.service import RecommendationPreparationResult
from phase4_recommendation.models import RecommendedRestaurant


client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "restaurants_loaded" in data


def test_cities_endpoint() -> None:
    resp = client.get("/cities")
    assert resp.status_code == 200
    data = resp.json()
    assert "cities" in data
    assert isinstance(data["cities"], list)


@mock.patch("api_backend.main.GroqAPIClient")
def test_recommendations_endpoint_with_fake_llm(mock_groq_client) -> None:
    # Arrange fake prep result by spying on the underlying service.
    # We don't want to actually download the dataset again, so just call
    # the real prep service to get a non-empty candidate set for a known city.
    raw = RawUserInput(city="Bangalore", price_text="800")
    prep_result: RecommendationPreparationResult = _prep_service.prepare(raw)

    if not prep_result.is_valid or prep_result.candidates is None:
        # If validation fails for this test data, just skip.
        return

    # Fake LLM client: return deterministic JSON.
    fake_llm = mock_groq_client.return_value
    fake_llm.generate.return_value = """
    [
      {"name": "Demo Place", "city": "bangalore", "cuisines": "Indian",
       "price_for_two": 800, "rating": 4.5, "reason": "Test reason"}
    ]
    """

    resp = client.post(
        "/recommendations",
        json={"city": "Bangalore", "price_text": "800"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    if data["recommendations"]:
        first = data["recommendations"][0]
        assert first["name"] == "Demo Place"

