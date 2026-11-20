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
| `docs/statistical-methodology.md` | Statistical methods and inferential limitations |
| `src/carbonapp/depth.py` | Authoritative 0–200 cm soil profile metadata |
| `src/carbonapp/data.py` | Dataset schema validation and spectral-band discovery |
| `src/carbonapp/statistics.py` | Descriptive statistics, spectral summaries and exploratory associations |
| `src/carbonapp/experimental.py` | Sampling-design audit, replicate aggregation and paired cluster bootstrap |
| `src/carbonapp/evaluation.py` | GroupKFold Huber baseline with fold-local preprocessing |\n| `src/carbonapp/model_comparison.py` | Grouped OOF comparison: Huber, Extra Trees, Elastic Net and Bayesian Ridge |\n| `docs/model-comparison-protocol.md` | Grouping strategy, model comparison and selection caveats |
| `tests/` | Unit tests for depth, statistics and experimental-design functions |
| `pyproject.toml` | Python package and development dependencies |
| `Filtro_Carbono.ipynb` | Original filter-based feature-selection experiments |
| `RFE_Carbon.ipynb` | Original recursive feature-elimination experiments |

## Scientific and engineering roadmap

1. **Data engineering:** validated ingestion, schema checks, provenance and data-quality reports.
2. **Descriptive and inferential statistics:** distributions, associations, uncertainty and group-aware comparisons.
3. **Machine learning:** reproducible baselines and model comparisons for TOC and N, with preprocessing and feature selection inside cross-validation.
4. **Probabilistic evaluation:** prediction intervals, calibration and uncertainty analysis.
5. **Interpretability:** fold-wise feature-selection stability, group-held-out permutation importance, optional SHAP and depth-stratified analyses.\n6. **TinyML:** compact models, quantization and measurements of latency, memory and model size after scientific validation.
7. **Soil visualization:** interactive vertical profiles linked to verified depth intervals; spatial 3D only when spatial coordinates support it.
8. **Web platform:** interactive scientific dashboards and reproducible reports.

## Methodological principles

- Avoid data leakage by fitting every learned preprocessing step within each training fold.
- Respect sample/profile grouping when creating train/test partitions.
- Keep external validation separate from model selection.
- Record dataset versions, random seeds, transformations, hyperparameters and metrics.
- Distinguish reproduced dissertation results from new experiments.
- Do not infer laboratory units or physical depth mappings from column names alone.
- Treat repeated `Sample Number` rows as technical replicates only after confirming their laboratory meaning.
- Use profile-level resampling only after confirming that the selected profile identifier represents the independent sampling unit.

## Current status

The `research/reproducible-core` branch contains the audit, data dictionary, authoritative depth metadata, dataset validation, grouped Huber baseline, descriptive statistics, sampling-design audit and an exploratory paired depth bootstrap. The original notebooks are retained as historical research artifacts; their evaluation procedures require revision before their scores can be treated as unbiased estimates.

The grouped evaluators keep repeated `Sample Number` observations in the same GroupKFold fold and fit scaling and feature selection inside each fold. The model-comparison module adds Huber, Extra Trees, Elastic Net and Bayesian Ridge, with pooled out-of-fold predictions and R², MAE, RMSE and bias. Run a second analysis grouped by `Amostra` to assess transfer to unseen sampling points. Candidate rankings are exploratory; final selected-model performance requires nested grouped CV or an untouched grouped test set. The experimental module can collapse repeated rows per `Sample Number` (averaging spectral scans while requiring invariant targets and metadata) and estimate paired depth contrasts by resampling whole sampling points/plots. `Amostra` identifies the point/plot; `Profundidade` identifies the repeated layer within that point. The technical-replicate interpretation of `Sample Number` still requires confirmation before aggregation.

## Citation and provenance

The original research is documented in `docs/Dissertacao.pdf`. Dataset provenance and experimental metadata should be cited from the dissertation and the corresponding laboratory documentation when the methodology is finalized.

## License

A license has not yet been specified. Until one is added, reuse and redistribution are subject to the applicable rights and permissions.

## Local development

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
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

Run the exploratory sampling-design audit and paired contrast:

