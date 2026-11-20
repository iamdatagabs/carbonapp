import numpy as np
import pandas as pd

from carbonapp.layerwise_nir import benchmark_nir_by_depth


def test_layerwise_benchmark_aggregates_repeats_and_returns_grouped_predictions():
    rows = []
    rng = np.random.default_rng(17)
    for point in range(10):
        for layer, base in zip("ABC", (30.0, 15.0, 5.0)):
            signal = rng.normal()
            toc = base + 0.8 * signal + rng.normal(scale=0.05)
            for repeat in range(2):
                row = {
                    "Indice": len(rows), "Amostra": point,
                    "Profundidade": layer, "Sample Number": f"{point}-{layer}",
                    "TOC": toc, "N": 0.5,
                }
                row.update({
                    f"r{1100 + 2*i}": 0.04 + signal * (i + 1) * 0.0001
                    for i in range(11)
                })
                rows.append(row)
    result = benchmark_nir_by_depth(
        pd.DataFrame(rows), outer_splits=5, inner_splits=3,
        k=5, models=("bayesian_ridge",), random_state=3,
    )
    assert result["n_input_rows"] == 60
    assert result["n_point_depth_observations"] == 30
    assert set(result["layers"]) == set("ABC")
    for item in result["layers"].values():
        assert item["n_points"] == 10
        for prep in ("raw", "savgol_first_derivative"):
            scenario = item["scenarios"][prep]
            assert len(scenario["predictions"]) == 10
            assert np.isfinite(scenario["predictions"]).all()
            assert len(scenario["folds"]) == 5


def test_layerwise_benchmark_rejects_inconsistent_toc_within_point_depth():
    rows = []
    for point in range(6):
        row = {
            "Indice": point, "Amostra": point, "Profundidade": "A",
            "Sample Number": f"{point}-A", "TOC": float(point + 1), "N": 0.5,
        }
        row.update({f"r{1100 + 2*i}": 0.04 for i in range(11)})
        rows.append(row)
    rows.append({**rows[0], "Indice": 99, "TOC": 99.0})
    try:
        benchmark_nir_by_depth(
            pd.DataFrame(rows), outer_splits=3, inner_splits=2,
            k=5, models=("bayesian_ridge",),
        )
    except ValueError as exc:
        assert "TOC must be constant" in str(exc)
    else:
        raise AssertionError("Expected inconsistent point-depth TOC to be rejected")
