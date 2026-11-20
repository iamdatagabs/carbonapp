import numpy as np
import pandas as pd
import pytest
from carbonapp.model_comparison import build_model_pipeline, compare_grouped_models

def synthetic_frame(n_groups=12, repeats=2, n_features=8):
    rng = np.random.default_rng(7); rows = []
    for group in range(n_groups):
        latent = rng.normal(size=n_features)
        for repeat in range(repeats):
            row = {"Indice": len(rows), "Amostra": group // 3, "Profundidade": "A" if repeat == 0 else "B", "Sample Number": f"S{group}", "TOC": float(4 + latent[0]*2 - latent[1] + rng.normal(0, 0.03)), "N": float(0.5 + latent[0]*0.1)}
            row.update({f"r{1100+2*i}": float(latent[i] + rng.normal(0, 0.01)) for i in range(n_features)})
            rows.append(row)
    return pd.DataFrame(rows)

def test_pipeline_contains_fold_local_feature_selection():
    assert build_model_pipeline("huber", k=4).steps[0][0] == "select"

def test_comparison_produces_oof_predictions():
    frame = synthetic_frame()
    result = compare_grouped_models(frame, n_splits=3, k=5, models=("huber", "extra_trees"))
    assert result["n_observations"] == len(frame) and result["n_groups"] == 12
    assert len(result["models"]["huber"]["predictions"]) == len(frame)
    assert set(result["ranking_by_rmse"]) == {"huber", "extra_trees"}
    assert np.isfinite(result["models"]["huber"]["metrics"]["rmse"])

def test_invalid_model_and_too_few_groups_raise():
    with pytest.raises(ValueError, match="Unsupported models"): compare_grouped_models(synthetic_frame(), models=("random_forest",))
    with pytest.raises(ValueError, match="unique groups"): compare_grouped_models(synthetic_frame(n_groups=4), n_splits=5)
