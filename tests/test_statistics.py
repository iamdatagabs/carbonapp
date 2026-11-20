import numpy as np
import pandas as pd

from carbonapp.statistics import (
    describe_by_depth,
    describe_spectra,
    describe_targets,
    target_band_associations,
)


def sample_frame():
    return pd.DataFrame({
        "Indice": [1, 2, 3, 4],
        "Amostra": ["P1", "P1", "P2", "P2"],
        "Profundidade": ["A", "B", "A", "B"],
        "Sample Number": [101, 102, 201, 202],
        "TOC": [10.0, 8.0, 12.0, 9.0],
        "N": [1.0, 0.8, 1.2, 0.9],
        "r1100": [0.1, 0.2, 0.3, 0.4],
        "r1102": [0.4, 0.3, 0.2, 0.1],
    })


def test_describe_targets_returns_unit_agnostic_summary():
    result = describe_targets(sample_frame())
    assert result["TOC"]["n"] == 4
    assert result["TOC"]["mean"] == 9.75
    assert result["N"]["min"] == 0.8


def test_depth_summary_uses_authoritative_layer_thickness():
    result = describe_by_depth(sample_frame(), targets=("TOC",))
    assert list(result["code"]) == ["A", "B"]
    assert list(result["thickness_cm"]) == [10, 10]
    assert list(result["n"]) == [2, 2]
    assert result.loc[result["code"] == "A", "mean"].iloc[0] == 11.0


def test_spectral_summary_parses_wavelengths():
    result = describe_spectra(sample_frame())
    assert list(result["wavelength_nm"]) == [1100, 1102]
    assert np.isclose(result.loc[0, "mean"], 0.25)


def test_band_associations_include_bh_adjusted_values():
    result = target_band_associations(sample_frame(), target="TOC")
    assert set(result["band"]) == {"r1100", "r1102"}
    assert result["q_value_bh"].between(0, 1).all()
