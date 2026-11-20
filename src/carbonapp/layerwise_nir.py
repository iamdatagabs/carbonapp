"""Exploratory NIR prediction benchmark within each soil depth layer."""

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


def _aggregate_point_depth(frame, bands):
    """Collapse repeated records to one mean spectrum per point and depth."""
    target_counts = frame.groupby(["Amostra", "Profundidade"])["TOC"].nunique()
    if (target_counts > 1).any():
        raise ValueError("TOC must be constant within each point-depth combination")
    aggregations = {band: "mean" for band in bands}
    aggregations["TOC"] = "mean"
    return frame.groupby(
        ["Amostra", "Profundidade"], as_index=False, sort=False
    ).agg(aggregations)


def benchmark_nir_by_depth(
    frame, outer_splits=5, inner_splits=4, k=40,
    models=MODELS, random_state=42,
):
    """Evaluate whether NIR predicts TOC within each depth, grouped by point."""
    validate_dataset(frame)
    if outer_splits < 2 or inner_splits < 2:
        raise ValueError("At least two outer and inner folds are required")
    if not models or set(models) - set(MODELS):
        raise ValueError("Unsupported or empty model list")

    bands = spectral_columns(frame)
    data = _aggregate_point_depth(frame, bands)
    layers = list(pd.unique(data["Profundidade"].astype(str)))
    results = {}

    for layer in layers:
        subset = data[data["Profundidade"].astype(str) == layer].copy()
        x = subset[bands].astype(float).to_numpy()
        y = subset["TOC"].astype(float).to_numpy()
        groups = subset["Amostra"].to_numpy()
        n_groups = int(pd.Series(groups).nunique())
        n_outer = min(outer_splits, n_groups)
        if n_outer < 2:
            continue
        n_inner = min(inner_splits, n_groups - int(np.ceil(n_groups / n_outer)))
        if n_inner < 2:
            continue

        predictions = {prep: np.full(len(subset), np.nan) for prep in PREPROCESSING}
        baseline = np.full(len(subset), np.nan)
        folds = {prep: [] for prep in PREPROCESSING}

        for fold, (train_idx, test_idx) in enumerate(
            GroupKFold(n_splits=n_outer).split(x, y, groups), start=1
        ):
            x_train, x_test = x[train_idx], x[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            g_train = groups[train_idx]
            baseline_value = float(np.mean(y_train))
            baseline[test_idx] = baseline_value
            inner_count = min(n_inner, pd.Series(g_train).nunique())
            inner_splits_list = list(
                GroupKFold(n_splits=inner_count).split(x_train, y_train, g_train)
            )

            for prep in PREPROCESSING:
                scores = {}
                scenario = "nir_raw" if prep == "raw" else "nir_savgol_first_derivative"
                for model in models:
                    squared_errors = []
                    for inner_train, inner_valid in inner_splits_list:
                        inner_mean = float(np.mean(y_train[inner_train]))
                        residual_train = y_train[inner_train] - inner_mean
                        estimator = _estimator(
                            scenario, model, len(bands), min(k, len(bands)), random_state
                        )
                        estimator.fit(x_train[inner_train], residual_train)
                        valid_pred = inner_mean + estimator.predict(x_train[inner_valid])
                        squared_errors.extend((y_train[inner_valid] - valid_pred) ** 2)
                    scores[model] = float(np.sqrt(np.mean(squared_errors)))

                selected = min(scores, key=scores.get)
                residual_train = y_train - baseline_value
                estimator = _estimator(
                    scenario, selected, len(bands), min(k, len(bands)), random_state
                )
                estimator.fit(x_train, residual_train)
                pred = baseline_value + estimator.predict(x_test)
                predictions[prep][test_idx] = pred
                folds[prep].append({
                    "fold": fold,
                    "selected_model": selected,
                    "inner_rmse": scores,
                    "outer_metrics": _metrics(y_test, pred),
                    "mean_baseline_metrics": _metrics(
                        y_test, np.full(len(y_test), baseline_value)
                    ),
                    "n_train_points": int(pd.Series(g_train).nunique()),
                    "n_test_points": int(pd.Series(groups[test_idx]).nunique()),
                })

        layer_result = {
            "n_observations": len(subset),
            "n_points": n_groups,
            "outer_splits": n_outer,
            "inner_splits": n_inner,
            "mean_baseline": _metrics(y, baseline),
            "scenarios": {},
        }
        for prep, pred in predictions.items():
            if np.isnan(pred).any():
                raise RuntimeError(f"Incomplete predictions for layer {layer}, {prep}")
            layer_result["scenarios"][prep] = {
                "metrics": _metrics(y, pred),
                "folds": folds[prep],
                "selected_model_counts": {
                    model: sum(item["selected_model"] == model for item in folds[prep])
                    for model in models
                },
                "predictions": pred.tolist(),
                "residuals": (y - pred).tolist(),
            }
        results[layer] = layer_result

    return {
        "target": "TOC",
        "group_column": "Amostra",
        "aggregation": "mean spectrum and mean TOC per Amostra × Profundidade",
        "n_input_rows": len(frame),
        "n_point_depth_observations": len(data),
        "n_spectral_bands": len(bands),
        "method": (
            "Each depth layer is modeled independently. Repeated rows are averaged "
            "within each sampling-point/depth pair. Nested GroupKFold keeps all rows "
            "from a sampling point in one fold. NIR models predict deviations from "
            "the training-fold mean TOC for that layer."
        ),
        "layers": results,
        "interpretation": (
            "Exploratory layer-specific predictive assessment. Small per-layer point "
            "counts and multiple layer comparisons limit inference; results do not "
            "establish chemical specificity or external validity."
        ),
    }
