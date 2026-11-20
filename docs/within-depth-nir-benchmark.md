# Within-depth NIR residual benchmark

## Research question

Does NIR predict variation in TOC among observations from the same categorical
depth layer, beyond a layer mean estimated only from the training partition?

## Method

For every outer grouped fold, compute the mean TOC for each depth layer using
outer-training rows only. The baseline predicts that mean for held-out rows.
For each NIR preprocessing (raw and Savitzky–Golay first derivative), train a
spectral model to predict deviations from the training-layer mean.

Model selection uses inner grouped folds. Crucially, layer means and residual
targets are recomputed from each inner-training partition; inner-validation
targets never contribute to their own baseline. The final outer model is fitted
on outer-training residuals and evaluated on held-out groups.

Primary grouping is `Amostra` (new sampling points); `Sample Number` is
secondary. Compare MAE/RMSE/R² and paired outer-fold RMSE against the
depth-mean baseline. This tests predictive incremental signal, not causality,
chemical specificity, or external validity. Layer-wise sample counts are small,
so results remain exploratory.
