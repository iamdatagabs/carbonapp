"""Reusable utilities for wavelength-indexed NIR spectral matrices."""
from __future__ import annotations

import re
from collections import defaultdict
from numbers import Integral

import numpy as np
import pandas as pd

_SPECTRAL_COLUMN = re.compile(r"^r(?P<wavelength_nm>\d+)$")


def wavelength_nm(column_name: str) -> int | None:
    """Return the wavelength encoded in a column such as r1470.

    Non-spectral column names return None. The convention is an integer
    wavelength in nanometres prefixed by a lowercase r.
    """
    match = _SPECTRAL_COLUMN.fullmatch(str(column_name))
    return int(match.group("wavelength_nm")) if match else None


def spectral_columns(frame: pd.DataFrame) -> list[str]:
    """Return spectral columns ordered by wavelength, rejecting aliases."""
    by_wavelength: dict[int, list[str]] = defaultdict(list)
    for column in frame.columns:
        wavelength = wavelength_nm(str(column))
        if wavelength is not None:
            by_wavelength[wavelength].append(str(column))

    duplicates = {nm: names for nm, names in by_wavelength.items() if len(names) > 1}
    if duplicates:
        details = "; ".join(
            f"{nm} nm: {', '.join(names)}" for nm, names in sorted(duplicates.items())
        )
        raise ValueError(f"Duplicate spectral wavelengths detected ({details})")

    return [
        names[0]
        for _, names in sorted(
            ((nm, names) for nm, names in by_wavelength.items()), key=lambda item: item[0]
        )
    ]


def select_spectral_window(
    frame: pd.DataFrame,
    start_nm: int,
    end_nm: int,
) -> pd.DataFrame:
    """Return an inclusive wavelength window, ordered by wavelength.

    The input frame is not modified. Raises ValueError when the interval
    is invalid or contains no spectral columns.
    """
    if (
        isinstance(start_nm, bool)
        or isinstance(end_nm, bool)
        or not isinstance(start_nm, Integral)
        or not isinstance(end_nm, Integral)
    ):
        raise TypeError("Wavelength bounds must be integers in nanometres")
    if start_nm < 0 or end_nm < start_nm:
        raise ValueError("Expected 0 <= start_nm <= end_nm")

    columns = [
        column
        for column in spectral_columns(frame)
        if start_nm <= wavelength_nm(column) <= end_nm
    ]
    if not columns:
        raise ValueError(f"No spectral bands found in the interval {start_nm}-{end_nm} nm")
    return frame.loc[:, columns].copy()


def validate_spectral_matrix(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
) -> list[str]:
    """Validate selected spectral columns as numeric, finite observations.

    Returns the validated column names without changing the input frame.
    """
    available = spectral_columns(frame)
    selected = available if columns is None else list(columns)
    if not selected:
        raise ValueError("At least one spectral column is required")

    missing = [column for column in selected if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing spectral columns: {', '.join(missing)}")
    non_spectral = [column for column in selected if column not in available]
    if non_spectral:
        raise ValueError(f"Not spectral columns: {', '.join(non_spectral)}")

    matrix = frame.loc[:, selected].apply(pd.to_numeric, errors="coerce")
    values = matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Spectral matrix contains missing, non-numeric or non-finite values")
    return selected
