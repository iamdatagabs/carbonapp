"""Leakage-safe test of NIR information in TOC residuals within depth layers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from .data import spectral_columns, validate_dataset
from .depth_nir_benchmark import MODELS, _estimator

PREPROCESSING = ("raw", "savgol_first_derivative")


def _metrics(y, pred):
    return {
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "bias": float(np.mean(np.asarray(pred) - np.asarray(y))),
    }


def _layer_means(y, depth):
    frame = pd.DataFrame({"y": np.asarray(y, dtype=float), "depth": np.asarray(depth, dtype=str)})
    means = frame.groupby("depth")["y"].mean().to_dict()
    return means, float(np.mean(y))


def _apply_layer_means(depth, means, fallback):
    return np.asarray([means.get(str(code), fallback) for code in depth], dtype=float)


def nested_within_depth_nir(frame, group_column="Amostra", outer_splits=5,
                            inner_splits=4, k=40, models=MODELS, random_state=42):
    """Predict TOC deviations from training-layer means using NIR only.

    Each inner split computes layer means from its training partition only.
    Outer-test predictions add a NIR-predicted residual to layer means learned
    from the complete outer-training partition.
    """
    validate_dataset(frame)
    if group_column not in ("Amostra", "Sample Number"):
        raise ValueError("group_column must be 'Amostra' or 'Sample Number'")
    if outer_splits < 2 or inner_splits < 2:
        raise ValueError("At least two outer and inner folds are required")
    if not models or set(models) - set(MODELS):
        raise ValueError("Unsupported or empty model list")

    bands = spectral_columns(frame)
    nir = frame[bands].astype(float).to_numpy()
    depth = frame["Profundidade"].astype(str).to_numpy()
    x = np.column_stack([nir, depth])
    y = frame["TOC"].astype(float).to_numpy()
    groups = frame[group_column].to_numpy()
    if pd.Series(groups).nunique() < outer_splits:
        raise ValueError("Number of unique groups must be >= outer_splits")

    predictions = {prep: np.full(len(frame), np.nan) for prep in PREPROCESSING}
    baseline = np.full(len(frame), np.nan)
    folds = {prep: [] for prep in PREPROCESSING}

    for fold, (train_idx, test_idx) in enumerate(
        GroupKFold(n_splits=outer_splits).split(x, y, groups), start=1
    ):
        x_train, x_test = x[train_idx], x[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        d_train, d_test = depth[train_idx], depth[test_idx]
        g_train = groups[train_idx]
        if pd.Series(g_train).nunique() < inner_splits:
            raise ValueError("Outer training partition has too few groups for inner CV")

        layer_means, global_mean = _layer_means(y_train, d_train)
        baseline[test_idx] = _apply_layer_means(d_test, layer_means, global_mean)
        inner_splits_list = list(GroupKFold(n_splits=inner_splits).split(x_train, y_train, g_train))

        for prep in PREPROCESSING:
            candidate_scores = {}
            for model in models:
                squared_errors = []
                for inner_train, inner_valid in inner_splits_list:
                    inner_means, inner_global = _layer_means(y_train[inner_train], d_train[inner_train])
                    residual_train = y_train[inner_train] - _apply_layer_means(
                        d_train[inner_train], inner_means, inner_global
                    )
                    estimator = _estimator(
                        "nir" if prep == "raw" else "nir_savgol_first_derivative",
                        model, len(bands), min(k, len(bands)), random_state
                    )
                    estimator.fit(x_train[inner_train], residual_train)
                    valid_base = _apply_layer_means(d_train[inner_valid], inner_means, inner_global)
                    valid_pred = valid_base + estimator.predict(x_train[inner_valid])
                    squared_errors.extend((y_train[inner_valid] - valid_pred) ** 2)
                candidate_scores[model] = float(np.sqrt(np.mean(squared_errors)))

            selected_model = min(candidate_scores, key=candidate_scores.get)
            residual_train = y_train - _apply_layer_means(d_train, layer_means, global_mean)
            estimator = _estimator(
                "nir" if prep == "raw" else "nir_savgol_first_derivative",
                selected_model, len(bands), min(k, len(bands)), random_state
            )
            estimator.fit(x_train, residual_train)
            pred = baseline[test_idx] + estimator.predict(x_test)
            predictions[prep][test_idx] = pred
            folds[prep].append({
                "fold": fold,
                "selected_model": selected_model,
                "inner_rmse": candidate_scores,
                "outer_metrics": _metrics(y_test, pred),
                "depth_mean_baseline_metrics": _metrics(y_test, baseline[test_idx]),
                "n_train_groups": int(pd.Series(g_train).nunique()),
                "n_test_groups": int(pd.Series(groups[test_idx]).nunique()),
            })

    if np.isnan(baseline).any() or any(np.isnan(p).any() for p in predictions.values()):
        raise RuntimeError("Nested CV did not generate predictions for every row")

    results = {}
    for prep, pred in predictions.items():
        results[prep] = {
            "metrics": _metrics(y, pred),
            "depth_mean_baseline_metrics": _metrics(y, baseline),
            "folds": folds[prep],
            "selected_model_counts": {
                model: sum(item["selected_model"] == model for item in folds[prep])
                for model in models
            },
            "predictions": pred.tolist(),
            "residuals": (y - pred).tolist(),
        }
    return {
        "target": "TOC",
        "group_column": group_column,
        "n_observations": len(frame),
        "n_groups": int(pd.Series(groups).nunique()),
        "n_spectral_bands": len(bands),
        "outer_splits": outer_splits,
        "inner_splits": inner_splits,
        "method": (
            "Within each training partition, compute mean TOC by categorical depth layer. "
            "Fit an NIR model to deviations from those training-only layer means. Add its "
            "prediction to the layer mean for validation/test rows. Recompute layer means "
            "inside every inner split; no validation/test target contributes to them."
        ),
        "depth_mean_baseline": {
            "metrics": _metrics(y, baseline),
            "predictions": baseline.tolist(),
        },
        "scenarios": results,
        "interpretation": (
            "This evaluates whether NIR predicts within-layer TOC deviations beyond a "
            "training-derived layer mean. It is predictive, not causal or chemical attribution."
        ),
    }
