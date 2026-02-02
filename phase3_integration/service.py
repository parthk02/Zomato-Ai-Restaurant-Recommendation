"""
Service layer for Phase 3 integration.

This prepares a candidate set of restaurants for a given user input by
connecting:
- Phase 2 validation + normalization, and
- Phase 1 in-memory restaurant store via the repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from phase2_user_input.models import NormalizedUserInput, RawUserInput
from phase2_user_input.validation import (
    InputNormalizer,
    InputValidator,
    ValidationError,
)

from .repository import RestaurantRepository


@dataclass
class RecommendationPreparationResult:
    """
    Result of preparing data for the recommendation step.
    """

    is_valid: bool
    errors: List[ValidationError]
    normalized_input: Optional[NormalizedUserInput]
    candidates: Optional[pd.DataFrame]


class RecommendationPreparationService:
    """
    Orchestrates Phase 2 and repository to produce a candidate set
    of restaurants that match the user's constraints.
    """

    def __init__(
        self,
        repository: RestaurantRepository,
        validator: InputValidator,
        normalizer: InputNormalizer,
    ) -> None:
        self._repository = repository
        self._validator = validator
        self._normalizer = normalizer

    def prepare(self, raw_input: RawUserInput) -> RecommendationPreparationResult:
        """
        Validate and normalize the user input, then fetch candidate
        restaurants that match city and price constraints.
        """
        validation = self._validator.validate(raw_input)
        if not validation.is_valid:
            return RecommendationPreparationResult(
                is_valid=False,
                errors=validation.errors,
                normalized_input=None,
                candidates=None,
            )

        normalized = self._normalizer.normalize(raw_input)
        candidates = self._repository.get_candidates(normalized)

        return RecommendationPreparationResult(
            is_valid=True,
            errors=[],
            normalized_input=normalized,
            candidates=candidates,
        )

