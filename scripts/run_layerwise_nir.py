"""Run nested grouped-CV NIR benchmarks independently by depth layer."""

import argparse
import json
from pathlib import Path

import pandas as pd

from carbonapp.data import load_dataset
from carbonapp.layerwise_nir import benchmark_nir_by_depth


def run(data_path, output_dir, seed=42, outer_splits=5, inner_splits=4):
    frame = load_dataset(data_path)
    result = benchmark_nir_by_depth(
        frame, outer_splits=outer_splits, inner_splits=inner_splits,
        random_state=seed,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "layerwise-nir-results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    rows = []
    for layer, item in result["layers"].items():
        baseline = item["mean_baseline"]
        rows.append({
            "depth_layer": layer, "scenario": "mean_baseline",
            "n_points": item["n_points"], **baseline,
        })
        for prep, scenario in item["scenarios"].items():
            rows.append({
                "depth_layer": layer, "scenario": f"mean_plus_nir_{prep}",
                "n_points": item["n_points"], **scenario["metrics"],
                "baseline_rmse": baseline["rmse"],
                "baseline_mae": baseline["mae"],
                "selected_models": json.dumps(scenario["selected_model_counts"]),
            })
    summary = pd.DataFrame(rows)
    summary.to_csv(output_dir / "layerwise-nir-summary.csv", index=False)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/layerwise-nir"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=4)
    args = parser.parse_args()
    print(run(args.data, args.output, args.seed,
              args.outer_splits, args.inner_splits).to_string(index=False))


if __name__ == "__main__":
    main()
