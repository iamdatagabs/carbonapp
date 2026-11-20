"""Group-aware split conformal prediction intervals."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from .data import spectral_columns, validate_dataset
from .model_comparison import SUPPORTED_MODELS, build_model_pipeline

def _finite_sample_quantile(scores: np.ndarray, alpha: float) -> float:
    """Conformal order statistic with the finite-sample +1 correction."""
    n = len(scores)
    rank = math.ceil((n + 1) * (1.0 - alpha))
    if rank > n:
        return float("inf")
    return float(np.sort(scores)[rank - 1])

def grouped_split_conformal(
    frame: pd.DataFrame, target: str = "TOC", group_column: str = "Sample Number",
    model_name: str = "huber", alpha: float = 0.10, k: int = 40,
    calibration_size: float = 0.35, test_size: float = 0.20, random_state: int = 42,
) -> dict:
    """Fit/calibrate/test intervals using disjoint groups at all three stages.

    Calibration scores are the maximum absolute residual within each calibration
    group. The resulting interval targets simultaneous within-group coverage,
    under exchangeability of independent groups. This is more conservative than
    row-wise conformal and avoids treating repeated rows as independent.
    """
    validate_dataset(frame)
    if target not in ("TOC", "N"): raise ValueError("target must be TOC or N")
    if group_column not in frame: raise ValueError(f"Missing group column: {group_column}")
    if model_name not in SUPPORTED_MODELS: raise ValueError(f"Unsupported model: {model_name}")
    if not 0.0 < alpha < 1.0: raise ValueError("alpha must be between 0 and 1")
    if not 0.0 < calibration_size < 1.0 or not 0.0 < test_size < 1.0 or calibration_size + test_size >= 1.0:
        raise ValueError("calibration_size and test_size must be positive and sum to less than 1")
    groups = frame[group_column].to_numpy()
    n_groups = pd.Series(groups).nunique()
    if n_groups < 6: raise ValueError("At least 6 unique groups are required for train/calibration/test splitting")
    x = frame[spectral_columns(frame)].astype(float)
    y = frame[target].astype(float).to_numpy()

    outer = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_cal_idx, test_idx = next(outer.split(x, y, groups))
    relative_cal_size = calibration_size / (1.0 - test_size)
    inner = GroupShuffleSplit(n_splits=1, test_size=relative_cal_size, random_state=random_state + 1)
    train_rel, cal_rel = next(inner.split(x.iloc[train_cal_idx], y[train_cal_idx], groups[train_cal_idx]))
    train_idx, cal_idx = train_cal_idx[train_rel], train_cal_idx[cal_rel]

    estimator = build_model_pipeline(model_name, min(k, x.shape[1]), random_state)
    estimator.fit(x.iloc[train_idx], y[train_idx])
    cal_pred = estimator.predict(x.iloc[cal_idx])
    cal_residual = np.abs(y[cal_idx] - cal_pred)
    cal_frame = pd.DataFrame({"group": groups[cal_idx], "score": cal_residual})
    group_scores = cal_frame.groupby("group", sort=False)["score"].max().to_numpy()
    q_hat = _finite_sample_quantile(group_scores, alpha)

    test_pred = estimator.predict(x.iloc[test_idx])
    lower, upper = test_pred - q_hat, test_pred + q_hat
    covered = (y[test_idx] >= lower) & (y[test_idx] <= upper)
    test_frame = pd.DataFrame({"group": groups[test_idx], "covered": covered})
    group_covered = test_frame.groupby("group", sort=False)["covered"].all().to_numpy()
    finite_width = float(2.0 * q_hat) if np.isfinite(q_hat) else float("inf")
    return {
        "target": target, "group_column": group_column, "model": model_name, "alpha": alpha,
        "nominal_coverage": 1.0 - alpha, "n_groups_total": int(n_groups),
        "n_train_groups": int(pd.Series(groups[train_idx]).nunique()),
        "n_calibration_groups": int(len(group_scores)),
        "n_test_groups": int(pd.Series(groups[test_idx]).nunique()),
        "n_train_rows": int(len(train_idx)), "n_calibration_rows": int(len(cal_idx)),
        "n_test_rows": int(len(test_idx)), "quantile": q_hat,
        "metrics": {
            "row_coverage": float(np.mean(covered)),
            "group_simultaneous_coverage": float(np.mean(group_covered)),
            "mean_interval_width": finite_width,
            "mae": float(mean_absolute_error(y[test_idx], test_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y[test_idx], test_pred))),
        },
        "test_predictions": test_pred.astype(float).tolist(),
        "test_lower": lower.astype(float).tolist(), "test_upper": upper.astype(float).tolist(),
        "test_group_coverage": group_covered.astype(bool).tolist(),
        "calibration_warning": ("The finite-sample quantile is infinite because the calibration set has too few independent groups for the requested alpha." if not np.isfinite(q_hat) else None),
        "assumptions": "Finite-sample group-level coverage requires exchangeable independent groups. If Amostra points are spatially dependent or nested in blocks/treatments, define those higher-level groups before interpreting coverage.",
    }
