"""Leakage-aware grouped model evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import spectral_columns, validate_dataset


def build_huber_pipeline(k: int = 40) -> Pipeline:
    """All learned preprocessing stays inside each training fold."""
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("select", SelectKBest(score_func=f_regression, k=k)),
            ("model", HuberRegressor(max_iter=2000)),
        ]
    )


def grouped_oof_evaluation(
    frame: pd.DataFrame,
    target: str = "TOC",
    group_column: str = "Sample Number",
    n_splits: int = 5,
    k: int = 40,
) -> dict:
    """Return out-of-fold metrics while keeping repeated Sample Numbers together."""
    validate_dataset(frame)
    if target not in ("TOC", "N"):
        raise ValueError("target must be 'TOC' or 'N'")
    if group_column not in frame:
        raise ValueError(f"Missing group column: {group_column}")

    x = frame[spectral_columns(frame)].astype(float)
    y = frame[target].astype(float)
    groups = frame[group_column]
    unique_groups = groups.nunique()
    if unique_groups < n_splits:
        raise ValueError("Number of unique groups must be >= n_splits")

    k = min(k, x.shape[1])
    cv = GroupKFold(n_splits=n_splits)
    predictions = cross_val_predict(
        build_huber_pipeline(k=k), x, y, groups=groups, cv=cv, n_jobs=None
    )
    residuals = y.to_numpy() - predictions
    rmse = float(np.sqrt(mean_squared_error(y, predictions)))
    return {
        "target": target,
        "group_column": group_column,
        "n_observations": int(len(frame)),
        "n_groups": int(unique_groups),
        "n_splits": int(n_splits),
        "metrics": {
            "r2": float(r2_score(y, predictions)),
            "mae": float(mean_absolute_error(y, predictions)),
            "rmse": rmse,
            "bias": float(np.mean(predictions - y.to_numpy())),
        },
        "predictions": predictions.tolist(),
        "residuals": residuals.tolist(),
    }
