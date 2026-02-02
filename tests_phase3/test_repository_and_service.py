"""
Tests for Phase 3 repository and integration service.
"""

from __future__ import annotations

import pandas as pd

from phase1_data_ingestion.storage import InMemoryRestaurantStore
from phase2_user_input.models import NormalizedUserInput, RawUserInput
from phase2_user_input.validation import InputNormalizer, InputValidator
from phase3_integration.repository import RestaurantRepository
from phase3_integration.service import (
    RecommendationPreparationResult,
    RecommendationPreparationService,
)


def _make_sample_store() -> InMemoryRestaurantStore:
    df = pd.DataFrame(
        {
            "name": ["A", "B", "C", "D"],
            "city": ["bangalore", "bangalore", "delhi", "bangalore"],
            "approx_cost(for two people)": [300.0, 800.0, 500.0, 1500.0],
        }
    )
    return InMemoryRestaurantStore(data=df)


def test_repository_filters_by_city_and_price_range() -> None:
    store = _make_sample_store()
    repo = RestaurantRepository(store=store)

    user_input = NormalizedUserInput(
        city="bangalore",
        price_range=(400.0, 1000.0),
        price_bucket="mid",
    )

    candidates = repo.get_candidates(user_input)

    # Should include only restaurant B (bangalore, 800)
    assert len(candidates) == 1
    assert candidates.iloc[0]["name"] == "B"


def test_preparation_service_returns_errors_for_invalid_input() -> None:
    store = _make_sample_store()
    repo = RestaurantRepository(store=store)
    validator = InputValidator(allowed_cities=["bangalore"])
    normalizer = InputNormalizer()
    service = RecommendationPreparationService(
        repository=repo, validator=validator, normalizer=normalizer
    )

    raw = RawUserInput(city="unknown-city", price_text="500")
    result: RecommendationPreparationResult = service.prepare(raw)

    assert not result.is_valid
    assert result.normalized_input is None
    assert result.candidates is None
    assert any(err.field == "city" for err in result.errors)


def test_preparation_service_produces_candidates_for_valid_input() -> None:
    store = _make_sample_store()
    repo = RestaurantRepository(store=store)
    validator = InputValidator(allowed_cities=["bangalore", "delhi"])
    normalizer = InputNormalizer()
    service = RecommendationPreparationService(
        repository=repo, validator=validator, normalizer=normalizer
    )

    raw = RawUserInput(city="Bangalore", price_text="800")
    result = service.prepare(raw)

    assert result.is_valid
    assert result.errors == []
    assert result.normalized_input is not None
    assert result.candidates is not None

    # For a target price of 800 with ±20% band [640, 960],
    # only restaurant B (bangalore, 800) matches.
    candidates = result.candidates
    assert len(candidates) == 1
    assert candidates.iloc[0]["name"] == "B"

