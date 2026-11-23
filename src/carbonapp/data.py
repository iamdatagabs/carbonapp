"""Dataset loading and structural validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .depth import DEPTH_BY_CODE
from .spectra import spectral_columns

IDENTIFIER_COLUMNS = ("Indice", "Amostra", "Profundidade", "Sample Number")
TARGET_COLUMNS = ("TOC", "N")


def load_dataset(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    validate_dataset(frame)
    return frame


def validate_dataset(frame: pd.DataFrame) -> None:
    """Validate schema without assuming target units or scientific provenance."""
    required = set(IDENTIFIER_COLUMNS + TARGET_COLUMNS)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    bands = spectral_columns(frame)
    if not bands:
        raise ValueError("No spectral columns found (expected names such as r1100)")

    if frame.empty:
        raise ValueError("Dataset is empty")

    if frame[list(TARGET_COLUMNS)].isna().any().any():
        raise ValueError("Target columns TOC/N contain missing values")
    if not set(frame["Profundidade"].dropna().unique()).issubset(DEPTH_BY_CODE):
        unknown = sorted(set(frame["Profundidade"].dropna().unique()) - set(DEPTH_BY_CODE))
        raise ValueError(f"Unknown depth codes: {unknown}")
    if frame["Sample Number"].isna().any():
        raise ValueError("Sample Number is required for grouped validation")

    numeric_bands = frame[bands].apply(pd.to_numeric, errors="coerce")
    if numeric_bands.isna().any().any():
        raise ValueError("Spectral matrix contains missing or non-numeric values")
