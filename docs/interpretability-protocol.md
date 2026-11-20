# Interpretability and spectral explainability protocol

## Scope

This module provides three complementary views of model behavior:

1. **Selection stability:** frequency with which each NIR band is selected by fold-local univariate feature selection across GroupKFold training partitions.
2. **Grouped permutation importance:** increase in RMSE after shuffling between-group wavelength means on a held-out set, while retaining within-group deviations.
3. **SHAP:** model-agnostic local additive attributions for predictions on held-out groups. Install the optional extra with `pip install -e ".[explainability]"`.
4. **Depth-stratified importance:** independent grouped holdout analyses within each of the nine depth layers. Layers with too few groups are omitted or rejected.

## Grouping and leakage

Use `Sample Number` as the default group while its relation to repeated scans/reference measurements remains the appropriate leakage boundary. Repeat analyses grouped by `Amostra` to test transfer to unseen sampling points. Train and test groups are disjoint in permutation and SHAP analyses. Permutation shuffles group-level band means while preserving within-group deviations. SHAP background and explained subsets use one representative row per group to avoid over-weighting groups with more repeated rows. Selection stability fits the selector independently inside each GroupKFold training partition.

## Interpretation limits

- NIR bands are strongly correlated. A single-band permutation can underestimate the importance of a wavelength when neighboring bands carry redundant information. Consider reporting contiguous wavelength windows or grouped permutations as a follow-up.
- Selection frequency measures algorithmic stability under the specified folds and selector; it is not a confidence interval or a significance test.
- SHAP explains the fitted predictor relative to its background sample. It does not identify chemical mechanisms, causal effects, or laboratory validity.
- Depth-specific models are fitted separately and can have different sample sizes and target distributions. Compare them with those limitations stated; do not infer a depth interaction from separate importance rankings alone.
- The 266-row dataset contains 28 sampling points and repeated Sample Number identifiers. A point-level analysis may have limited independent groups per layer.
- TOC is the target directly supported by the dissertation. N remains exploratory until its reference method, units, and provenance are verified.

## Example

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
by_depth = depth_stratified_importance(df, target="TOC")
```

For final reporting, predefine the grouping level and random seed, save the exact dataset version and model configuration, and avoid selecting a model based on the same holdout used for its reported importance.
