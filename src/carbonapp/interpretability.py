"""Group-aware interpretability for NIR regression models.

Importance scores describe predictive reliance, not chemical causality. Individual
wavelength scores can be diluted by strong spectral collinearity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from .data import spectral_columns, validate_dataset
from .model_comparison import SUPPORTED_MODELS, build_model_pipeline


def _validate(frame: pd.DataFrame, target: str, group_column: str, model_name: str) -> list[str]:
    validate_dataset(frame)
    if target not in ("TOC", "N"):
        raise ValueError("target must be TOC or N")
    if group_column not in frame:
        raise ValueError(f"Missing group column: {group_column}")
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_name}")
    return spectral_columns(frame)


def feature_selection_stability(
    frame: pd.DataFrame,
    target: str = "TOC",
    group_column: str = "Sample Number",
    n_splits: int = 5,
    k: int = 40,
) -> pd.DataFrame:
    """Measure how often each band is selected across grouped training folds."""
    bands = _validate(frame, target, group_column, "huber")
    groups = frame[group_column].to_numpy()
    if n_splits < 2 or pd.Series(groups).nunique() < n_splits:
        raise ValueError("Need at least n_splits unique groups and n_splits >= 2")
    if k < 1:
        raise ValueError("k must be >= 1")
    x = frame[bands].astype(float)
    y = frame[target].astype(float).to_numpy()
    counts = np.zeros(len(bands), dtype=int)
    cv = GroupKFold(n_splits=n_splits)
    for train_idx, _ in cv.split(x, y, groups):
        selector = build_model_pipeline("huber", min(k, len(bands))).named_steps["select"]
        selector.fit(x.iloc[train_idx], y[train_idx])
        counts += selector.get_support().astype(int)
    return pd.DataFrame({
        "band": bands,
        "wavelength_nm": [int(name[1:]) for name in bands],
        "selected_folds": counts,
        "selection_frequency": counts / n_splits,
        "n_splits": n_splits,
    }).sort_values(["selection_frequency", "wavelength_nm"], ascending=[False, True]).reset_index(drop=True)


def grouped_permutation_importance(
    frame: pd.DataFrame,
    target: str = "TOC",
    group_column: str = "Sample Number",
    model_name: str = "huber",
    test_size: float = 0.25,
    n_repeats: int = 20,
    k: int = 40,
    random_state: int = 42,
) -> dict:
    """Fit on training groups and permute wavelengths only on held-out groups."""
    bands = _validate(frame, target, group_column, model_name)
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")
    if n_repeats < 1:
        raise ValueError("n_repeats must be >= 1")
    groups = frame[group_column].to_numpy()
    if pd.Series(groups).nunique() < 4:
        raise ValueError("At least 4 unique groups are required")
    x = frame[bands].astype(float)
    y = frame[target].astype(float).to_numpy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(x, y, groups))
    estimator = build_model_pipeline(model_name, min(k, len(bands)), random_state)
    estimator.fit(x.iloc[train_idx], y[train_idx])
    result = permutation_importance(
        estimator, x.iloc[test_idx], y[test_idx], scoring="neg_root_mean_squared_error",
        n_repeats=n_repeats, random_state=random_state, n_jobs=1,
    )
    importance = pd.DataFrame({
        "band": bands,
        "wavelength_nm": [int(name[1:]) for name in bands],
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values("importance_mean", ascending=False).reset_index(drop=True)
    return {
        "target": target, "group_column": group_column, "model": model_name,
        "n_train_groups": int(pd.Series(groups[train_idx]).nunique()),
        "n_test_groups": int(pd.Series(groups[test_idx]).nunique()),
        "baseline_test_rmse": float(np.sqrt(np.mean((y[test_idx] - estimator.predict(x.iloc[test_idx])) ** 2))),
        "importance": importance,
        "interpretation": "Importance is the increase in held-out RMSE after permuting one band. Correlated neighboring wavelengths can share or mask importance; scores are not causal effects.",
    }


def grouped_shap_explanation(
    frame: pd.DataFrame,
    target: str = "TOC",
    group_column: str = "Sample Number",
    model_name: str = "huber",
    test_size: float = 0.25,
    background_size: int = 30,
    explain_size: int = 40,
    k: int = 40,
    random_state: int = 42,
) -> dict:
    """Compute model-agnostic SHAP values on held-out groups (optional dependency)."""
    bands = _validate(frame, target, group_column, model_name)
    try:
        import shap
    except ImportError as exc:
        raise ImportError("Install the optional dependency with: pip install -e '.[explainability]'") from exc
    groups = frame[group_column].to_numpy()
    if pd.Series(groups).nunique() < 4:
        raise ValueError("At least 4 unique groups are required")
    if min(background_size, explain_size) < 1 or not 0 < test_size < 1:
        raise ValueError("Sample sizes must be positive and test_size must be between 0 and 1")
    x = frame[bands].astype(float)
    y = frame[target].astype(float).to_numpy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(x, y, groups))
    estimator = build_model_pipeline(model_name, min(k, len(bands)), random_state)
    estimator.fit(x.iloc[train_idx], y[train_idx])
    background = x.iloc[train_idx].sample(n=min(background_size, len(train_idx)), random_state=random_state)
    explain = x.iloc[test_idx].sample(n=min(explain_size, len(test_idx)), random_state=random_state)
    explainer = shap.Explainer(estimator.predict, background)
    values = explainer(explain)
    shap_values = np.asarray(values.values)
    mean_abs = np.mean(np.abs(shap_values), axis=0)
    summary = pd.DataFrame({
        "band": bands,
        "wavelength_nm": [int(name[1:]) for name in bands],
        "mean_abs_shap": mean_abs,
        "mean_shap": np.mean(shap_values, axis=0),
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    return {
        "target": target, "group_column": group_column, "model": model_name,
        "n_train_groups": int(pd.Series(groups[train_idx]).nunique()),
        "n_test_groups": int(pd.Series(groups[test_idx]).nunique()),
        "base_value": float(np.asarray(values.base_values).mean()),
        "importance": summary,
        "interpretation": "SHAP values explain this fitted model's predictions relative to the sampled background. They are not causal effects or proof of molecular mechanisms.",
    }


def depth_stratified_importance(
    frame: pd.DataFrame,
    target: str = "TOC",
    depth_column: str = "Profundidade",
    group_column: str = "Sample Number",
    model_name: str = "huber",
    min_groups: int = 8,
    test_size: float = 0.25,
    n_repeats: int = 10,
    k: int = 40,
    random_state: int = 42,
) -> pd.DataFrame:
    """Run independent group-held-out permutation analyses within each layer."""
    _validate(frame, target, group_column, model_name)
    if depth_column not in frame:
        raise ValueError(f"Missing depth column: {depth_column}")
    outputs = []
    for depth_code, subset in frame.groupby(depth_column, sort=False):
        if subset[group_column].nunique() < min_groups:
            continue
        result = grouped_permutation_importance(
            subset, target=target, group_column=group_column, model_name=model_name,
            test_size=test_size, n_repeats=n_repeats, k=k, random_state=random_state,
        )
        table = result["importance"].copy()
        table["depth_code"] = depth_code
        table["n_train_groups"] = result["n_train_groups"]
        table["n_test_groups"] = result["n_test_groups"]
        outputs.append(table)
    if not outputs:
        raise ValueError("No depth layer has enough independent groups for the requested analysis")
    return pd.concat(outputs, ignore_index=True)
