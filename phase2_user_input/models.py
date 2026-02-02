"""
Core models for Phase 2 user input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class RawUserInput:
    """
    Raw strings as received from CLI/Web.
    """

    city: str
    price_text: str


@dataclass
class NormalizedUserInput:
    """
    Cleaned and structured user input ready for the recommendation layer.
    """

    city: str  # normalized, lowercase city
    price_range: Optional[Tuple[Optional[float], Optional[float]]]
    price_bucket: Optional[str]

