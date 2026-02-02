"""
Configuration for Phase 1 data ingestion.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetConfig:
    """
    Immutable configuration for the Zomato dataset source.
    """

    # Hugging Face dataset identifier
    hf_dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"

    # Split to load; most tabular datasets expose 'train'
    split: str = "train"


DEFAULT_CONFIG = DatasetConfig()

