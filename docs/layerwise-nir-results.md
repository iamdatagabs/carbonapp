# Layer-wise NIR benchmark — results

## Executive result

The exploratory nested grouped cross-validation did **not** identify a consistent
incremental predictive contribution from NIR spectra over a training-fold mean
TOC baseline within individual depth layers.

The benchmark aggregates repeated records to one mean spectrum per
`Amostra × Profundidade`, then performs nested GroupKFold by `Amostra`.
There are only 21–27 independent sampling points per layer. Results are
therefore exploratory and should not be interpreted as external validation.

## Pooled out-of-fold results by layer

RMSE is reported in the dataset's TOC units, which have not yet been verified
against laboratory documentation. The percentage column is
`100 × (scenario RMSE − baseline RMSE) / baseline RMSE`; negative values
indicate improvement over the mean baseline.

| Layer | Points | Mean baseline RMSE | Raw NIR RMSE | Raw Δ RMSE (%) | First-derivative RMSE | Derivative Δ RMSE (%) |
|---|---:|---:|---:|---:|---:|---:|
| A | 27 | 2.792 | 2.810 | +0.6 | 2.841 | +1.8 |
| B | 25 | 3.368 | 3.329 | **−1.2** | 3.811 | +13.1 |
| C | 25 | 2.762 | 2.795 | +1.2 | 2.807 | +1.6 |
| D | 24 | 1.635 | 1.750 | +7.1 | 1.830 | +12.0 |
| E | 26 | 2.875 | 2.940 | +2.3 | 3.307 | +15.0 |
| F | 27 | 2.999 | 3.357 | +11.9 | 3.146 | +4.9 |
| G | 21 | 2.159 | 2.213 | +2.5 | 2.778 | +28.7 |
| H | 25 | 2.131 | 2.248 | +5.5 | 2.630 | +23.4 |
| I | 24 | 1.430 | 1.442 | +0.8 | 1.469 | +2.7 |

Only raw NIR in layer B reduced pooled RMSE relative to its baseline, and the
reduction was small (about 1.2%). First-derivative NIR did not reduce RMSE in
any layer. Raw NIR MAE was slightly lower than baseline in B, C and I, but
these modest differences were not accompanied by consistent RMSE improvement.
The raw-NIR pooled R² was positive only in B (0.0087); all other layer-wise
raw-NIR R² values were negative. All first-derivative R² values were negative.

## Interpretation

1. No layer currently provides convincing evidence of useful NIR-based TOC
   prediction beyond the layer-specific mean.
2. The small apparent advantage in layer B is exploratory, based on 25 points
   and one grouped nested-CV run; it is not evidence of a validated layer-
   specific calibration.
3. The first derivative generally worsened error, particularly in layers
   G and H. This does not rule out other preprocessing or spectral regions,
   but does not justify adopting this derivative as the current default.
4. The high predictive performance of depth-only models in the pooled
   analysis must not be attributed to NIR: depth is a strong structural
   predictor in this dataset, while within-layer NIR performance remains weak.

## Limitations and next analyses

- Per-layer sample sizes are small, and nine layer-wise comparisons create
  multiplicity and selection concerns.
- No independent geographic or external validation set is available.
- Spatial independence cannot be assumed because coordinates and sampling
  blocks are unavailable.
- TOC units and the laboratory reference method remain to be confirmed.
- Nitrogen (N) remains exploratory and is not validated by this TOC benchmark.

A useful next step is to assess whether any spectral-region or feature signal
is stable across grouped resamples, with feature selection performed entirely
inside each training fold. Such analysis should be treated as hypothesis
generation, not a route to post-hoc calibration claims.
