"""Create depth-stratified and paired-fold residual diagnostics."""

import argparse
import json
from pathlib import Path

from carbonapp.data import load_dataset
from carbonapp.depth_nir_residual_audit import build_residual_audit


def run(data_path: Path, results_dir: Path, output_dir: Path):
    frame = load_dataset(data_path)
    results = {}
    for group, filename in (
        ("Amostra", "depth-nir-amostra.json"),
        ("Sample Number", "depth-nir-sample-number.json"),
    ):
        with (results_dir / filename).open(encoding="utf-8") as handle:
            results[group] = json.load(handle)
    by_depth, by_fold = build_residual_audit(frame, results)
    output_dir.mkdir(parents=True, exist_ok=True)
    by_depth.to_csv(output_dir / "depth-nir-residuals-by-depth.csv", index=False)
    by_fold.to_csv(output_dir / "depth-nir-fold-rmse-deltas.csv", index=False)
    summary = {
        "n_observations": len(frame),
        "groupings": list(results),
        "interpretation": (
            "Residual metrics are descriptive diagnostics of the existing out-of-fold "
            "predictions. Positive fold RMSE delta means worse than depth_only. "
            "They do not establish causal or chemical mechanisms."
        ),
    }
    (output_dir / "depth-nir-residual-audit.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return by_depth, by_fold


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--results", type=Path, default=Path("reports/depth-nir-benchmark"))
    parser.add_argument("--output", type=Path, default=Path("reports/depth-nir-residual-audit"))
    args = parser.parse_args()
    by_depth, by_fold = run(args.data, args.results, args.output)
    print("Residuals by depth:")
    print(by_depth.to_string(index=False))
    print("\nPaired fold RMSE deltas:")
    print(by_fold.to_string(index=False))


if __name__ == "__main__":
    main()
