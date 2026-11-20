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