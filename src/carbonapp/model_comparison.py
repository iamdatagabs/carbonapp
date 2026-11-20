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
