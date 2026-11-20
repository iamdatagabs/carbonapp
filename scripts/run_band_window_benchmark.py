"""Run nested grouped-CV comparisons of full NIR and the candidate wavelength window."""
import argparse
import json
from pathlib import Path
import pandas as pd
from carbonapp.band_window_benchmark import nested_band_window_benchmark
from carbonapp.data import load_dataset

def run(data_path, output_dir, seed=42, outer_splits=5, inner_splits=4,
        groups=("Amostra", "Sample Number")):
    frame = load_dataset(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for group in groups:
        result = nested_band_window_benchmark(frame, group_column=group,
            outer_splits=min(outer_splits, frame[group].nunique()),
            inner_splits=inner_splits, random_state=seed)
        safe = group.lower().replace(" ", "-")
        (output_dir / f"band-window-{safe}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        base = result["depth_mean_baseline"]["metrics"]
        rows.append({"group_column": group, "scenario": "depth_mean_baseline",
            **base, "n_groups": result["n_groups"], "n_bands": 0,
            "delta_rmse_vs_baseline": 0.0, "delta_mae_vs_baseline": 0.0,
            "selected_models": ""})
        for scenario, item in result["scenarios"].items():
            rows.append({"group_column": group, "scenario": scenario,
                **item["metrics"], "n_groups": result["n_groups"],
                "n_bands": result["n_full_spectral_bands"] if scenario == "nir_full_raw"
                    else result["n_window_bands"],
                "delta_rmse_vs_baseline": item["delta_vs_layer_baseline"]["rmse"],
                "delta_mae_vs_baseline": item["delta_vs_layer_baseline"]["mae"],
                "selected_models": json.dumps(item["selected_model_counts"])})
    summary = pd.DataFrame(rows)
    summary.to_csv(output_dir / "band-window-benchmark-summary.csv", index=False)
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/band-window-benchmark"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=4)
    parser.add_argument("--groups", nargs="+", default=["Amostra", "Sample Number"])
    args = parser.parse_args()
    print(run(args.data, args.output, args.seed, args.outer_splits,
              args.inner_splits, tuple(args.groups)).to_string(index=False))

if __name__ == "__main__":
    main()
