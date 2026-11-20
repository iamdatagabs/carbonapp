# CarbonApp — Soil Spectroscopy & Machine Learning

Research software for estimating soil organic carbon and nitrogen from near-infrared (NIR) spectral reflectance, with a roadmap toward reproducible statistical analysis, machine learning, TinyML and interactive soil-profile visualization.

> This repository is being revived from the original master's research. Original notebooks and data are preserved while a reproducible scientific core is developed.

## Research data currently available

The repository includes a spectral dataset with:
- 266 observations;
- 275 spectral bands from 1,100 to 1,648 nm at 2 nm intervals;
- metadata columns for sample, depth code, TOC and N;
- no missing values observed in the TOC and N columns in the initial static audit.

**Important:** the physical depth mapping is confirmed: A 0–10, B 10–20, C 20–40, D 40–60, E 60–80, F 80–100, G 100–130, H 130–160 and I 160–200 cm. TOC/N units and laboratory reference methods remain to be confirmed; values must not be assigned inferred units.

## Repository contents

| Path | Purpose |
|---|---|
| `data/raw/` | Original spectral dataset |
| `docs/Dissertacao.pdf` | Master's dissertation |
| `docs/technical-audit.md` | Initial methodological and software audit |
| `docs/data-dictionary.md` | Data dictionary, spectral schema and confirmed depth intervals |
| `src/carbonapp/depth.py` | Authoritative 0–200 cm soil profile metadata |
| `src/carbonapp/data.py` | Dataset schema validation and spectral-band discovery |
| `src/carbonapp/evaluation.py` | GroupKFold evaluation with preprocessing inside each fold |
| `tests/test_depth.py` | Tests for profile geometry |
| `pyproject.toml` | Python package and development dependencies |
| `Filtro_Carbono.ipynb` | Original filter-based feature-selection experiments |
| `RFE_Carbon.ipynb` | Original recursive feature-elimination experiments |

## Scientific and engineering roadmap

1. **Data engineering:** validated ingestion, schema checks, provenance and data-quality reports.
2. **Descriptive and inferential statistics:** distributions, associations, uncertainty and group-aware comparisons.
3. **Machine learning:** reproducible baselines and model comparisons for TOC and N, with preprocessing and feature selection inside cross-validation.
4. **Probabilistic evaluation:** prediction intervals, calibration and uncertainty analysis.
5. **TinyML:** compact models, quantization and measurements of latency, memory and model size after scientific validation.
6. **Soil visualization:** interactive vertical profiles linked to verified depth intervals; spatial 3D only when spatial coordinates support it.
7. **Web platform:** interactive scientific dashboards and reproducible reports.

## Methodological principles

- Avoid data leakage by fitting every learned preprocessing step within each training fold.
- Respect sample/profile grouping when creating train/test partitions.
- Keep external validation separate from model selection.
- Record dataset versions, random seeds, transformations, hyperparameters and metrics.
- Distinguish reproduced dissertation results from new experiments.
- Do not infer laboratory units or physical depth mappings from column names alone.

## Current status

The current branch, `research/reproducible-core`, contains the audit, data dictionary, authoritative depth metadata, dataset validation, a grouped Huber baseline and initial tests. The original notebooks are retained as historical research artifacts; their evaluation procedures require revision before their scores can be treated as unbiased estimates. The grouped evaluator keeps repeated `Sample Number` observations in the same GroupKFold fold and fits scaling and feature selection inside each fold.

## Citation and provenance

The original research is documented in `docs/Dissertacao.pdf`. Dataset provenance and experimental metadata should be cited from the dissertation and the corresponding laboratory documentation when the methodology is finalized.

## License

A license has not yet been specified. Until one is added, reuse and redistribution are subject to the applicable rights and permissions.

## Local development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the grouped baseline from Python:

```python
from carbonapp.data import load_dataset
from carbonapp.evaluation import grouped_oof_evaluation

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")
results = grouped_oof_evaluation(df, target="TOC", n_splits=5)
print(results["metrics"])
```
