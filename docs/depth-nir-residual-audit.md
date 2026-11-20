# Depth-versus-NIR residual audit

This audit consumes the out-of-fold predictions from the depth-versus-NIR
benchmark; it does not retrain models or alter the source spectra.

## Outputs

- `depth-nir-residuals-by-depth.csv`: MAE, RMSE and signed bias within each
  predefined layer, for each scenario and grouping.
- `depth-nir-fold-rmse-deltas.csv`: paired outer-fold RMSE difference relative
  to `depth_only`. Positive values mean the scenario is worse.
- `depth-nir-residual-audit.json`: compact provenance and interpretation note.

The primary grouping remains `Amostra` (held-out sampling points). The
`Sample Number` grouping is secondary and answers a different generalization
question. All metrics are descriptive diagnostics of the existing out-of-fold
predictions; layer-stratified residuals can reveal where a model struggles but
cannot establish a causal or chemical mechanism. Row order must remain aligned
with the original CSV used to produce the benchmark JSON.
