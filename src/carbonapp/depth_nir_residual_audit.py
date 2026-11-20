"""Residual diagnostics for the grouped depth-versus-NIR benchmark."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import validate_dataset
from .depth import DEPTH_PROFILE


def build_residual_audit(frame: pd.DataFrame, results_by_group: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return depth-stratified OOF residual metrics and paired fold RMSE deltas.

    Prediction arrays must preserve the original CSV row order. Positive delta
    means the scenario has higher (worse) RMSE than depth_only.
    """
    validate_dataset(frame)
    depth_rows: list[dict] = []
    fold_rows: list[dict] = []
    expected_rows = len(frame)

    for group_column, result in results_by_group.items():
        if result.get("group_column") != group_column:
            raise ValueError(f"Result key/group mismatch: {group_column}")
        if result.get("n_observations") != expected_rows:
            raise ValueError(f"Observation count mismatch for {group_column}")
        scenarios = result.get("scenarios", {})
        if "depth_only" not in scenarios:
            raise ValueError(f"Missing depth_only scenario for {group_column}")

        y = frame["TOC"].astype(float).to_numpy()
        depth_only = scenarios["depth_only"]
        depth_pred = np.asarray(depth_only.get("predictions"), dtype=float)
        if depth_pred.shape != (expected_rows,) or not np.isfinite(depth_pred).all():
            raise ValueError(f"Invalid depth_only predictions for {group_column}")

        for scenario, item in scenarios.items():
            pred = np.asarray(item.get("predictions"), dtype=float)
            if pred.shape != (expected_rows,) or not np.isfinite(pred).all():
                raise ValueError(f"Invalid predictions for {group_column}/{scenario}")
            residual = y - pred
            for interval in DEPTH_PROFILE:
                mask = frame["Profundidade"].astype(str).to_numpy() == interval.code
                if not mask.any():
                    continue
                errors = residual[mask]
                depth_rows.append({
                    "group_column": group_column,
                    "scenario": scenario,
                    "depth_code": interval.code,
                    "top_cm": interval.top_cm,
                    "bottom_cm": interval.bottom_cm,
                    "n_observations": int(mask.sum()),
                    "n_sampling_points": int(frame.loc[mask, "Amostra"].nunique()),
                    "mae": float(np.mean(np.abs(errors))),
                    "rmse": float(np.sqrt(np.mean(errors ** 2))),
                    "bias": float(np.mean(pred[mask] - y[mask])),
                })

            folds = item.get("folds", [])
            reference_folds = depth_only.get("folds", [])
            if len(folds) != len(reference_folds):
                raise ValueError(f"Fold count mismatch for {group_column}/{scenario}")
            for fold, reference in zip(folds, reference_folds):
                if fold.get("fold") != reference.get("fold"):
                    raise ValueError(f"Fold alignment mismatch for {group_column}/{scenario}")
                rmse = float(fold["outer_metrics"]["rmse"])
                reference_rmse = float(reference["outer_metrics"]["rmse"])
                fold_rows.append({
                    "group_column": group_column,
                    "scenario": scenario,
                    "fold": int(fold["fold"]),
                    "selected_model": fold.get("selected_model"),
                    "rmse": rmse,
                    "depth_only_rmse": reference_rmse,
                    "delta_rmse_vs_depth_only": rmse - reference_rmse,
                    "delta_rmse_percent": (
                        100.0 * (rmse - reference_rmse) / reference_rmse
                        if reference_rmse else np.nan
                    ),
                })

    return pd.DataFrame(depth_rows), pd.DataFrame(fold_rows)
