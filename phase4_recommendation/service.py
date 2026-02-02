"""
Recommendation service for Phase 4 that uses an LLM client.

This service is independent of any concrete Groq API usage. It can be
fully tested using a fake LLM client that returns deterministic JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

import pandas as pd

from phase2_user_input.models import NormalizedUserInput
from .llm_client import LLMClient
from .models import RecommendedRestaurant
from .prompt_builder import build_recommendation_prompt


class LLMRecommendationError(Exception):
    """
    Raised when the LLM call or response parsing fails in a way that
    should be surfaced to the caller as a recoverable error.
    """


@dataclass
class LLMRecommendationService:
    """
    Coordinates prompt building, LLM call, and response parsing.
    """

    llm_client: LLMClient

    def recommend(
        self,
        user_input: NormalizedUserInput,
        candidates: pd.DataFrame,
    ) -> List[RecommendedRestaurant]:
        """
        Use the LLM to select and describe the best restaurants.
        """
        if candidates.empty:
            return []

        prompt = build_recommendation_prompt(user_input, candidates)

        try:
            raw_response = self.llm_client.generate(prompt)
        except Exception as exc:  # pragma: no cover - network/LLM failure
            raise LLMRecommendationError(f"Error calling LLM: {exc}") from exc

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise LLMRecommendationError("LLM response was not valid JSON.") from exc

        if not isinstance(data, list):
            raise LLMRecommendationError("LLM response root must be a JSON array.")

        recommendations: List[RecommendedRestaurant] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue

            recommendations.append(
                RecommendedRestaurant(
                    name=name,
                    city=item.get("city"),
                    cuisines=item.get("cuisines"),
                    price_for_two=_to_optional_float(item.get("price_for_two")),
                    rating=_to_optional_float(item.get("rating")),
                    reason=item.get("reason"),
                )
            )

        return recommendations


def _to_optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

