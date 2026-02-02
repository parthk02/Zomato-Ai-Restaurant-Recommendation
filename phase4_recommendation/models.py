"""
Models used in Phase 4 recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RecommendedRestaurant:
    """
    Structured representation of a restaurant recommendation coming
    back from the LLM.
    """

    name: str
    city: Optional[str] = None
    cuisines: Optional[str] = None
    price_for_two: Optional[float] = None
    rating: Optional[float] = None
    reason: Optional[str] = None

