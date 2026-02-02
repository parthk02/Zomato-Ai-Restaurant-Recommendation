"""
Tests for Phase 1 data loader and cleaner.

These tests are lightweight and focus on structure/behavior rather than
downloading the full remote dataset.
"""

from __future__ import annotations

from unittest import mock

import pandas as pd

from phase1_data_ingestion.config import DatasetConfig
from phase1_data_ingestion.data_cleaner import DataCleaner, required_columns_present
from phase1_data_ingestion.data_loader import HFDatasetLoader


def test_loader_uses_configured_dataset_name_and_split() -> None:
    config = DatasetConfig(hf_dataset_name="dummy/name", split="train")
    loader = HFDatasetLoader(config=config)

    assert loader.config.hf_dataset_name == "dummy/name"
    assert loader.config.split == "train"


@mock.patch("phase1_data_ingestion.data_loader.load_dataset")
def test_loader_converts_to_pandas_dataframe(mock_load_dataset: mock.MagicMock) -> None:
    # Arrange: fake Hugging Face dataset with to_pandas
    fake_df = pd.DataFrame({"city": ["a", "b"], "approx_cost(for two people)": ["100", "200"]})

    class FakeHFDataset:
        def to_pandas(self) -> pd.DataFrame:  # type: ignore[override]
            return fake_df

    mock_load_dataset.return_value = FakeHFDataset()

    loader = HFDatasetLoader()

    # Act
    df = loader.load()

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == list(fake_df.columns)
    pd.testing.assert_frame_equal(df, fake_df)


def test_data_cleaner_normalizes_city_and_price() -> None:
    raw_df = pd.DataFrame(
        {
            "city": ["  Bangalore ", "DELHI", None],
            "approx_cost(for two people)": ["1,200", "800", "not_a_number"],
        }
    )
    cleaner = DataCleaner()

    cleaned = cleaner.clean(raw_df)

    # Rows with non-numeric prices should be dropped.
    assert len(cleaned) == 2
    # City normalization: strip + lower-case.
    assert set(cleaned["city"].tolist()) == {"bangalore", "delhi"}
    # Price normalization: commas removed and converted to numeric.
    assert cleaned["approx_cost(for two people)"].dtype.kind in {"i", "u", "f"}


def test_required_columns_present_helper() -> None:
    df = pd.DataFrame({"a": [1], "b": [2]})
    assert required_columns_present(df, ["a"])
    assert required_columns_present(df, ["a", "b"])
    assert not required_columns_present(df, ["a", "c"])