```python
from carbonapp.data import load_dataset
from carbonapp.experimental import audit_sample_structure, paired_depth_bootstrap

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")
print(audit_sample_structure(df))
# Only after verifying that "Amostra" is the independent profile/cluster:
contrast = paired_depth_bootstrap(df, target="TOC", depth_a="A", depth_b="I")
print(contrast)
```

## Compare candidate models

```python
from carbonapp.data import load_dataset
from carbonapp.model_comparison import compare_grouped_models

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")

# Keep repeated sample/reference identifiers together.
by_reference = compare_grouped_models(df, target="TOC", group_column="Sample Number", n_splits=5)

# Hold out complete sampling points/parcels for a stricter transfer analysis.
by_sampling_point = compare_grouped_models(df, target="TOC", group_column="Amostra", n_splits=5)

print(by_reference["ranking_by_rmse"])
print(by_sampling_point["ranking_by_rmse"])
```

Use `target="N"` only as an explicitly exploratory experiment until its laboratory reference method, units and provenance are verified. See `docs/model-comparison-protocol.md` before interpreting rankings.

For an estimate that accounts for choosing among candidate model families,
use nested grouped CV:

```python
from carbonapp.model_comparison import nested_grouped_model_selection

nested = nested_grouped_model_selection(
    df, target="TOC", group_column="Sample Number",
    outer_splits=5, inner_splits=4
)
print(nested["metrics"])
print(nested["selected_model_counts"])
```

The outer folds estimate the model-selection procedure; they are not a score
for a final model refitted on all observations. See the model-comparison
protocol for interpretation and the stricter point-held-out analysis.

## Group-aware prediction intervals

```python
from carbonapp.uncertainty import grouped_split_conformal

# Use Sample Number for scan/reference grouping, then repeat with Amostra
# for a stricter point-held-out transfer assessment.
intervals = grouped_split_conformal(
    df, target="TOC", group_column="Sample Number",
    model_name="huber", alpha=0.10
)
print(intervals["metrics"])
print(intervals["n_calibration_groups"], intervals["quantile"])
```

Calibration and test partitions are disjoint at the group level. The conformal
quantile uses the maximum absolute residual per calibration group, targeting
simultaneous within-group coverage under exchangeability of independent groups.
If the calibration partition has too few groups for the requested coverage,
the interval is infinite by the finite-sample rule; do not replace it with an
arbitrary percentile. See `docs/uncertainty-methodology.md`.

## Spectral interpretability

Install the optional SHAP dependency when needed:

```bash
pip install -e ".[explainability]"
```

Run group-aware analyses:

```python
from carbonapp.data import load_dataset
from carbonapp.interpretability import (
    feature_selection_stability,
    grouped_permutation_importance,
    grouped_shap_explanation,
    depth_stratified_importance,
)

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")
stability = feature_selection_stability(df, target="TOC", group_column="Sample Number")
permutation = grouped_permutation_importance(df, target="TOC", group_column="Sample Number")
shap_result = grouped_shap_explanation(df, target="TOC", group_column="Sample Number")
depth_importance = depth_stratified_importance(df, target="TOC")
```

The selection-stability analysis refits the feature selector within each training fold. Permutation and SHAP explanations use held-out groups. Spectral collinearity means individual-band importance is not causal or chemical proof; interpret contiguous bands and depth-specific analyses cautiously. See `docs/interpretability-protocol.md`.


## Spectral interpretability

Install the optional SHAP dependency when needed:

```bash
pip install -e ".[explainability]"
```

Run group-aware analyses:

```python
from carbonapp.data import load_dataset
from carbonapp.interpretability import (
    feature_selection_stability,
    grouped_permutation_importance,
    grouped_shap_explanation,
    depth_stratified_importance,
)

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")
stability = feature_selection_stability(df, target="TOC", group_column="Sample Number")
permutation = grouped_permutation_importance(df, target="TOC", group_column="Sample Number")
shap_result = grouped_shap_explanation(df, target="TOC", group_column="Sample Number")
depth_importance = depth_stratified_importance(df, target="TOC")
```

Permutation and SHAP explanations use held-out groups. Spectral collinearity means individual-band importance is not causal or chemical proof; interpret contiguous bands and depth-specific analyses cautiously. See `docs/interpretability-protocol.md`.
