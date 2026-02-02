"""
Simple in-memory storage abstraction for Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class InMemoryRestaurantStore:
    """
    Holds the cleaned restaurant dataset in memory.
    """

    data: pd.DataFrame

    def is_empty(self) -> bool:
        return self.data.empty

    def count(self) -> int:
        return int(len(self.data.index))

    def head(self, n: int = 5) -> pd.DataFrame:
        return self.data.head(n)

