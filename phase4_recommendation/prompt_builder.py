"""
Prompt building utilities for Phase 4.
"""

from __future__ import annotations

from typing import List

import pandas as pd

from phase2_user_input.models import NormalizedUserInput


def build_recommendation_prompt(
    user_input: NormalizedUserInput,
    candidates: pd.DataFrame,
    max_candidates: int = 20,
) -> str:
    """
    Build a textual prompt describing the user preferences and a list of
    candidate restaurants.

    The LLM is expected to return a JSON array of objects with fields:
    - name
    - city (optional)
    - cuisines (optional)
    - price_for_two (optional)
    - rating (optional)
    - reason (short explanation)
    """
    lines: List[str] = []
    lines.append("You are an AI assistant that recommends restaurants.")
    lines.append(
        "Given the user's preferences and the list of candidate restaurants, "
        "choose the best options and respond ONLY with a JSON array of objects."
    )
    lines.append("")

    # User preferences section.
    lines.append("User preferences:")
    lines.append(f"- City: {user_input.city}")
    if user_input.price_range is not None:
        lower, upper = user_input.price_range
        lines.append(f"- Price range for two: {lower} to {upper}")
    if user_input.price_bucket is not None:
        lines.append(f"- Price bucket: {user_input.price_bucket}")
    lines.append("")

    # Candidate restaurants section.
    display_cols = [
        col
        for col in [
            "name",
            "city",
            "approx_cost(for two people)",
            "cuisines",
            "aggregate_rating",
        ]
        if col in candidates.columns
    ]
    subset = candidates[display_cols].head(max_candidates)

    lines.append("Candidate restaurants (tabular):")
    lines.append(subset.to_csv(index=False))
    lines.append("")

    # Output format instructions.
    lines.append("Respond with JSON using this schema:")
    lines.append(
        '[{"name": "...", "city": "...", "cuisines": "...", '
        '"price_for_two": 0, "rating": 0, "reason": "..."}]'
    )

    return "\n".join(lines)

