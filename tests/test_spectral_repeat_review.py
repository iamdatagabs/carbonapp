from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "review_spectral_repeats.py"
SPEC = importlib.util.spec_from_file_location("review_spectral_repeats", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
build_repeat_review = MODULE.build_repeat_review


def test_repeat_review_writes_pair_group_and_visual_outputs(tmp_path):
    frame = pd.DataFrame({
        "Indice": [1, 2, 3, 4],
        "Amostra": [1, 1, 2, 2],
        "Profundidade": ["A", "A", "B", "B"],
        "Sample Number": ["01A", "01A", "02B", "02B"],
        "TOC": [12.0, 12.0, 8.0, 8.0],
        "N": [0.8, 0.8, 0.5, 0.5],
        "r1100": [0.10, 0.10, 0.20, 0.21],
        "r1102": [0.20, 0.20, 0.30, 0.29],
        "r1104": [0.30, 0.30, 0.40, 0.41],
        "r1106": [0.40, 0.40, 0.50, 0.49],
    })
    source = tmp_path / "tiny.csv"
    output = tmp_path / "qc"
    frame.to_csv(source, index=False)

    summary = build_repeat_review(source, output)

    assert summary["n_repeated_ids"] == 2
    assert summary["n_repeat_pairs"] == 2
    assert summary["n_exact_pairs"] == 1
    assert set(summary["outputs"]).issubset({p.name for p in output.iterdir()})
    assert (output / "spectral-qc-repeat-pair-detail.csv").exists()
    assert (output / "spectral-qc-repeat-group-review.csv").exists()
    assert (output / "spectral-qc-review-candidates.csv").exists()
    assert (output / "spectral-qc-repeat-pairs.svg").exists()
    assert (output / "spectral-qc-smoothness-review.svg").exists()
    assert (output / "spectral-qc-review.html").exists()
    saved = json.loads((output / "spectral-qc-review-summary.json").read_text())
    assert saved["n_exact_pairs"] == 1
