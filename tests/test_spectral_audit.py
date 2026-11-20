from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_spectral_data.py"
SPEC = importlib.util.spec_from_file_location("audit_spectral_data", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
audit_spectra = MODULE.audit_spectra


def test_audit_spectra_writes_descriptive_outputs(tmp_path):
    frame = pd.DataFrame({
        "Indice": [1, 2, 3],
        "Amostra": [1, 1, 2],
        "Profundidade": ["A", "A", "B"],
        "Sample Number": [101, 101, 202],
        "TOC": [12.0, 12.0, 8.0],
        "N": [0.8, 0.8, 0.5],
        "r1100": [0.10, 0.11, 0.20],
        "r1102": [0.20, 0.21, 0.30],
        "r1104": [0.30, 0.31, 0.40],
    })
    source = tmp_path / "tiny.csv"
    output = tmp_path / "qc"
    frame.to_csv(source, index=False)

    summary = audit_spectra(source, output)

    assert summary["n_rows"] == 3
    assert summary["n_bands"] == 3
    assert summary["repeat_pairs_compared"] == 1
    assert summary["constant_bands"] == 0
    assert (output / "spectral-qc-by-band.csv").exists()
    assert (output / "spectral-qc-by-spectrum.csv").exists()
    assert (output / "spectral-qc-repeat-similarity.csv").exists()
    assert (output / "spectral-qc-by-depth.csv").exists()
    saved = json.loads((output / "spectral-qc-summary.json").read_text(encoding="utf-8"))
    assert saved["dataset_sha256"] == summary["dataset_sha256"]
