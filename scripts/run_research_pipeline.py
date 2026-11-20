"""Execute the end-to-end TOC research workflow and persist reproducible artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
import joblib

from carbonapp.data import load_dataset, spectral_columns
from carbonapp.interpretability import (
    depth_stratified_importance,
    feature_selection_stability,
    grouped_permutation_importance,
)
from carbonapp.model_comparison import (
    SUPPORTED_MODELS,
    build_model_pipeline,
    nested_grouped_model_selection,
)
from carbonapp.profile import build_profile_3d_payload, build_profile_summary
from carbonapp.tinyml import (
    benchmark_onnx_model,
    compare_onnx_models,
    export_linear_pipeline_onnx,
    quantize_onnx_dynamic,
)
from carbonapp.uncertainty import grouped_split_conformal


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if pd.isna(value):
        return None
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")


def _write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")


def run(data_path: Path, output_dir: Path, seed: int = 42, n_splits: int = 5):
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir = output_dir / "models"
    model_dir.mkdir(exist_ok=True)
    data_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    frame = load_dataset(data_path)
    bands = spectral_columns(frame)
    manifest = {
        "dataset_path": str(data_path),
        "dataset_sha256": data_hash,
        "n_rows": int(len(frame)),
        "n_spectral_bands": len(bands),
        "targets": ["TOC"],
        "seed": seed,
        "grouping": {
            "reference_group": "Sample Number",
            "sampling_point_group": "Amostra",
        },
        "warning": "N remains exploratory until its units and laboratory reference method are confirmed.",
    }

    # Nested grouped CV estimates the complete model-selection procedure.
    candidate_models = ("huber", "extra_trees", "elastic_net", "bayesian_ridge")
    nested_reference = nested_grouped_model_selection(
        frame, target="TOC", group_column="Sample Number",
        outer_splits=n_splits, inner_splits=min(4, n_splits),
        models=candidate_models, random_state=seed,
    )
    nested_points = nested_grouped_model_selection(
        frame, target="TOC", group_column="Amostra",
        outer_splits=min(n_splits, int(frame["Amostra"].nunique())),
        inner_splits=min(4, int(frame["Amostra"].nunique()) - 1),
        models=candidate_models, random_state=seed,
    )
    _write_json(output_dir / "nested-cv-sample-number.json", nested_reference)
    _write_json(output_dir / "nested-cv-sampling-point.json", nested_points)

    # Explanations are calculated using held-out reference groups.
    stability = feature_selection_stability(frame, target="TOC", group_column="Sample Number", n_splits=n_splits)
    permutation = grouped_permutation_importance(frame, target="TOC", group_column="Sample Number", random_state=seed)
    by_depth = depth_stratified_importance(frame, target="TOC", group_column="Sample Number", random_state=seed)
    stability.to_csv(output_dir / "feature-selection-stability.csv", index=False)
    permutation["importance"].to_csv(output_dir / "permutation-importance.csv", index=False)
    by_depth.to_csv(output_dir / "permutation-importance-by-depth.csv", index=False)

    conformal_reference = grouped_split_conformal(
        frame, target="TOC", group_column="Sample Number", random_state=seed,
    )
    conformal_points = grouped_split_conformal(
        frame, target="TOC", group_column="Amostra", random_state=seed,
    )
    _write_json(output_dir / "conformal-sample-number.json", conformal_reference)
    _write_json(output_dir / "conformal-sampling-point.json", conformal_points)

    # Profile tables use unique Sample Number references, then equal-weight points.
    build_profile_summary(frame, target="TOC").to_csv(output_dir / "profile-summary-toc.csv", index=False)
    build_profile_summary(frame, target="N").to_csv(output_dir / "profile-summary-n-exploratory.csv", index=False)
    _write_json(output_dir / "profile-3d-toc.json", build_profile_3d_payload(frame, target="TOC"))

    # Fit a deployable model on training groups; never use the held-out groups for fitting.
    groups = frame["Sample Number"].to_numpy()
    x, y = frame[bands].astype(float), frame["TOC"].astype(float).to_numpy()
    train_idx, test_idx = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed).split(x, y, groups))
    selected_model = max(nested_reference["selected_model_counts"], key=nested_reference["selected_model_counts"].get)
    estimator = build_model_pipeline(selected_model, k=min(40, len(bands)), random_state=seed)
    estimator.fit(x.iloc[train_idx], y[train_idx])
    joblib.dump(estimator, model_dir / "toc-selected-model.joblib")
    float_path, int8_path = model_dir / "toc-model.onnx", model_dir / "toc-model-int8.onnx"
    export_info = export_linear_pipeline_onnx(estimator, bands, float_path)
    quantization_info = quantize_onnx_dynamic(float_path, int8_path)
    drift = compare_onnx_models(float_path, int8_path, x.iloc[test_idx])
    float_metrics = {
        "mae": float(mean_absolute_error(y[test_idx], drift["reference_predictions"])),
        "rmse": float(np.sqrt(mean_squared_error(y[test_idx], drift["reference_predictions"]))),
    }
    int8_metrics = {
        "mae": float(mean_absolute_error(y[test_idx], drift["candidate_predictions"])),
        "rmse": float(np.sqrt(mean_squared_error(y[test_idx], drift["candidate_predictions"]))),
    }
    benchmark = {
        "float": benchmark_onnx_model(float_path, x.iloc[test_idx].to_numpy(), repeats=100, warmup=10),
        "int8": benchmark_onnx_model(int8_path, x.iloc[test_idx].to_numpy(), repeats=100, warmup=10),
    }
    _write_json(output_dir / "tinyml-comparison.json", {
        "selected_model": selected_model,
        "n_train_groups": int(pd.Series(groups[train_idx]).nunique()),
        "n_test_groups": int(pd.Series(groups[test_idx]).nunique()),
        "float_task_metrics": float_metrics,
        "int8_task_metrics": int8_metrics,
        "prediction_drift": drift,
        "export": export_info,
        "quantization": quantization_info,
        "benchmark": benchmark,
        "warning": "Host CPU measurements are not embedded-device RAM, flash, latency or energy measurements.",
    })

    manifest["selected_linear_model_for_export"] = selected_model
    manifest["artifacts"] = sorted(path.name for path in output_dir.iterdir())
    _write_json(output_dir / "run-manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/latest-run"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--splits", type=int, default=5)
    args = parser.parse_args()
    result = run(args.data, args.output, seed=args.seed, n_splits=args.splits)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
