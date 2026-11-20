"""Create a non-destructive review report for repeated and unusual NIR spectra.

The report ranks records for human inspection; it never removes observations or
chooses preprocessing. SVG charts are generated with the Python standard library.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from carbonapp.data import load_dataset, spectral_columns


def _corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _scale_points(values: np.ndarray, x0: float, y0: float,
                  width: float, height: float, ymin: float, ymax: float) -> str:
    if ymax <= ymin:
        ymax = ymin + 1e-9
    n = len(values)
    coords = []
    for i, value in enumerate(values):
        x = x0 + (i / max(n - 1, 1)) * width
        y = y0 + height - ((float(value) - ymin) / (ymax - ymin)) * height
        coords.append(f"{x:.2f},{y:.2f}")
    return " ".join(coords)


def _svg_panel(title: str, series: list[tuple[str, np.ndarray, str]],
               x_label: str, y_label: str, width: int = 560,
               height: int = 230) -> str:
    left, top, right, bottom = 58, 34, 18, 42
    plot_w, plot_h = width - left - right, height - top - bottom
    all_values = np.concatenate([s[1] for s in series])
    ymin, ymax = float(np.min(all_values)), float(np.max(all_values))
    pad = max((ymax - ymin) * 0.08, 1e-7)
    ymin, ymax = ymin - pad, ymax + pad
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{html.escape(title)}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="{left}" y="20" font-size="13" font-weight="bold">{html.escape(title)}</text>',
        f'<path d="M{left} {top} V{top+plot_h} H{left+plot_w}" fill="none" stroke="#555"/>',
        f'<text x="8" y="{top+plot_h/2}" font-size="10" transform="rotate(-90 8 {top+plot_h/2})">{html.escape(y_label)}</text>',
        f'<text x="{left+plot_w/2}" y="{height-7}" font-size="10" text-anchor="middle">{html.escape(x_label)}</text>',
        f'<text x="{left-7}" y="{top+4}" font-size="9" text-anchor="end">{ymax:.4f}</text>',
        f'<text x="{left-7}" y="{top+plot_h}" font-size="9" text-anchor="end">{ymin:.4f}</text>',
    ]
    colors = ["#6b4f3a", "#287c65", "#a44a3f", "#416b9b", "#9270a8", "#b18b31"]
    for idx, (label, values, color) in enumerate(series):
        points = _scale_points(values, left, top, plot_w, plot_h, ymin, ymax)
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color or colors[idx % len(colors)]}" stroke-width="1.7"/>')
        lx = left + 8 + (idx % 3) * 175
        ly = height - 24 + (idx // 3) * 11
        parts.append(f'<text x="{lx}" y="{ly}" font-size="9" fill="{color or colors[idx % len(colors)]}">{html.escape(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def build_repeat_review(data_path: Path, output_dir: Path) -> dict:
    frame = load_dataset(data_path)
    bands = spectral_columns(frame)
    wavelengths = np.array([int(b[1:]) for b in bands], dtype=int)
    matrix = frame[bands].to_numpy(dtype=float)

    pair_rows: list[dict] = []
    group_rows: list[dict] = []
    grouped_positions = frame.groupby("Sample Number", sort=False).indices

    for sample_id, positions in grouped_positions.items():
        positions = np.asarray(positions, dtype=int)
        if len(positions) < 2:
            continue
        subset = matrix[positions]
        group_pair_rows = []
        for i, j in combinations(range(len(positions)), 2):
            a, b = subset[i], subset[j]
            corr = _corr(a, b)
            rmse = float(np.sqrt(np.mean((a - b) ** 2)))
            mean_a, mean_b = float(a.mean()), float(b.mean())
            record = {
                "Sample Number": str(sample_id),
                "row_i": int(positions[i]), "row_j": int(positions[j]),
                "spectral_pearson_r": corr,
                "spectral_rmse": rmse,
                "mean_absolute_difference": float(np.mean(np.abs(a - b))),
                "mean_i": mean_a, "mean_j": mean_b,
                "mean_offset_j_minus_i": mean_b - mean_a,
                "max_absolute_band_difference": float(np.max(np.abs(a - b))),
                "exact_match": bool(np.array_equal(a, b)),
            }
            pair_rows.append(record)
            group_pair_rows.append(record)
        correlations = [x["spectral_pearson_r"] for x in group_pair_rows if x["spectral_pearson_r"] is not None]
        rmses = [x["spectral_rmse"] for x in group_pair_rows]
        means = subset.mean(axis=1)
        group_rows.append({
            "Sample Number": str(sample_id),
            "n_records": int(len(positions)),
            "n_pairs": int(len(group_pair_rows)),
            "n_unique_spectra": int(np.unique(subset, axis=0).shape[0]),
            "n_exact_pairs": int(sum(x["exact_match"] for x in group_pair_rows)),
            "min_pair_correlation": min(correlations) if correlations else None,
            "median_pair_correlation": float(np.median(correlations)) if correlations else None,
            "max_pair_rmse": max(rmses),
            "mean_level_range": float(np.ptp(means)),
            "review_priority": "high" if (min(correlations, default=1) < 0.90 or max(rmses) > 0.002) else "routine",
        })

    pairs = pd.DataFrame(pair_rows)
    groups = pd.DataFrame(group_rows).sort_values(
        ["review_priority", "max_pair_rmse"], ascending=[True, False]
    )
    spectrum = pd.DataFrame({
        "row_index": np.arange(len(frame)),
        "Amostra": frame["Amostra"].to_numpy(),
        "Profundidade": frame["Profundidade"].to_numpy(),
        "Sample Number": frame["Sample Number"].astype(str).to_numpy(),
        "TOC": frame["TOC"].to_numpy(),
        "spectral_mean": matrix.mean(axis=1),
        "adjacent_difference_rms": np.sqrt(np.mean(np.diff(matrix, axis=1) ** 2, axis=1)),
    })
    med = float(spectrum["adjacent_difference_rms"].median())
    mad = float(np.median(np.abs(spectrum["adjacent_difference_rms"] - med)))
    threshold = med + 6 * 1.4826 * mad if mad > 0 else med * 10
    spectrum["smoothness_review_candidate"] = spectrum["adjacent_difference_rms"] > threshold
    spectrum["smoothness_robust_threshold"] = threshold

    output_dir.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(output_dir / "spectral-qc-repeat-pair-detail.csv", index=False)
    groups.to_csv(output_dir / "spectral-qc-repeat-group-review.csv", index=False)
    spectrum.to_csv(output_dir / "spectral-qc-review-candidates.csv", index=False)

    # Overlay every scan for repeat groups with at least two distinct spectra.
    panels = []
    for _, group in groups[groups["n_unique_spectra"] > 1].iterrows():
        positions = np.flatnonzero(frame["Sample Number"].astype(str).to_numpy() == group["Sample Number"])
        series = [
            (f"row {pos}", matrix[pos], "")
            for pos in positions
        ]
        panels.append(_svg_panel(
            f'Sample Number {group["Sample Number"]}: repeated spectra',
            series, "Wavelength (nm; bands ordered at 2 nm)", "Reflectance"
        ))
    if not panels:
        panels.append("<p>No non-identical repeated spectra found.</p>")
    repeat_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 '
        f'{((len(panels)+1)//2)*250}" width="100%">'
        + "".join(
            f'<g transform="translate({(i%2)*580},{(i//2)*250})">{panel}</g>'
            for i, panel in enumerate(panels)
        )
        + "</svg>"
    )
    (output_dir / "spectral-qc-repeat-pairs.svg").write_text(repeat_svg, encoding="utf-8")

    # Show the most abrupt spectrum against the dataset median profile.
    worst_pos = int(np.argmax(spectrum["adjacent_difference_rms"].to_numpy()))
    median_profile = np.median(matrix, axis=0)
    outlier_series = [
        (f'row {worst_pos} ({frame.iloc[worst_pos]["Sample Number"]})', matrix[worst_pos], "#a44a3f"),
        ("dataset median profile", median_profile, "#287c65"),
    ]
    outlier_svg = _svg_panel(
        "Highest adjacent-band variation (review candidate)",
        outlier_series, "Wavelength (nm; 1100–1648)", "Reflectance", 1000, 360
    )
    (output_dir / "spectral-qc-smoothness-review.svg").write_text(outlier_svg, encoding="utf-8")

    review_html = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>NIR repeat review</title>
<style>body{{font:15px system-ui;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#292929}}
section{{margin:2rem 0}}svg{{max-width:100%;height:auto}}table{{border-collapse:collapse}}
th,td{{padding:.4rem .6rem;border-bottom:1px solid #ddd;text-align:left}}</style>
<h1>Raw NIR repeat and smoothness review</h1>
<p>Diagnostic report only. No spectra were removed and no preprocessing was selected.</p>
<section><h2>Repeated Sample Number profiles</h2>{repeat_svg}</section>
<section><h2>Highest smoothness anomaly candidate</h2>{outlier_svg}</section>
<section><h2>Repeat-group summary</h2>{groups.to_html(index=False, border=0)}</section>
</html>"""
    (output_dir / "spectral-qc-review.html").write_text(review_html, encoding="utf-8")

    high_priority = groups[groups["review_priority"] == "high"]
    summary = {
        "n_repeated_ids": int(len(groups)),
        "n_repeat_pairs": int(len(pairs)),
        "n_exact_pairs": int(pairs["exact_match"].sum()) if len(pairs) else 0,
        "n_repeat_groups_high_priority": int(len(high_priority)),
        "high_priority_sample_numbers": high_priority["Sample Number"].tolist(),
        "n_smoothness_review_candidates": int(spectrum["smoothness_review_candidate"].sum()),
        "smoothness_robust_threshold": threshold,
        "highest_smoothness_candidate": {
            "row_index": worst_pos,
            "sample_number": str(frame.iloc[worst_pos]["Sample Number"]),
            "point": str(frame.iloc[worst_pos]["Amostra"]),
            "depth": str(frame.iloc[worst_pos]["Profundidade"]),
            "adjacent_difference_rms": float(spectrum.iloc[worst_pos]["adjacent_difference_rms"]),
        },
        "warning": "Review priorities are triage aids, not exclusion criteria. Confirm sample preparation, instrument protocol, scan identity, and reference provenance before any data removal or preprocessing decision.",
        "outputs": [
            "spectral-qc-repeat-pair-detail.csv",
            "spectral-qc-repeat-group-review.csv",
            "spectral-qc-review-candidates.csv",
            "spectral-qc-repeat-pairs.svg",
            "spectral-qc-smoothness-review.svg",
            "spectral-qc-review.html",
        ],
    }
    (output_dir / "spectral-qc-review-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/[quad]base_nirs_refletancia.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/spectral-qc"))
    args = parser.parse_args()
    print(json.dumps(build_repeat_review(args.data, args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
