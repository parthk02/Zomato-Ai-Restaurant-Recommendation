"""
Tests for Phase 2 user input validation and normalization.
"""

from __future__ import annotations

from phase2_user_input.models import NormalizedUserInput, RawUserInput
from phase2_user_input.validation import (
    InputNormalizer,
    InputValidator,
    ValidationResult,
)


def test_validator_rejects_empty_city() -> None:
    validator = InputValidator()
    raw = RawUserInput(city="   ", price_text="500")

    result: ValidationResult = validator.validate(raw)

    assert not result.is_valid
    assert any(err.field == "city" for err in result.errors)


def test_validator_rejects_city_not_in_allowed_list() -> None:
    validator = InputValidator(allowed_cities=["bangalore", "mumbai"])
    raw = RawUserInput(city="delhi", price_text="500")

    result = validator.validate(raw)

    assert not result.is_valid
    assert any(err.field == "city" for err in result.errors)


def test_validator_accepts_city_in_allowed_list_and_valid_price() -> None:
    validator = InputValidator(allowed_cities=["bangalore", "mumbai"])
    raw = RawUserInput(city="  Bangalore ", price_text="500-1000")

    result = validator.validate(raw)

    assert result.is_valid
    assert result.errors == []


def test_validator_rejects_invalid_price_expression() -> None:
    validator = InputValidator()
    raw = RawUserInput(city="Bangalore", price_text="cheap")

    result = validator.validate(raw)

    assert not result.is_valid
    assert any(err.field == "price_text" for err in result.errors)


def test_normalizer_converts_to_lowercase_city_and_price_range_for_single_value() -> None:
    normalizer = InputNormalizer()
    raw = RawUserInput(city="Bangalore", price_text="1000")

    normalized: NormalizedUserInput = normalizer.normalize(raw)

    assert normalized.city == "bangalore"
    assert normalized.price_range is not None
    lower, upper = normalized.price_range
    # ±20% band around 1000 → [800, 1200]
    assert lower == 800.0
    assert upper == 1200.0
    assert normalized.price_bucket == "mid" or normalized.price_bucket == "high"


def test_normalizer_handles_range_and_assigns_bucket() -> None:
    normalizer = InputNormalizer()
    raw = RawUserInput(city="Delhi", price_text="200-300")

    normalized = normalizer.normalize(raw)

    assert normalized.city == "delhi"
    assert normalized.price_range == (200.0, 300.0)
    assert normalized.price_bucket == "low"


def test_normalizer_handles_empty_price() -> None:
    normalizer = InputNormalizer()
    raw = RawUserInput(city="Delhi", price_text="  ")

    normalized = normalizer.normalize(raw)

    assert normalized.city == "delhi"
    assert normalized.price_range is None
    assert normalized.price_bucket is None

