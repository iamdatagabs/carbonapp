import pandas as pd
import pytest

from carbonapp.spectra import (
    select_spectral_window,
    spectral_columns,
    validate_spectral_matrix,
    wavelength_nm,
)


def test_wavelength_nm_parses_only_spectral_column_names():
    assert wavelength_nm("r1470") == 1470
    assert wavelength_nm("TOC") is None
    assert wavelength_nm("R1470") is None
    assert wavelength_nm("r1470_mean") is None


def test_spectral_columns_are_sorted_by_numeric_wavelength():
    frame = pd.DataFrame(columns=["r1488", "TOC", "r1100", "r1470"])
    assert spectral_columns(frame) == ["r1100", "r1470", "r1488"]


def test_spectral_columns_reject_duplicate_wavelength_aliases():
    frame = pd.DataFrame(columns=["r1100", "r01100"])
    with pytest.raises(ValueError, match="Duplicate spectral wavelengths"):
        spectral_columns(frame)


def test_select_spectral_window_is_inclusive_ordered_and_does_not_mutate():
    frame = pd.DataFrame({"r1488": [3.0], "TOC": [1.0], "r1440": [2.0], "r1438": [4.0]})
    selected = select_spectral_window(frame, 1440, 1488)
    assert selected.columns.tolist() == ["r1440", "r1488"]
    assert frame.columns.tolist() == ["r1488", "TOC", "r1440", "r1438"]
    assert selected.iloc[0].tolist() == [2.0, 3.0]


@pytest.mark.parametrize(("start", "end"), [(1488, 1440), (-1, 10)])
def test_select_spectral_window_rejects_invalid_bounds(start, end):
    with pytest.raises(ValueError):
        select_spectral_window(pd.DataFrame({"r1440": [1.0]}), start, end)


def test_validate_spectral_matrix_rejects_non_finite_values():
    frame = pd.DataFrame({"r1100": [1.0, float("inf")]})
    with pytest.raises(ValueError, match="non-finite"):
        validate_spectral_matrix(frame)
