"""
Dataset loading for Phase 1.

This module is responsible only for:
- Downloading/loading the Zomato dataset from Hugging Face.
- Exposing it as a pandas DataFrame for downstream cleaning.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from datasets import load_dataset

from .config import DatasetConfig, DEFAULT_CONFIG


class HFDatasetLoader:
    """
    Loads the Zomato dataset from Hugging Face as a pandas DataFrame.
    """

    def __init__(self, config: DatasetConfig | None = None) -> None:
        self._config = config or DEFAULT_CONFIG

    @property
    def config(self) -> DatasetConfig:
        return self._config

    def load(self) -> pd.DataFrame:
        """
        Load the configured dataset split from Hugging Face.

        Returns:
            A pandas DataFrame containing the raw dataset.
        """
        dataset = load_dataset(self._config.hf_dataset_name, split=self._config.split)
        # Convert to pandas for easier downstream manipulation.
        return dataset.to_pandas()

