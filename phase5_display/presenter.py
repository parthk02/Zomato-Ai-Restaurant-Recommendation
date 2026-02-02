"""
Presentation utilities for Phase 5.

These helpers are UI-agnostic but optimized for CLI text output.
"""

from __future__ import annotations

from typing import Iterable, List

from phase4_recommendation.models import RecommendedRestaurant


def format_recommendations_text(
    recommendations: Iterable[RecommendedRestaurant],
    max_items: int = 10,
) -> str:
    """
    Format recommendations as a human-readable multiline string
    suitable for CLI output.
    """
    recs: List[RecommendedRestaurant] = list(recommendations)[:max_items]
    if not recs:
        return "No recommendations available."

    lines: List[str] = []
    lines.append("Top restaurant recommendations:")

    for idx, r in enumerate(recs, start=1):
        header = f"{idx}. {r.name}"
        if r.city:
            header += f" ({r.city})"

        meta_parts: List[str] = []
        if r.price_for_two is not None:
            meta_parts.append(f"price_for_two={int(r.price_for_two)}")
        if r.rating is not None:
            meta_parts.append(f"rating={r.rating:.1f}")
        if meta_parts:
            header += " [" + ", ".join(meta_parts) + "]"

        lines.append(header)

        if r.cuisines:
            lines.append(f"   Cuisines: {r.cuisines}")
        if r.reason:
            lines.append(f"   Reason: {r.reason}")

    return "\n".join(lines)

