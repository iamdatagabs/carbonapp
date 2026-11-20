"""Nested grouped-CV benchmark separating depth and spectral information."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import BayesianRidge, ElasticNet, HuberRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data import spectral_columns, validate_dataset
from .preprocessing import build_preprocessor

SCENARIOS = {
    "depth_only": ("depth", "raw"),
    "nir_raw": ("nir", "raw"),
    "nir_raw_plus_depth": ("combined", "raw"),
    "nir_savgol_first_derivative": ("nir", "savgol_first_derivative"),
    "nir_savgol_first_derivative_plus_depth": ("combined", "savgol_first_derivative"),
}
MODELS = ("bayesian_ridge", "elastic_net", "huber", "extra_trees")


def _metrics(y, pred):
    return {
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "bias": float(np.mean(np.asarray(pred) - np.asarray(y))),
    }


def _estimator(scenario, model, n_bands, k, seed):
    kind, prep = SCENARIOS[scenario]
    transformers = []
    if kind in ("nir", "combined"):
        transformers.append(("nir", build_preprocessor(prep), list(range(n_bands))))
    if kind in ("depth", "combined"):
        transformers.append(("depth", OneHotEncoder(handle_unknown="ignore",
            sparse_output=False), [n_bands]))
    features = ColumnTransformer(transformers, remainder="drop")
    steps = [("features", features), ("select", SelectKBest(f_regression, k=k))]
    if model == "bayesian_ridge":
        steps += [("scale", StandardScaler()), ("model", BayesianRidge())]
    elif model == "elastic_net":
        steps += [("scale", StandardScaler()),
                  ("model", ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=20000, random_state=seed))]
    elif model == "huber":
        steps += [("scale", StandardScaler()), ("model", HuberRegressor(max_iter=3000))]
    elif model == "extra_trees":
        steps += [("model", ExtraTreesRegressor(n_estimators=150, min_samples_leaf=2,
            max_features=1.0, random_state=seed, n_jobs=1))]
    else:
        raise ValueError(f"Unsupported model: {model}")
    return Pipeline(steps)


def nested_depth_nir_benchmark(frame, group_column="Amostra", outer_splits=5,
        inner_splits=4, k=40, models=MODELS, random_state=42):
    """Compare depth-only, NIR-only and combined models with nested grouped CV."""
    validate_dataset(frame)
    if group_column not in ("Amostra", "Sample Number"):
        raise ValueError("group_column must be 'Amostra' or 'Sample Number'")
    if outer_splits < 2 or inner_splits < 2:
        raise ValueError("At least two outer and inner folds are required")
    if not models or set(models) - set(MODELS):
        raise ValueError("Unsupported or empty model list")

    bands = spectral_columns(frame)
    nir = frame[bands].astype(float).to_numpy()
    depth = frame["Profundidade"].astype(str).to_numpy().reshape(-1, 1)
    x = np.column_stack([nir, depth])
    y = frame["TOC"].astype(float).to_numpy()
    groups = frame[group_column].to_numpy()
    n_groups = int(pd.Series(groups).nunique())
    if n_groups < outer_splits:
        raise ValueError("Number of unique groups must be >= outer_splits")

    predictions = {name: np.full(len(frame), np.nan) for name in SCENARIOS}
    baseline = np.full(len(frame), np.nan)
    fold_results = {name: [] for name in SCENARIOS}

    for fold, (train, test) in enumerate(
        GroupKFold(n_splits=outer_splits).split(x, y, groups), start=1
    ):
        x_train, x_test = x[train], x[test]
        y_train, y_test = y[train], y[test]
        train_groups = groups[train]
        if pd.Series(train_groups).nunique() < inner_splits:
            raise ValueError("Outer training partition has too few groups for inner CV")
        inner = GroupKFold(n_splits=inner_splits)
        baseline[test] = float(y_train.mean())

        for scenario in SCENARIOS:
            if scenario == "depth_only":
                n_features = int(frame["Profundidade"].nunique())
            elif "plus_depth" in scenario:
                n_features = len(bands) + int(frame["Profundidade"].nunique())
            else:
                n_features = len(bands)
            selected_k = min(k, n_features)
            scores = {}
            for model in models:
                estimator = _estimator(scenario, model, len(bands), selected_k, random_state)
                oof = cross_val_predict(estimator, x_train, y_train, groups=train_groups,
                    cv=inner, n_jobs=None)
                scores[model] = float(np.sqrt(mean_squared_error(y_train, oof)))
            selected_model = min(scores, key=scores.get)
            estimator = _estimator(scenario, selected_model, len(bands), selected_k, random_state)
            estimator.fit(x_train, y_train)
            pred = estimator.predict(x_test)
            predictions[scenario][test] = pred
            fold_results[scenario].append({
                "fold": fold, "selected_model": selected_model, "inner_rmse": scores,
                "outer_metrics": _metrics(y_test, pred),
                "n_train_groups": int(pd.Series(train_groups).nunique()),
                "n_test_groups": int(pd.Series(groups[test]).nunique()),
            })

    if np.isnan(baseline).any() or any(np.isnan(p).any() for p in predictions.values()):
        raise RuntimeError("Nested CV did not generate predictions for every row")

    results = {}
    for scenario, pred in predictions.items():
        results[scenario] = {
            "metrics": _metrics(y, pred), "folds": fold_results[scenario],
            "selected_model_counts": {m: sum(f["selected_model"] == m
                for f in fold_results[scenario]) for m in models},
            "predictions": pred.tolist(), "residuals": (y - pred).tolist(),
        }
    baseline_metrics = _metrics(y, baseline)
    return {
        "target": "TOC", "group_column": group_column, "n_observations": len(frame),
        "n_groups": n_groups, "n_spectral_bands": len(bands),
        "outer_splits": outer_splits, "inner_splits": inner_splits,
        "depth_encoding": "categorical one-hot by the nine predefined profile layers",
        "scenarios": results,
        "fold_specific_mean_baseline": {"metrics": baseline_metrics,
            "predictions": baseline.tolist()},
        "interpretation": (
            "Depth-only measures predictive information in layer identity. NIR-only measures "
            "spectral prediction without layer identity. Combined measures their joint predictive "
            "value; it does not by itself prove incremental causal or chemical information. "
            "All preprocessing, feature selection and model selection are fitted within training "
            "folds. Grouped validation by sampling point is the primary transfer assessment."
        ),
    }
