"""
Validation and normalization logic for Phase 2 user input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .models import NormalizedUserInput, RawUserInput


@dataclass
class ValidationError:
    field: str
    message: str


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]


class InputValidator:
    """
    Validates raw user input fields for basic correctness.
    """

    def __init__(self, allowed_cities: Optional[List[str]] = None) -> None:
        # Store cities in normalized form for comparison.
        self.allowed_cities = (
            [c.strip().lower() for c in allowed_cities] if allowed_cities else None
        )

    def validate(self, raw: RawUserInput) -> ValidationResult:
        errors: List[ValidationError] = []

        # City: required, non-empty.
        if not raw.city or not raw.city.strip():
            errors.append(
                ValidationError(field="city", message="City is required and cannot be empty.")
            )
        else:
            normalized_city = raw.city.strip().lower()
            if self.allowed_cities is not None and normalized_city not in self.allowed_cities:
                errors.append(
                    ValidationError(
                        field="city",
                        message="City is not available in our service area.",
                    )
                )

        # Price text: optional, but if provided must be interpretable.
        if raw.price_text and raw.price_text.strip():
            price_text = raw.price_text.strip()
            if not _is_valid_price_expression(price_text):
                errors.append(
                    ValidationError(
                        field="price_text",
                        message="Price must be a number or a range like '500-1000'.",
                    )
                )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class InputNormalizer:
    """
    Normalizes validated user input into a structured form.
    """

    def normalize(self, raw: RawUserInput) -> NormalizedUserInput:
        city = raw.city.strip().lower()
        price_range = _parse_price_expression(raw.price_text)
        bucket = _derive_price_bucket(price_range)

        return NormalizedUserInput(city=city, price_range=price_range, price_bucket=bucket)


def _is_valid_price_expression(text: str) -> bool:
    """
    Return True if the text looks like a valid price expression.
    Supported:
      - Single number, e.g. "700"
      - Range, e.g. "500-1200"
    """
    try:
        _ = _parse_price_expression(text)
        return True
    except ValueError:
        return False


def _parse_price_expression(
    text: Optional[str],
) -> Optional[Tuple[Optional[float], Optional[float]]]:
    if text is None:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    # Range: "min-max"
    if "-" in stripped:
        parts = stripped.split("-", maxsplit=1)
        if len(parts) != 2:
            raise ValueError("Invalid price range format.")
        try:
            lower = float(parts[0].replace(",", "").strip())
            upper = float(parts[1].replace(",", "").strip())
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Price range bounds must be numbers.") from exc
        if lower < 0 or upper < 0 or lower > upper:
            raise ValueError("Invalid numeric bounds for price range.")
        return (lower, upper)

    # Single value: interpret as a target price with ±20% band.
    try:
        value = float(stripped.replace(",", ""))
    except ValueError as exc:
        raise ValueError("Price must be numeric.") from exc
    if value < 0:
        raise ValueError("Price cannot be negative.")

    margin = value * 0.2
    return (value - margin, value + margin)


def _derive_price_bucket(
    price_range: Optional[Tuple[Optional[float], Optional[float]]]
) -> Optional[str]:
    """
    Quick heuristic to label a price range as low / mid / high.
    This is a placeholder that can be tuned with real data later.
    """
    if price_range is None:
        return None

    lower, upper = price_range
    if lower is None and upper is None:
        return None

    # Use the midpoint as a proxy for "typical" price.
    if lower is None:
        midpoint = upper
    elif upper is None:
        midpoint = lower
    else:
        midpoint = (lower + upper) / 2.0

    if midpoint is None:
        return None

    if midpoint < 400:
        return "low"
    if midpoint < 1000:
        return "mid"
    return "high"

