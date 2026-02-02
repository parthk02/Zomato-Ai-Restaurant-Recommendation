"""
End-to-end Phase 1 pipeline:
- Load raw data from Hugging Face.
- Clean and normalize it.
- Return an in-memory store.
"""

from __future__ import annotations

import pandas as pd

from .data_cleaner import DataCleaner
from .data_loader import HFDatasetLoader
from .storage import InMemoryRestaurantStore


def build_phase1_store() -> InMemoryRestaurantStore:
    """
    Run the full Phase 1 ingestion pipeline and return an in-memory store.
    """
    loader = HFDatasetLoader()
    raw_df: pd.DataFrame = loader.load()

    cleaner = DataCleaner()
    cleaned_df = cleaner.clean(raw_df)

    return InMemoryRestaurantStore(data=cleaned_df)

