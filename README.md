# CarbonApp — Soil Spectroscopy Research Platform

A reproducible research codebase for near-infrared (NIR) soil spectroscopy, prediction of total organic carbon (TOC), exploratory nitrogen analysis, uncertainty estimation, spectral interpretability, compact model export and interactive vertical-profile exploration.

The original research notebooks and source data are preserved. New engineering work lives in the `research/reproducible-core` branch until it has passed automated validation and scientific review.

## Dataset and scientific scope

The initial static audit of `data/raw/[quad]base_nirs_refletancia.csv` recorded 266 rows, 275 NIR bands from 1,100 to 1,648 nm at 2 nm intervals, and no missing values in TOC or N. The physical depth intervals were confirmed as:

| Code | Depth (cm) | Thickness (cm) |
|---|---:|---:|
| A | 0–10 | 10 |
| B | 10–20 | 10 |
| C | 20–40 | 20 |
| D | 40–60 | 20 |
| E | 60–80 | 20 |
| F | 80–100 | 20 |
| G | 100–130 | 30 |
| H | 130–160 | 30 |
| I | 160–200 | 40 |

`Amostra` identifies the sampling point/plot; `Profundidade` identifies its layer. `Sample Number` is used as the default leakage-prevention group for repeated observations, pending confirmation of its laboratory meaning. For generalization to new sampling points, repeat evaluation grouped by `Amostra`.

**Scientific limitations:** TOC units and laboratory reference method must be verified against laboratory documentation. N is exploratory until its units, reference method and provenance are confirmed. A point-by-depth 3D plot is not a geographic soil volume: no geographic coordinates are currently available.

## Research core

| Module | Responsibility |
|---|---|
| `data.py`, `depth.py` | Schema validation, spectral-band discovery and authoritative 0–200 cm depth metadata |
| `statistics.py`, `experimental.py` | Descriptive statistics, data-structure audit and paired point-level comparisons |
| `evaluation.py`, `model_comparison.py` | Leakage-aware pipelines, grouped OOF comparison and nested grouped model selection |
| `uncertainty.py` | Group split-conformal prediction intervals |
| `interpretability.py` | Feature-selection stability, group-held-out permutation importance, optional SHAP and depth-stratified analysis |
| `profile.py` | Point-aware profile aggregation, equal-point summaries and 3D-ready payload |
| `tinyml.py` | Linear ONNX export, dynamic INT8 quantization, prediction-drift comparison and host benchmarks |
| `api.py` | Optional FastAPI endpoints for metadata, dataset summary and vertical profiles |
| `apps/frontend/` | Static dashboard with vertical and categorical 3D Plotly visualizations |

## Methodological safeguards

- All learned preprocessing and feature selection are fitted inside training folds.
- Keep repeated `Sample Number` rows together to reduce leakage across scans/references.
- Use `Amostra` as the grouping unit for point-level transfer and paired depth inference, subject to the sampling design.
- Model ranking and explanations are not causal evidence. Adjacent NIR bands are collinear.
- Nested grouped CV estimates the model-selection procedure; retain an untouched external test where possible.
- Conformal coverage depends on exchangeability of independent groups. Spatial dependence or nested blocks require a higher-level grouping strategy.
- Quantization must be evaluated on held-out groups against both reference predictions and laboratory targets.
- Host latency and Python allocation measurements are not embedded-device RAM, flash, energy or latency claims.

## Local development and tests

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev,api]"
pytest -q
```

The CI workflow installs `.[dev,api]` and runs the test suite on Python 3.11. Optional explainability and TinyML dependencies are installed separately:

```bash
pip install -e ".[explainability]"
pip install -e ".[tinyml]"
```

## Run the research analyses

```python
from carbonapp.data import load_dataset
from carbonapp.model_comparison import nested_grouped_model_selection
from carbonapp.interpretability import (
    feature_selection_stability,
    grouped_permutation_importance,
    depth_stratified_importance,
)
from carbonapp.profile import build_profile_summary, build_profile_3d_payload

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")

# Final selection-procedure estimate; repeat with group_column="Amostra".
nested = nested_grouped_model_selection(
    df, target="TOC", group_column="Sample Number",
    outer_splits=5, inner_splits=4,
)
print(nested["metrics"])

stability = feature_selection_stability(df, target="TOC")
permutation = grouped_permutation_importance(df, target="TOC")
by_depth = depth_stratified_importance(df, target="TOC")

profile_summary = build_profile_summary(df, target="TOC")
profile_3d = build_profile_3d_payload(df, target="TOC")
```

For SHAP, use `grouped_shap_explanation` after installing the `explainability` extra. See `docs/model-comparison-protocol.md`, `docs/uncertainty-methodology.md` and `docs/interpretability-protocol.md`.

## API and interactive dashboard

Install the API extra and start the service:

```bash
pip install -e ".[api]"
uvicorn carbonapp.api:create_app --factory --reload
```

The API defaults to `data/raw/[quad]base_nirs_refletancia.csv`. Override with `CARBONAPP_DATA_PATH`. Serve `apps/frontend/index.html` over HTTP to open the dashboard. For a separate frontend origin, set `window.CARBONAPP_API_BASE` before `app.js` and configure the API allowlist:

```bash
CARBONAPP_CORS_ORIGINS=https://your-static-site.example
```

Endpoints:

- `GET /health`
- `GET /api/v1/metadata/depths`
- `GET /api/v1/dataset/summary?target=TOC|N`
- `GET /api/v1/profiles/{point_id}?target=TOC|N`
- `GET /api/v1/profiles-3d?target=TOC|N`

See `docs/api-and-frontend.md` for setup and deployment boundaries.

## TinyML workflow

The first ONNX export supports fitted linear pipelines (Huber, Elastic Net and Bayesian Ridge), folding feature selection and standardization into a single linear operator. Export, quantize and compare predictions on the same held-out spectra:

```python
from carbonapp.data import load_dataset, spectral_columns
from carbonapp.model_comparison import build_model_pipeline
from carbonapp.tinyml import (
    export_linear_pipeline_onnx, quantize_onnx_dynamic,
    compare_onnx_models, benchmark_onnx_model,
)

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")
bands = spectral_columns(df)
model = build_model_pipeline("huber", k=40).fit(df[bands], df["TOC"])
export_linear_pipeline_onnx(model, bands, "models/onnx/toc_float.onnx")
quantize_onnx_dynamic("models/onnx/toc_float.onnx", "models/onnx/toc_int8.onnx")
drift = compare_onnx_models("models/onnx/toc_float.onnx", "models/onnx/toc_int8.onnx", df[bands].iloc[:20])
print(drift)
```

This snippet illustrates the API only; final artifacts must be trained under the grouped protocol and the comparison must use a held-out group set. See `docs/tinyml-protocol.md`.

## Repository structure

- `data/raw/`: original research data
- `docs/`: dissertation, audits and scientific protocols
- `src/carbonapp/`: reusable scientific and API modules
- `apps/frontend/`: static interactive dashboard
- `tests/`: automated tests
- `models/`, `reports/`, `experiments/`: reserved for versioned outputs and artifacts
- `notebooks/`: historical and exploratory notebooks

## Provenance and license

The original master's research is documented in `docs/Dissertacao.pdf`. Laboratory units, reference methods and sample identifier semantics should be cited from the corresponding original records before confirmatory claims are made. A repository license has not yet been specified; reuse and redistribution remain subject to applicable rights and permissions.
