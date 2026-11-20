# Repeated grouped NIR band-selection stability — results

## Run provenance

- Target: TOC
- Spectral variables: 275 bands, 1,100–1,648 nm, 2 nm spacing
- Resampling: 100 repeated `GroupShuffleSplit` runs, seed 42
- Selected features per resample: up to 40
- Primary grouping: `Amostra` (sampling point)
- Secondary grouping: `Sample Number` (identifier semantics remain unconfirmed)
- Before selection, spectral bands and TOC were centered by depth means calculated from training groups only.
- Outputs: `band-stability-amostra.csv`, `band-stability-sample-number.csv`, and `band-stability-summary.csv` in the GitHub Actions artifact.

## Main finding

No individual wavelength was selected in at least half of the 100 resamples:
the maximum selection frequency was 49% under grouping by `Amostra` and 48%
under grouping by `Sample Number`. Thus, there is no single highly stable
wavelength under this procedure.

However, a contiguous region around **1,440–1,488 nm** was repeatedly selected
under both grouping strategies. Across the 26 bands in that interval, mean
selection frequency was 47.3% for `Amostra` and 45.7% for `Sample Number`.
Within 1,460–1,480 nm (11 bands), the corresponding means were 48.6% and 46.9%.

The selection-frequency rankings across all 275 bands were concordant between
the two grouping strategies (Spearman correlation approximately 0.779). The
strongest shared individual band was r1470 (1,470 nm), selected in 49% of
point-group resamples and 48% of Sample Number resamples. Nearby bands had
similar frequencies:

| Band | Wavelength (nm) | Amostra | Sample Number |
|---|---:|---:|---:|
| r1470 | 1,470 | 49% | 48% |
| r1476 | 1,476 | 49% | 47% |
| r1468 | 1,468 | 49% | 47% |
| r1472 | 1,472 | 49% | 47% |
| r1474 | 1,474 | 49% | 47% |
| r1464 | 1,464 | 47% | 47% |
| r1462 | 1,462 | 48% | 47% |
| r1466 | 1,466 | 49% | 47% |
| r1458 | 1,458 | 48% | 47% |
| r1456 | 1,456 | 47% | 47% |

A second region around 1,100–1,180 nm appeared more often in the
`Sample Number` analysis (mean 38.2%) than in the point-group analysis
(mean 29.8%), suggesting greater sensitivity to the grouping definition.

## Interpretation

1. The most defensible result is a **candidate spectral region**, not a
   uniquely stable wavelength: approximately 1,440–1,488 nm.
2. Adjacent NIR bands are strongly collinear. Selection can move between
   neighboring wavelengths across resamples, so a flat cluster of similar
   frequencies is expected and should not be interpreted as multiple
   independent chemical signals.
3. This is univariate feature-selection stability after depth centering. It
   does not establish that the region improves out-of-sample TOC prediction,
   identify a molecular mechanism, or validate a calibration.
4. The earlier layer-wise benchmark showed no consistent NIR gain over a
   layer-specific mean baseline. The current result does not overturn that
   predictive finding.

## Recommended next step

Treat 1,440–1,488 nm as a pre-specified candidate region in a new nested,
grouped comparison against (a) the layer-mean baseline, (b) all-band NIR and
(c) the candidate-window NIR model. Keep feature selection and tuning inside
the training folds, compare point-group and Sample Number grouping, and report
paired outer-fold errors. Any confirmatory claim still requires independent
laboratory samples, verified TOC units/reference method and a documented
sampling design.
