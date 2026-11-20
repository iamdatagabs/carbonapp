# Group-aware uncertainty and conformal intervals

`carbonapp.uncertainty.grouped_split_conformal` creates a train/calibration/test split by group. The estimator is fitted only on training groups; calibration residuals come from disjoint calibration groups; coverage is assessed on disjoint test groups.

## Group-level nonconformity
For each calibration group, the score is the maximum absolute residual among its rows. The conformal quantile uses the finite-sample order statistic `ceil((G + 1) * (1 - alpha))`, where G is the number of calibration groups. If the required order statistic exceeds G, the quantile is infinite; the function reports this rather than silently using an invalid percentile.

The resulting symmetric intervals target simultaneous coverage of all rows within a new exchangeable group. This is deliberately more conservative than treating every scan/row as independent. Report both row coverage and group-simultaneous coverage on the untouched test groups.

## Group choice and limitations
- `Sample Number` keeps repeated sample/reference records together.
- `Amostra` holds out entire sampling points/parcels and is the more demanding transfer analysis.
- The guarantee relies on exchangeability of independent groups. Spatial autocorrelation, blocks, treatments or hierarchical sampling may require a higher-level grouping design.
- The single split is sensitive to the random partition; repeat with predeclared seeds or use repeated external evaluation as a stability analysis, without pooling calibration/test data across runs.
- Prediction intervals quantify predictive uncertainty under the validation design; they do not resolve unknown laboratory units, reference-method provenance or target validity.
- TOC and N remain separate targets. N is exploratory until its laboratory reference method, units and provenance are confirmed.
