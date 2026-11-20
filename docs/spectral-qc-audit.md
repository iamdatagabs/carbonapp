# Raw NIR spectral quality audit

Run the descriptive audit before selecting a scatter correction or derivative:

```bash
python scripts/audit_spectral_data.py \
  --data "data/raw/[quad]base_nirs_refletancia.csv" \
  --output reports/spectral-qc
```

The audit reports per-wavelength distributions, per-spectrum scale and
smoothness diagnostics, within-`Sample Number` spectral similarity, and
summaries by depth. It does not remove observations, flag rows for automatic
exclusion, or fit a predictive model.

Review the output alongside the instrument's acquisition protocol. Negative
values, scale differences, derivative-like shapes, and repeated spectra can
have legitimate instrumental or preprocessing explanations. Do not infer
technical-replicate semantics from identifier repetition alone.

The audit is descriptive and does not establish chemical validity, instrument
calibration, or the best preprocessing method.
