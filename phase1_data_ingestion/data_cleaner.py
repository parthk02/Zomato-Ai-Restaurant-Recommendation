"""
Data cleaning and normalization for the Zomato dataset (Phase 1).
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd


class DataCleaner:
    """
    Cleans and normalizes core Zomato fields that are needed in later phases.
    """

    def __init__(
        self,
        city_column: str = "city",
        price_column: str = "approx_cost(for two people)",
    ) -> None:
        self.city_column = city_column
        self.price_column = price_column

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a cleaned copy of the DataFrame.

        Operations:
        - Drop exact duplicate rows.
        - Standardize city names (strip + lowercase).
        - Normalize price column to numeric, dropping rows where price is missing.
        """
        df_clean = df.copy()

        # Drop perfect duplicates.
        df_clean = df_clean.drop_duplicates()

        # Standardize city names when column exists.
        if self.city_column in df_clean.columns:
            df_clean[self.city_column] = (
                df_clean[self.city_column]
                .astype(str)
                .str.strip()
                .str.lower()
            )

        # Normalize price column if present.
        if self.price_column in df_clean.columns:
            df_clean[self.price_column] = (
                df_clean[self.price_column]
                .astype(str)
                .str.replace(",", "", regex=False)
            )
            df_clean[self.price_column] = pd.to_numeric(
                df_clean[self.price_column], errors="coerce"
            )
            df_clean = df_clean.dropna(subset=[self.price_column])

        return df_clean


def required_columns_present(df: pd.DataFrame, required: Iterable[str]) -> bool:
    """
    Helper to check that all required columns exist in the DataFrame.
    """
    missing = [col for col in required if col not in df.columns]
    return len(missing) == 0

