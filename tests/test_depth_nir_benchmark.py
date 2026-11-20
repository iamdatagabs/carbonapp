import numpy as np
import pandas as pd

from carbonapp.depth_nir_benchmark import nested_depth_nir_benchmark


def synthetic_frame(n_groups=15, n_features=12):
    rng = np.random.default_rng(71)
    rows = []
    for group in range(n_groups):
        for layer, code in enumerate("ABC"):
            latent = rng.normal(size=n_features)
            row = {"Indice": len(rows), "Amostra": group,
                "Profundidade": code, "Sample Number": f"S{group}-{code}",
                "TOC": float(25 - 5 * layer + 0.2 * latent[0] + rng.normal(0, .1)),
                "N": float(0.5 + 0.01 * latent[0])}
            row.update({f"r{1100 + 2*i}": float(0.04 + latent[i] * .001)
                for i in range(n_features)})
            rows.append(row)
    return pd.DataFrame(rows)


def test_depth_nir_benchmark_returns_all_scenarios_and_grouped_predictions():
    result = nested_depth_nir_benchmark(synthetic_frame(), group_column="Amostra",
        outer_splits=3, inner_splits=2, models=("bayesian_ridge",))
    assert set(result["scenarios"]) == {
        "depth_only", "nir_raw", "nir_raw_plus_depth",
        "nir_savgol_first_derivative", "nir_savgol_first_derivative_plus_depth"}
    assert len(result["scenarios"]["depth_only"]["predictions"]) == 45
    assert len(result["scenarios"]["nir_raw"]["folds"]) == 3
    assert np.isfinite(result["fold_specific_mean_baseline"]["metrics"]["rmse"])


def test_sample_number_grouping_is_supported():
    result = nested_depth_nir_benchmark(synthetic_frame(), group_column="Sample Number",
        outer_splits=3, inner_splits=2, models=("bayesian_ridge",))
    assert result["group_column"] == "Sample Number"
    assert result["n_groups"] == 45
