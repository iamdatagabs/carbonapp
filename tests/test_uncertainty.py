import numpy as np
import pandas as pd
import pytest
from carbonapp.uncertainty import _finite_sample_quantile, grouped_split_conformal

def synthetic_frame(n_groups=40, repeats=2, n_features=8):
    rng = np.random.default_rng(17); rows = []
    for group in range(n_groups):
        latent = rng.normal(size=n_features)
        for repeat in range(repeats):
            row = {"Indice": len(rows), "Amostra": group // 2, "Profundidade": "A" if repeat == 0 else "B", "Sample Number": f"S{group}", "TOC": float(5 + latent[0] - latent[1] + rng.normal(0, 0.02)), "N": float(0.4 + latent[0] * 0.1)}
            row.update({f"r{1100+2*i}": float(latent[i] + rng.normal(0, 0.01)) for i in range(n_features)})
            rows.append(row)
    return pd.DataFrame(rows)

def test_conformal_quantile_uses_finite_sample_correction():
    assert _finite_sample_quantile(np.arange(1, 10), 0.10) == 9.0
    assert np.isinf(_finite_sample_quantile(np.arange(1, 5), 0.10))

def test_grouped_split_conformal_separates_groups_and_returns_intervals():
    result = grouped_split_conformal(synthetic_frame(), group_column="Sample Number", calibration_size=0.25, test_size=0.20, k=4)
    assert result["n_train_groups"] + result["n_calibration_groups"] + result["n_test_groups"] == 40
    assert result["n_test_rows"] == len(result["test_predictions"])
    assert len(result["test_lower"]) == len(result["test_upper"])
    assert 0.0 <= result["metrics"]["row_coverage"] <= 1.0

def test_conformal_rejects_invalid_alpha():
    with pytest.raises(ValueError, match="alpha"): grouped_split_conformal(synthetic_frame(), alpha=1.0)
