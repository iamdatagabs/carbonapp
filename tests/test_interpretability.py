import numpy as np
import pandas as pd
import pytest

from carbonapp.interpretability import (
    depth_stratified_importance,
    feature_selection_stability,
    grouped_permutation_importance,
)


def synthetic_frame(n_groups=24, repeats=2, n_features=8):
    rng = np.random.default_rng(31)
    rows = []
    for group in range(n_groups):
        latent = rng.normal(size=n_features)
        for depth in ("A", "B", "C"):
            row = {
                "Indice": len(rows), "Amostra": group // 2, "Profundidade": depth,
                "Sample Number": f"S{group}", "TOC": float(7 + 2 * latent[0] - latent[1]),
                "N": float(0.5 + 0.1 * latent[0]),
            }
            row.update({f"r{1100 + 2*i}": float(latent[i] + rng.normal(0, 0.02)) for i in range(n_features)})
            rows.append(row)
    return pd.DataFrame(rows)


def test_feature_selection_stability_reports_frequency():
    result = feature_selection_stability(synthetic_frame(), n_splits=4, k=3)
    assert len(result) == 8
    assert result.selection_frequency.between(0, 1).all()
    assert result.selected_folds.max() <= 4


def test_grouped_permutation_importance_holds_out_groups():
    result = grouped_permutation_importance(
        synthetic_frame(), test_size=0.25, n_repeats=3, k=4
    )
    assert result["n_train_groups"] + result["n_test_groups"] == 24
    assert len(result["importance"]) == 8
    assert np.isfinite(result["baseline_test_rmse"])


def test_depth_stratified_importance_returns_layer_labels():
    result = depth_stratified_importance(
        synthetic_frame(), min_groups=8, n_repeats=2, k=4
    )
    assert set(result.depth_code) == {"A", "B", "C"}


def test_shap_is_optional_and_invalid_target_rejected():
    from carbonapp.interpretability import grouped_shap_explanation
    with pytest.raises(ValueError, match="target"):
        grouped_shap_explanation(synthetic_frame(), target="wrong")
