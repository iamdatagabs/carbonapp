"""Run nested grouped-CV comparisons of NIR preprocessing methods."""
import argparse
import json
from pathlib import Path
import pandas as pd
from carbonapp.data import load_dataset
from carbonapp.preprocessing_comparison import PREPROCESSING_METHODS, MODEL_NAMES, nested_preprocessing_comparison

def run(data_path, output_dir, seed=42, outer_splits=5, inner_splits=4,
        groups=("Sample Number", "Amostra")):
    frame = load_dataset(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for group in groups:
        n_groups = int(frame[group].nunique())
        outer = min(outer_splits, n_groups)
        result = nested_preprocessing_comparison(frame, target="TOC", group_column=group,
            outer_splits=outer, inner_splits=inner_splits, preprocessing_methods=PREPROCESSING_METHODS,
            models=MODEL_NAMES, random_state=seed)
        safe = group.lower().replace(" ", "-")
        (output_dir / f"preprocessing-{safe}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        base = result["fold_specific_mean_baseline"]["metrics"]
        for method, item in result["preprocessing"].items():
            rows.append({"group_column": group, "preprocessing": method, **item["metrics"],
                "selected_models": json.dumps(item["selected_model_counts"]),
                "baseline_rmse": base["rmse"], "baseline_mae": base["mae"],
                "outer_splits": outer, "n_groups": n_groups})
        rows.append({"group_column": group, "preprocessing": "fold_specific_mean_baseline",
            **base, "selected_models": "", "baseline_rmse": base["rmse"],
            "baseline_mae": base["mae"], "outer_splits": outer, "n_groups": n_groups})
    table = pd.DataFrame(rows)
    table.to_csv(output_dir / "preprocessing-comparison-summary.csv", index=False)
    return table

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/preprocessing-comparison"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=4)
    parser.add_argument("--groups", nargs="+", default=["Sample Number", "Amostra"])
    args = parser.parse_args()
    print(run(args.data, args.output, args.seed, args.outer_splits, args.inner_splits,
              tuple(args.groups)).to_string(index=False))

if __name__ == "__main__":
    main()
