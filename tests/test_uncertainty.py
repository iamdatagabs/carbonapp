import numpy as np
import pytest
from carbonapp.uncertainty import _finite_sample_quantile, grouped_split_conformal
from test_model_comparison import synthetic_frame

def test_conformal_quantile_uses_finite_sample_correction():
    assert _finite_sample_quantile(np.arange(1, 10), 0.10) == 9.0
    assert np.isinf(_finite_sample_quantile(np.arange(1, 5), 0.10))

def test_grouped_split_conformal_separates_groups_and_returns_intervals():
    frame = synthetic_frame(n_groups=40, repeats=2)
    result = grouped_split_conformal(frame, group_column="Sample Number", calibration_size=0.25, test_size=0.20, k=4)
    assert result["n_train_groups"] + result["n_calibration_groups"] + result["n_test_groups"] == 40
    assert result["n_test_rows"] == len(result["test_predictions"])
    assert len(result["test_lower"]) == len(result["test_upper"])
    assert result["metrics"]["row_coverage"] >= 0.0

def test_conformal_rejects_invalid_alpha():
    with pytest.raises(ValueError, match="alpha"):
        grouped_split_conformal(synthetic_frame(), alpha=1.0)
