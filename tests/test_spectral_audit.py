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
    frame = pd.DataFrame([
        {"Indice": 0, "Amostra": 1, "Profundidade": "A", "Sample Number": "S1", "TOC": 8.0, "N": 0.5, "r1100": 0.10, "r1102": 0.12, "r1104": 0.15},
        {"Indice": 1, "Amostra": 1, "Profundidade": "A", "Sample Number": "S1", "TOC": 8.0, "N": 0.5, "r1100": 0.11, "r1102": 0.13, "r1104": 0.16},
        {"Indice": 2, "Amostra": 2, "Profundidade": "B", "Sample Number": "S2", "TOC": 5.0, "N": 0.3, "r1100": 0.08, "r1102": 0.10, "r1104": 0.12},
    ])
    data_path = tmp_path / "spectra.csv"
    output_dir = tmp_path / "report"
    frame.to_csv(data_path, index=False)

    summary = audit_spectra(data_path, output_dir)

    assert summary["n_rows"] == 3
    assert summary["n_bands"] == 3
    assert summary["repeat_pairs_compared"] == 1
    assert summary["repeated_sample_number_ids"] == 1
    expected = {
        "spectral-qc-by-band.csv",
        "spectral-qc-by-spectrum.csv",
        "spectral-qc-repeat-similarity.csv",
        "spectral-qc-by-depth.csv",
        "spectral-qc-summary.json",
    }
    assert expected.issubset({path.name for path in output_dir.iterdir()})
    saved = json.loads((output_dir / "spectral-qc-summary.json").read_text(encoding="utf-8"))
    assert saved["dataset_sha256"] == summary["dataset_sha256"]
