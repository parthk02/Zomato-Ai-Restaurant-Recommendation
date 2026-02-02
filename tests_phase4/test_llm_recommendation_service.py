"""
Tests for Phase 4 LLMRecommendationService and prompt building.
"""

from __future__ import annotations

import json

import pandas as pd

from phase2_user_input.models import NormalizedUserInput
from phase4_recommendation.models import RecommendedRestaurant
from phase4_recommendation.prompt_builder import build_recommendation_prompt
from phase4_recommendation.service import LLMRecommendationService


class FakeLLMClient:
    """
    Simple fake LLM client that ignores the prompt and returns
    deterministic JSON for testing.
    """

    def __init__(self, response_payload) -> None:
        self._payload = response_payload
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return json.dumps(self._payload)


def _make_user_input() -> NormalizedUserInput:
    return NormalizedUserInput(
        city="bangalore",
        price_range=(500.0, 1000.0),
        price_bucket="mid",
    )


def _make_candidates_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["A", "B"],
            "city": ["bangalore", "bangalore"],
            "approx_cost(for two people)": [600.0, 900.0],
            "cuisines": ["Indian", "Italian"],
            "aggregate_rating": [4.2, 4.5],
        }
    )


def test_build_recommendation_prompt_contains_user_and_candidates() -> None:
    user_input = _make_user_input()
    candidates = _make_candidates_df()

    prompt = build_recommendation_prompt(user_input, candidates, max_candidates=1)

    # Should mention city and price range.
    assert "bangalore" in prompt
    assert "500.0 to 1000.0" in prompt
    # Should include at least the first candidate name and cuisines.
    assert "A" in prompt
    assert "Indian" in prompt


def test_llm_recommendation_service_parses_valid_json_response() -> None:
    user_input = _make_user_input()
    candidates = _make_candidates_df()

    fake_response = [
        {
            "name": "A",
            "city": "bangalore",
            "cuisines": "Indian",
            "price_for_two": 600,
            "rating": 4.2,
            "reason": "Good match for your budget in Bangalore.",
        },
        {
            "name": "B",
            "city": "bangalore",
            "cuisines": "Italian",
            "price_for_two": 900,
            "rating": 4.5,
            "reason": "Highly rated Italian option within your price range.",
        },
    ]

    fake_client = FakeLLMClient(response_payload=fake_response)
    service = LLMRecommendationService(llm_client=fake_client)

    recommendations = service.recommend(user_input, candidates)

    assert len(recommendations) == 2
    first: RecommendedRestaurant = recommendations[0]
    assert first.name == "A"
    assert first.city == "bangalore"
    assert first.cuisines == "Indian"
    assert first.price_for_two == 600.0
    assert first.rating == 4.2
    assert "Good match" in (first.reason or "")


def test_llm_recommendation_service_handles_empty_candidates() -> None:
    user_input = _make_user_input()
    candidates = _make_candidates_df().iloc[0:0]

    fake_client = FakeLLMClient(response_payload=[])
    service = LLMRecommendationService(llm_client=fake_client)

    recommendations = service.recommend(user_input, candidates)

    assert recommendations == []


def test_llm_recommendation_service_ignores_malformed_items() -> None:
    user_input = _make_user_input()
    candidates = _make_candidates_df()

    fake_response = [
        {"name": "Valid", "price_for_two": "700", "rating": "4.0"},
        "not-a-dict",
        {"name": 123},  # invalid name
    ]
    fake_client = FakeLLMClient(response_payload=fake_response)

    service = LLMRecommendationService(llm_client=fake_client)

    recommendations = service.recommend(user_input, candidates)

    assert len(recommendations) == 1
    assert recommendations[0].name == "Valid"
    assert recommendations[0].price_for_two == 700.0
    assert recommendations[0].rating == 4.0

