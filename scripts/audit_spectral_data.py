"""Audit raw NIR spectra before choosing any preprocessing strategy.

This script is descriptive only: it never removes rows/bands or fits a target model.
It writes machine-readable summaries to support review of range, scatter,
spectral shape, repeated Sample Number consistency, and depth-related shifts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from carbonapp.data import load_dataset, spectral_columns


def _safe_float(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def audit_spectra(data_path: Path, output_dir: Path) -> dict:
    frame = load_dataset(data_path)
    bands = spectral_columns(frame)
    matrix = frame[bands].astype(float)
    values = matrix.to_numpy(dtype=float)
    wavelengths = np.array([int(name[1:]) for name in bands], dtype=int)

    band_rows = []
    for index, band in enumerate(bands):
        x = values[:, index]
        mean = float(np.mean(x))
        sd = float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
        q01, q25, q50, q75, q99 = np.quantile(x, [0.01, 0.25, 0.5, 0.75, 0.99])
        band_rows.append({
            "band": band, "wavelength_nm": int(wavelengths[index]),
            "mean": mean, "sd": sd, "cv": _safe_float(sd / abs(mean)) if abs(mean) > 1e-12 else None,
            "min": float(np.min(x)), "q01": float(q01), "q25": float(q25),
            "median": float(q50), "q75": float(q75), "q99": float(q99),
            "max": float(np.max(x)), "negative_fraction": float(np.mean(x < 0)),
            "zero_fraction": float(np.mean(np.isclose(x, 0.0))),
            "n_unique": int(np.unique(x).size),
        })
    by_band = pd.DataFrame(band_rows)

    # Per-spectrum diagnostics: scale, offset, smoothness and shape.
    row_mean = values.mean(axis=1)
    row_sd = values.std(axis=1, ddof=1)
    row_median = np.median(values, axis=1)
    row_iqr = np.quantile(values, 0.75, axis=1) - np.quantile(values, 0.25, axis=1)
    first_diff = np.diff(values, axis=1)
    row_records = pd.DataFrame({
        "row_index": np.arange(len(frame)),
        "Amostra": frame["Amostra"].to_numpy(),
        "Profundidade": frame["Profundidade"].to_numpy(),
        "Sample Number": frame["Sample Number"].to_numpy(),
        "TOC": frame["TOC"].to_numpy(),
        "N": frame["N"].to_numpy(),
        "spectral_mean": row_mean,
        "spectral_sd": row_sd,
        "spectral_median": row_median,
        "spectral_iqr": row_iqr,
        "spectral_min": values.min(axis=1),
        "spectral_max": values.max(axis=1),
        "negative_band_fraction": (values < 0).mean(axis=1),
        "adjacent_difference_rms": np.sqrt(np.mean(first_diff ** 2, axis=1)),
        "adjacent_difference_abs_median": np.median(np.abs(first_diff), axis=1),
        "spectral_range": values.max(axis=1) - values.min(axis=1),
    })

    # Within-ID repeat similarity; no assumption that repeats are technical scans.
    repeat_rows = []
    for sample_id, positions in frame.groupby("Sample Number", sort=False).indices.items():
        positions = np.asarray(positions, dtype=int)
        if len(positions) < 2:
            continue
        subset = values[positions]
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                a, b = subset[i], subset[j]
                corr = float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else np.nan
                repeat_rows.append({
                    "Sample Number": str(sample_id),
                    "row_i": int(positions[i]), "row_j": int(positions[j]),
                    "spectral_pearson_r": _safe_float(corr),
                    "spectral_rmse": float(np.sqrt(np.mean((a - b) ** 2))),
                    "mean_absolute_difference": float(np.mean(np.abs(a - b))),
                })
    repeat_similarity = pd.DataFrame(repeat_rows, columns=[
        "Sample Number", "row_i", "row_j", "spectral_pearson_r",
        "spectral_rmse", "mean_absolute_difference",
    ])

    # Depth summaries describe spectral levels, not chemistry or causal effects.
    by_depth = row_records.groupby("Profundidade", observed=True).agg(
        n_rows=("row_index", "size"),
        n_points=("Amostra", "nunique"),
        n_sample_numbers=("Sample Number", "nunique"),
        spectral_mean_mean=("spectral_mean", "mean"),
        spectral_mean_sd=("spectral_mean", "std"),
        spectral_sd_mean=("spectral_sd", "mean"),
        spectral_iqr_mean=("spectral_iqr", "mean"),
        adjacent_difference_rms_mean=("adjacent_difference_rms", "mean"),
        negative_band_fraction_mean=("negative_band_fraction", "mean"),
    ).reset_index()

    output_dir.mkdir(parents=True, exist_ok=True)
    by_band.to_csv(output_dir / "spectral-qc-by-band.csv", index=False)
    row_records.to_csv(output_dir / "spectral-qc-by-spectrum.csv", index=False)
    repeat_similarity.to_csv(output_dir / "spectral-qc-repeat-similarity.csv", index=False)
    by_depth.to_csv(output_dir / "spectral-qc-by-depth.csv", index=False)

    summary = {
        "dataset_path": str(data_path),
        "dataset_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "n_rows": int(len(frame)),
        "n_bands": int(len(bands)),
        "wavelength_min_nm": int(wavelengths.min()),
        "wavelength_max_nm": int(wavelengths.max()),
        "wavelength_step_nm": int(np.median(np.diff(wavelengths))) if len(wavelengths) > 1 else None,
        "non_finite_spectral_values": int((~np.isfinite(values)).sum()),
        "negative_spectral_values": int((values < 0).sum()),
        "zero_spectral_values": int(np.isclose(values, 0.0).sum()),
        "constant_bands": int((by_band["n_unique"] == 1).sum()),
        "repeated_sample_number_ids": int((frame.groupby("Sample Number").size() > 1).sum()),
        "repeat_pairs_compared": int(len(repeat_similarity)),
        "repeat_pair_correlation_median": _safe_float(repeat_similarity["spectral_pearson_r"].median()) if len(repeat_similarity) else None,
        "repeat_pair_rmse_median": _safe_float(repeat_similarity["spectral_rmse"].median()) if len(repeat_similarity) else None,
        "warning": "Descriptive diagnostics only. Do not automatically discard spectra or select preprocessing based on these summaries. Confirm instrument protocol, replicate semantics, and reference method first.",
        "outputs": [
            "spectral-qc-by-band.csv", "spectral-qc-by-spectrum.csv",
            "spectral-qc-repeat-similarity.csv", "spectral-qc-by-depth.csv",
        ],
    }
    (output_dir / "spectral-qc-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/spectral-qc"))
    args = parser.parse_args()
    print(json.dumps(audit_spectra(args.data, args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
