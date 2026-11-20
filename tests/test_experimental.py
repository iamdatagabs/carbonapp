import numpy as np
import pandas as pd
import pytest

from carbonapp.experimental import (
    aggregate_replicate_rows,
    audit_sample_structure,
    paired_depth_bootstrap,
)


def design_frame():
    return pd.DataFrame({
        "Indice": [1, 2, 3, 4, 5, 6],
        "Amostra": ["P1", "P1", "P1", "P2", "P2", "P2"],
        "Profundidade": ["A", "A", "B", "A", "B", "B"],
        "Sample Number": [101, 101, 102, 201, 202, 202],
        "TOC": [10.0, 10.0, 8.0, 12.0, 9.0, 9.0],
        "N": [1.0, 1.0, 0.8, 1.2, 0.9, 0.9],
        "r1100": [0.1, 0.3, 0.2, 0.4, 0.5, 0.7],
        "r1102": [0.4, 0.6, 0.3, 0.2, 0.1, 0.3],
    })


def test_design_audit_reports_repeated_scan_ids_and_profile_depths():
    result = audit_sample_structure(design_frame())
    assert result["n_rows"] == 6
    assert result["n_profiles"] == 2
    assert result["n_replicate_ids"] == 4
    assert result["n_replicate_ids_repeated"] == 2
    assert result["inconsistent_target_ids"] == {"TOC": 0, "N": 0}


def test_aggregate_replicates_averages_spectra_and_preserves_targets():
    result = aggregate_replicate_rows(design_frame())
    assert len(result) == 4
    row = result.loc[result["Sample Number"] == 101].iloc[0]
    assert row["TOC"] == 10.0
    assert np.isclose(row["r1100"], 0.2)


def test_aggregate_rejects_conflicting_targets_within_replicate_id():
    frame = design_frame()
    frame.loc[1, "TOC"] = 11.0
    with pytest.raises(ValueError, match="conflicting"):
        aggregate_replicate_rows(frame)


def test_paired_depth_bootstrap_resamples_profiles():
    result = paired_depth_bootstrap(
        design_frame(), target="TOC", depth_a="A", depth_b="B",
        n_bootstrap=500, random_state=7,
    )
    assert result["n_paired_profiles"] == 2
    assert result["mean_paired_difference"] == -2.5
    assert result["contrast"] == "B - A"
    assert len(result["bootstrap_ci"]) == 2
