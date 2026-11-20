"""Nested grouped-CV comparison of depth baseline, full NIR and a candidate band window."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from .data import spectral_columns, validate_dataset
from .depth_nir_benchmark import MODELS, _estimator

CANDIDATE_MIN_NM = 1440
CANDIDATE_MAX_NM = 1488

def _metrics(y, pred):
    return {"r2": float(r2_score(y, pred)), "mae": float(mean_absolute_error(y, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, pred))),
            "bias": float(np.mean(np.asarray(pred) - np.asarray(y)))}

def _layer_means(y, depth):
    frame = pd.DataFrame({"y": np.asarray(y, dtype=float), "depth": np.asarray(depth, dtype=str)})
    return frame.groupby("depth")["y"].mean().to_dict(), float(np.mean(y))

def _apply_layer_means(depth, means, fallback):
    return np.asarray([means.get(str(code), fallback) for code in depth], dtype=float)

def nested_band_window_benchmark(frame, group_column="Amostra", outer_splits=5,
        inner_splits=4, k=40, models=MODELS, random_state=42,
        window_min_nm=CANDIDATE_MIN_NM, window_max_nm=CANDIDATE_MAX_NM):
    """Compare a training-derived layer mean with full and fixed-window NIR.

    Model selection, preprocessing and feature selection occur only in inner
    grouped folds. The fixed wavelength window is an exploratory hypothesis
    selected from earlier analysis on this same dataset, not independent proof.
    """
    validate_dataset(frame)
    if group_column not in ("Amostra", "Sample Number"):
        raise ValueError("group_column must be 'Amostra' or 'Sample Number'")
    if outer_splits < 2 or inner_splits < 2:
        raise ValueError("At least two outer and inner folds are required")
    if not models or set(models) - set(MODELS):
        raise ValueError("Unsupported or empty model list")
    if window_min_nm > window_max_nm:
        raise ValueError("window_min_nm must be <= window_max_nm")
    all_bands = spectral_columns(frame)
    window_bands = [b for b in all_bands if window_min_nm <= int(b[1:]) <= window_max_nm]
    if len(window_bands) < 2:
        raise ValueError("Candidate window must contain at least two spectral bands")
    y = frame["TOC"].astype(float).to_numpy()
    depth = frame["Profundidade"].astype(str).to_numpy()
    groups = frame[group_column].to_numpy()
    n_groups = int(pd.Series(groups).nunique())
    if n_groups < outer_splits:
        raise ValueError("Number of unique groups must be >= outer_splits")
    band_sets = {"nir_full_raw": all_bands, "nir_window_raw": window_bands}
    predictions = {name: np.full(len(frame), np.nan) for name in band_sets}
    baseline = np.full(len(frame), np.nan)
    fold_results = {name: [] for name in band_sets}
    outer = GroupKFold(n_splits=outer_splits)
    for fold, (train_idx, test_idx) in enumerate(outer.split(np.zeros(len(frame)), y, groups), 1):
        y_train, y_test = y[train_idx], y[test_idx]
        d_train, d_test, g_train = depth[train_idx], depth[test_idx], groups[train_idx]
        if pd.Series(g_train).nunique() < inner_splits:
            raise ValueError("Outer training partition has too few groups for inner CV")
        layer_means, global_mean = _layer_means(y_train, d_train)
        baseline[test_idx] = _apply_layer_means(d_test, layer_means, global_mean)
        inner = list(GroupKFold(n_splits=inner_splits).split(
            np.zeros(len(train_idx)), y_train, g_train))
        for scenario, bands in band_sets.items():
            x = frame[bands].astype(float).to_numpy()
            x_train, x_test = x[train_idx], x[test_idx]
            scores = {}
            for model in models:
                errors = []
                for inner_train, inner_valid in inner:
                    means, fallback = _layer_means(y_train[inner_train], d_train[inner_train])
                    residual = y_train[inner_train] - _apply_layer_means(
                        d_train[inner_train], means, fallback)
                    estimator = _estimator("nir_raw", model, len(bands),
                                           min(k, len(bands)), random_state)
                    estimator.fit(x_train[inner_train], residual)
                    valid_base = _apply_layer_means(d_train[inner_valid], means, fallback)
                    valid_pred = valid_base + estimator.predict(x_train[inner_valid])
                    errors.extend((y_train[inner_valid] - valid_pred) ** 2)
                scores[model] = float(np.sqrt(np.mean(errors)))
            selected = min(scores, key=scores.get)
            residual_train = y_train - _apply_layer_means(d_train, layer_means, global_mean)
            estimator = _estimator("nir_raw", selected, len(bands),
                                   min(k, len(bands)), random_state)
            estimator.fit(x_train, residual_train)
            pred = baseline[test_idx] + estimator.predict(x_test)
            predictions[scenario][test_idx] = pred
            fold_results[scenario].append({
                "fold": fold, "selected_model": selected, "inner_rmse": scores,
                "outer_metrics": _metrics(y_test, pred),
                "layer_mean_baseline_metrics": _metrics(y_test, baseline[test_idx]),
                "n_train_groups": int(pd.Series(g_train).nunique()),
                "n_test_groups": int(pd.Series(groups[test_idx]).nunique())})
    if np.isnan(baseline).any() or any(np.isnan(p).any() for p in predictions.values()):
        raise RuntimeError("Nested CV did not generate predictions for every row")
    base_metrics = _metrics(y, baseline)
    scenarios = {}
    for name, pred in predictions.items():
        metrics = _metrics(y, pred)
        scenarios[name] = {
            "metrics": metrics,
            "delta_vs_layer_baseline": {key: float(metrics[key] - base_metrics[key])
                                        for key in ("mae", "rmse")},
            "folds": fold_results[name],
            "selected_model_counts": {m: sum(f["selected_model"] == m
                for f in fold_results[name]) for m in models},
            "predictions": pred.tolist(), "residuals": (y - pred).tolist()}
    return {
        "target": "TOC", "group_column": group_column, "n_observations": len(frame),
        "n_groups": n_groups, "n_full_spectral_bands": len(all_bands),
        "n_window_bands": len(window_bands), "window_nm": [window_min_nm, window_max_nm],
        "window_band_names": window_bands, "outer_splits": outer_splits,
        "inner_splits": inner_splits,
        "preprocessing": "raw reflectance; identical model-selection protocol for both NIR scenarios",
        "depth_mean_baseline": {"metrics": base_metrics, "predictions": baseline.tolist()},
        "scenarios": scenarios,
        "limitations": [
            "The candidate window was identified from prior stability analyses on this same dataset; this is exploratory post-selection evaluation, not independent confirmation.",
            "Grouped folds estimate transfer across the selected grouping unit; Sample Number semantics require confirmation.",
            "No spatial coordinates or independent external validation set are available.",
            "TOC units and laboratory reference method remain to be confirmed.",
            "N is not modeled; the target is TOC only."] }
