"""Nested grouped-CV comparison of NIR preprocessing strategies."""
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
from .preprocessing import build_preprocessor

PREPROCESSING_METHODS = ("raw", "snv", "msc", "savgol_smooth", "savgol_first_derivative")
MODEL_NAMES = ("bayesian_ridge", "elastic_net", "huber", "extra_trees")

def _metrics(y, pred):
    return {"r2": float(r2_score(y, pred)), "mae": float(mean_absolute_error(y, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, pred))),
            "bias": float(np.mean(np.asarray(pred)-np.asarray(y)))}

def _pipeline(preprocessing, model, k, seed):
    steps = [("preprocess", build_preprocessor(preprocessing)),
             ("select", SelectKBest(f_regression, k=k))]
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

def nested_preprocessing_comparison(frame, target="TOC", group_column="Sample Number",
        outer_splits=5, inner_splits=4, k=40,
        preprocessing_methods=PREPROCESSING_METHODS, models=MODEL_NAMES, random_state=42):
    """Evaluate each transform/model-selection procedure with nested GroupKFold."""
    validate_dataset(frame)
    if target not in ("TOC", "N") or group_column not in frame:
        raise ValueError("Invalid target or missing grouping column")
    if outer_splits < 2 or inner_splits < 2 or not models or not preprocessing_methods:
        raise ValueError("At least two folds, models and preprocessing methods are required")
    bad_p = sorted(set(preprocessing_methods)-set(PREPROCESSING_METHODS))
    bad_m = sorted(set(models)-set(MODEL_NAMES))
    if bad_p or bad_m:
        raise ValueError(f"Unsupported preprocessing={bad_p}, models={bad_m}")
    bands = spectral_columns(frame)
    x, y = frame[bands].astype(float), frame[target].astype(float).to_numpy()
    groups = frame[group_column].to_numpy()
    if pd.Series(groups).nunique() < outer_splits:
        raise ValueError("Number of unique groups must be >= outer_splits")
    preds = {p: np.full(len(frame), np.nan) for p in preprocessing_methods}
    baseline = np.full(len(frame), np.nan)
    folds = {p: [] for p in preprocessing_methods}
    for fold, (tr, te) in enumerate(GroupKFold(n_splits=outer_splits).split(x, y, groups), 1):
        xtr, xte, ytr, yte = x.iloc[tr], x.iloc[te], y[tr], y[te]
        gtr = groups[tr]
        if pd.Series(gtr).nunique() < inner_splits:
            raise ValueError("Each outer training partition must contain >= inner_splits groups")
        inner = GroupKFold(n_splits=inner_splits)
        baseline[te] = ytr.mean()
        for prep in preprocessing_methods:
            scores = {}
            for model in models:
                pred = cross_val_predict(_pipeline(prep, model, min(k, len(bands)), random_state),
                    xtr, ytr, groups=gtr, cv=inner, n_jobs=None)
                scores[model] = float(np.sqrt(mean_squared_error(ytr, pred)))
            selected = min(scores, key=scores.get)
            estimator = _pipeline(prep, selected, min(k, len(bands)), random_state)
            estimator.fit(xtr, ytr)
            p = estimator.predict(xte)
            preds[prep][te] = p
            folds[prep].append({"fold": fold, "selected_model": selected, "inner_rmse": scores,
                "outer_metrics": _metrics(yte, p),
                "n_train_groups": int(pd.Series(gtr).nunique()),
                "n_test_groups": int(pd.Series(groups[te]).nunique())})
    if np.isnan(baseline).any() or any(np.isnan(v).any() for v in preds.values()):
        raise RuntimeError("Nested grouped CV did not predict every observation")
    result = {}
    for prep in preprocessing_methods:
        result[prep] = {"metrics": _metrics(y, preds[prep]), "folds": folds[prep],
            "selected_model_counts": {m: sum(f["selected_model"] == m for f in folds[prep]) for m in models},
            "predictions": preds[prep].tolist(), "residuals": (y-preds[prep]).tolist()}
    baseline_metrics = _metrics(y, baseline)
    ranking = sorted(preprocessing_methods, key=lambda p: (result[p]["metrics"]["rmse"], result[p]["metrics"]["mae"]))
    return {"target": target, "group_column": group_column, "n_observations": len(frame),
        "n_groups": int(pd.Series(groups).nunique()), "outer_splits": outer_splits,
        "inner_splits": inner_splits, "n_spectral_bands": len(bands), "selected_features_k": min(k, len(bands)),
        "preprocessing": result, "fold_specific_mean_baseline": {
            "metrics": baseline_metrics, "predictions": baseline.tolist()},
        "ranking_by_outer_rmse": ranking,
        "interpretation": "Outer metrics estimate each preprocessing-specific inner model-selection procedure. "
        "Ranking is uncertain with few independent groups; external validation remains necessary."}
