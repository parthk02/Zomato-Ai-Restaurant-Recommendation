"""
Data access / repository layer for Phase 3 integration.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from phase1_data_ingestion.storage import InMemoryRestaurantStore
from phase2_user_input.models import NormalizedUserInput


@dataclass
class RestaurantRepository:
    """
    Simple repository that queries the in-memory restaurant store.
    """

    store: InMemoryRestaurantStore
    city_column: str = "city"
    price_column: str = "approx_cost(for two people)"

    def get_candidates(self, user_input: NormalizedUserInput) -> pd.DataFrame:
        """
        Filter restaurants by city and, if provided, by price range.
        """
        df = self.store.data

        # Filter by city (exact match on normalized lowercase).
        if self.city_column in df.columns:
            df = df[df[self.city_column] == user_input.city]

        # Filter by price range if available.
        if user_input.price_range is not None and self.price_column in df.columns:
            lower, upper = user_input.price_range
            if lower is not None:
                df = df[df[self.price_column] >= lower]
            if upper is not None:
                df = df[df[self.price_column] <= upper]

        return df.reset_index(drop=True)

