"""Leakage-aware comparison of regression models under grouped CV."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import BayesianRidge, ElasticNet, HuberRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from .data import spectral_columns, validate_dataset

SUPPORTED_MODELS = ("huber", "extra_trees", "elastic_net", "bayesian_ridge")

def build_model_pipeline(model_name: str, k: int = 40, random_state: int = 42) -> Pipeline:
    """All learned preprocessing is fitted inside each training fold."""
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_name}. Choose from {SUPPORTED_MODELS}")
    if k < 1:
        raise ValueError("k must be >= 1")
    steps = [("select", SelectKBest(score_func=f_regression, k=k))]
    if model_name == "huber":
        steps.extend([("scale", StandardScaler()), ("model", HuberRegressor(max_iter=3000))])
    elif model_name == "extra_trees":
        steps.append(("model", ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2, max_features=1.0, random_state=random_state, n_jobs=1)))
    elif model_name == "elastic_net":
        steps.extend([("scale", StandardScaler()), ("model", ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=20000, random_state=random_state))])
    else:
        steps.extend([("scale", StandardScaler()), ("model", BayesianRidge())])
    return Pipeline(steps)

def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {"r2": float(r2_score(y_true, y_pred)), "mae": float(mean_absolute_error(y_true, y_pred)), "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))), "bias": float(np.mean(y_pred - y_true))}

def compare_grouped_models(frame: pd.DataFrame, target: str = "TOC", group_column: str = "Sample Number", n_splits: int = 5, k: int = 40, models: tuple[str, ...] = SUPPORTED_MODELS, random_state: int = 42) -> dict:
    """Return grouped OOF estimates; use nested grouped CV for final model selection."""
    validate_dataset(frame)
    if target not in ("TOC", "N"): raise ValueError("target must be TOC or N")
    if group_column not in frame: raise ValueError(f"Missing group column: {group_column}")
    if n_splits < 2: raise ValueError("n_splits must be >= 2")
    if not models: raise ValueError("At least one model must be selected")
    unknown = sorted(set(models).difference(SUPPORTED_MODELS))
    if unknown: raise ValueError(f"Unsupported models: {unknown}")
    bands = spectral_columns(frame)
    x, y, groups = frame[bands].astype(float), frame[target].astype(float).to_numpy(), frame[group_column]
    n_groups = int(groups.nunique())
    if n_groups < n_splits: raise ValueError("Number of unique groups must be >= n_splits")
    effective_k = min(k, len(bands))
    cv = GroupKFold(n_splits=n_splits)
    results = {}
    for name in models:
        pred = cross_val_predict(build_model_pipeline(name, effective_k, random_state), x, y, groups=groups, cv=cv, n_jobs=None)
        results[name] = {"metrics": _metrics(y, pred), "predictions": pred.astype(float).tolist(), "residuals": (y-pred).astype(float).tolist()}
    ranking = sorted(models, key=lambda name: (results[name]["metrics"]["rmse"], results[name]["metrics"]["mae"]))
    return {"target": target, "group_column": group_column, "n_observations": int(len(frame)), "n_groups": n_groups, "n_splits": int(n_splits), "n_features": len(bands), "k_features": effective_k, "models": results, "ranking_by_rmse": ranking, "selection_warning": "OOF candidate ranking is exploratory; use nested grouped CV or an untouched grouped test set for final performance."}


def nested_grouped_model_selection(
    frame: pd.DataFrame,
    target: str = "TOC",
    group_column: str = "Sample Number",
    outer_splits: int = 5,
    inner_splits: int = 4,
    k: int = 40,
    models: tuple[str, ...] = SUPPORTED_MODELS,
    random_state: int = 42,
) -> dict:
    """Estimate performance of model selection with nested grouped CV.

    The inner GroupKFold selects among the fixed candidate pipelines. The
    selected pipeline is refitted on the complete outer-training partition and
    evaluated once on the untouched outer fold. This estimates the selection
    procedure, not a final model trained on all observations.
    """
    validate_dataset(frame)
    if target not in ("TOC", "N"):
        raise ValueError("target must be TOC or N")
    if group_column not in frame:
        raise ValueError(f"Missing group column: {group_column}")
    if outer_splits < 2 or inner_splits < 2:
        raise ValueError("outer_splits and inner_splits must be >= 2")
    if not models:
        raise ValueError("At least one model must be selected")
    unknown = sorted(set(models).difference(SUPPORTED_MODELS))
    if unknown:
        raise ValueError(f"Unsupported models: {unknown}")

    bands = spectral_columns(frame)
    x = frame[bands].astype(float)
    y = frame[target].astype(float).to_numpy()
    groups = frame[group_column].to_numpy()
    if pd.Series(groups).nunique() < outer_splits:
        raise ValueError("Number of unique groups must be >= outer_splits")

    outer_cv = GroupKFold(n_splits=outer_splits)
    outer_predictions = np.full(len(frame), np.nan, dtype=float)
    fold_records = []

    for fold_number, (train_idx, test_idx) in enumerate(outer_cv.split(x, y, groups), start=1):
        x_train, x_test = x.iloc[train_idx], x.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        groups_train = groups[train_idx]
        if pd.Series(groups_train).nunique() < inner_splits:
            raise ValueError("Each outer training partition must contain >= inner_splits groups")

        inner_cv = GroupKFold(n_splits=inner_splits)
        candidate_scores = {}
        for name in models:
            inner_pred = cross_val_predict(
                build_model_pipeline(name, min(k, len(bands)), random_state),
                x_train, y_train, groups=groups_train, cv=inner_cv, n_jobs=None
            )
            candidate_scores[name] = float(np.sqrt(mean_squared_error(y_train, inner_pred)))

        selected = min(candidate_scores, key=candidate_scores.get)
        estimator = build_model_pipeline(selected, min(k, len(bands)), random_state)
        estimator.fit(x_train, y_train)
        fold_pred = estimator.predict(x_test)
        outer_predictions[test_idx] = fold_pred
        fold_records.append({
            "fold": fold_number,
            "selected_model": selected,
            "inner_rmse": candidate_scores,
            "outer_metrics": _metrics(y_test, fold_pred),
            "n_train_groups": int(pd.Series(groups_train).nunique()),
            "n_test_groups": int(pd.Series(groups[test_idx]).nunique()),
        })

    if np.isnan(outer_predictions).any():
        raise RuntimeError("Nested CV did not generate a prediction for every observation")
    counts = {name: sum(record["selected_model"] == name for record in fold_records) for name in models}
    return {
        "target": target,
        "group_column": group_column,
        "n_observations": int(len(frame)),
        "n_groups": int(pd.Series(groups).nunique()),
        "outer_splits": int(outer_splits),
        "inner_splits": int(inner_splits),
        "selected_model_counts": counts,
        "folds": fold_records,
        "metrics": _metrics(y, outer_predictions),
        "predictions": outer_predictions.tolist(),
        "residuals": (y - outer_predictions).tolist(),
        "interpretation": "Outer-fold metrics estimate the complete inner-CV model-selection procedure. They do not report the performance of a final model refitted on all observations.",
    }
