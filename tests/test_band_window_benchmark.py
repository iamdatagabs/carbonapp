import numpy as np
import pandas as pd
from carbonapp.band_window_benchmark import nested_band_window_benchmark

def test_band_window_benchmark_returns_grouped_complete_predictions():
    rng = np.random.default_rng(21)
    rows = []
    for point in range(10):
        point_signal = rng.normal()
        for layer, base in zip("ABC", (28.0, 14.0, 5.0)):
            row = {"Indice": len(rows), "Amostra": point, "Profundidade": layer,
                   "Sample Number": f"{point}-{layer}",
                   "TOC": base + 0.4 * point_signal + rng.normal(scale=0.2), "N": 0.5}
            for i in range(50):
                wavelength = 1400 + 2 * i
                signal = point_signal if 1440 <= wavelength <= 1488 else rng.normal(scale=0.1)
                row[f"r{wavelength}"] = 0.04 + signal * 0.0005 + rng.normal(scale=0.0001)
            rows.append(row)
    result = nested_band_window_benchmark(pd.DataFrame(rows), group_column="Amostra",
        outer_splits=5, inner_splits=3, k=8, models=("bayesian_ridge",),
        random_state=5, window_min_nm=1440, window_max_nm=1488)
    assert result["n_window_bands"] == 25
    assert len(result["depth_mean_baseline"]["predictions"]) == len(rows)
    for name in ("nir_full_raw", "nir_window_raw"):
        item = result["scenarios"][name]
        assert len(item["predictions"]) == len(rows)
        assert np.isfinite(item["predictions"]).all()
        assert len(item["folds"]) == 5
