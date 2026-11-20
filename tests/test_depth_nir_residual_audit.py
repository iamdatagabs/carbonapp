import numpy as np
import pandas as pd
import pytest

from carbonapp.depth_nir_residual_audit import build_residual_audit


def small_frame():
    rows = []
    for point in range(6):
        for layer, toc in zip("ABC", (30.0, 15.0, 5.0)):
            row = {"Indice": len(rows), "Amostra": point, "Profundidade": layer,
                   "Sample Number": f"{point}-{layer}", "TOC": toc, "N": 0.5}
            row.update({f"r{1100 + 2*i}": 0.04 + i * 0.0001 for i in range(3)})
            rows.append(row)
    return pd.DataFrame(rows)


def fake_result(group, offset):
    y = small_frame()["TOC"].to_numpy()
    depth_prediction = y + 1.0
    scenario_prediction = y + offset
    def folds(rmse):
        return [{"fold": i, "outer_metrics": {"rmse": rmse},
                 "selected_model": "bayesian_ridge"} for i in (1, 2)]
    return {
        "group_column": group, "n_observations": len(y),
        "scenarios": {
            "depth_only": {"predictions": depth_prediction.tolist(), "folds": folds(1.0)},
            "nir_raw_plus_depth": {"predictions": scenario_prediction.tolist(), "folds": folds(offset)},
        },
    }


def test_residual_audit_reports_depth_strata_and_paired_fold_deltas():
    frame = small_frame()
    by_depth, by_fold = build_residual_audit(frame, {
        "Amostra": fake_result("Amostra", 2.0),
    })
    assert set(by_depth["depth_code"]) == {"A", "B", "C"}
    assert len(by_depth) == 6
    delta = by_fold.query("scenario == 'nir_raw_plus_depth'")
    assert len(delta) == 2
    assert np.allclose(delta["delta_rmse_vs_depth_only"], 1.0)


def test_residual_audit_rejects_misaligned_prediction_length():
    result = fake_result("Amostra", 2.0)
    result["scenarios"]["depth_only"]["predictions"] = [1.0]
    with pytest.raises(ValueError, match="Invalid depth_only predictions"):
        build_residual_audit(small_frame(), {"Amostra": result})
