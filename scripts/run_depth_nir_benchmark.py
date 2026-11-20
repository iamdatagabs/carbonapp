"""Run depth-versus-NIR nested grouped-CV benchmarks."""
import argparse
import json
from pathlib import Path

import pandas as pd

from carbonapp.data import load_dataset
from carbonapp.depth_nir_benchmark import SCENARIOS, nested_depth_nir_benchmark


def run(data_path, output_dir, seed=42, outer_splits=5, inner_splits=4,
        groups=("Amostra", "Sample Number")):
    frame = load_dataset(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for group in groups:
        result = nested_depth_nir_benchmark(frame, group_column=group,
            outer_splits=min(outer_splits, frame[group].nunique()),
            inner_splits=inner_splits, random_state=seed)
        safe = group.lower().replace(" ", "-")
        (output_dir / f"depth-nir-{safe}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        base = result["fold_specific_mean_baseline"]["metrics"]
        for scenario, item in result["scenarios"].items():
            rows.append({"group_column": group, "scenario": scenario, **item["metrics"],
                "selected_models": json.dumps(item["selected_model_counts"]),
                "baseline_rmse": base["rmse"], "baseline_mae": base["mae"],
                "n_groups": result["n_groups"], "outer_splits": result["outer_splits"]})
        rows.append({"group_column": group, "scenario": "fold_specific_mean_baseline",
            **base, "selected_models": "", "baseline_rmse": base["rmse"],
            "baseline_mae": base["mae"], "n_groups": result["n_groups"],
            "outer_splits": result["outer_splits"]})
    summary = pd.DataFrame(rows)
    summary.to_csv(output_dir / "depth-nir-benchmark-summary.csv", index=False)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/depth-nir-benchmark"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=4)
    parser.add_argument("--groups", nargs="+", default=["Amostra", "Sample Number"])
    args = parser.parse_args()
    print(run(args.data, args.output, args.seed, args.outer_splits,
              args.inner_splits, tuple(args.groups)).to_string(index=False))


if __name__ == "__main__":
    main()
