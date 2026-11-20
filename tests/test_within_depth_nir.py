import numpy as np
import pandas as pd

from carbonapp.within_depth_nir import nested_within_depth_nir


def test_within_depth_residual_benchmark_is_grouped_and_returns_complete_predictions():
    rows = []
    rng = np.random.default_rng(7)
    for point in range(8):
        for layer, base in zip("ABC", (30.0, 15.0, 5.0)):
            signal = rng.normal()
            row = {
                "Indice": len(rows), "Amostra": point,
                "Profundidade": layer, "Sample Number": f"{point}-{layer}",
                "TOC": base + 0.7 * signal + rng.normal(scale=0.1), "N": 0.5,
            }
            row.update({f"r{1100 + 2*i}": 0.04 + signal * (i + 1) * 0.0001 for i in range(11)})
            rows.append(row)
    frame = pd.DataFrame(rows)
    result = nested_within_depth_nir(
        frame, group_column="Amostra", outer_splits=4, inner_splits=3,
        k=5, models=("bayesian_ridge",), random_state=11
    )
    assert result["n_observations"] == len(frame)
    assert len(result["depth_mean_baseline"]["predictions"]) == len(frame)
    for scenario in ("raw", "savgol_first_derivative"):
        item = result["scenarios"][scenario]
        assert len(item["predictions"]) == len(frame)
        assert np.isfinite(item["predictions"]).all()
        assert len(item["folds"]) == 4
