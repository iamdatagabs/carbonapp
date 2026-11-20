# Layer-wise NIR benchmark

## Research question

Does NIR carry predictive information about TOC variation among sampling
points **within an individual depth layer**? The preceding pooled within-depth
benchmark found no incremental gain when all layers were modeled together.
This experiment checks whether a signal may be confined to a subset of layers.

## Unit of analysis and validation

Repeated rows are collapsed to one observation per `Amostra × Profundidade`,
using the mean spectrum and mean TOC. TOC must be constant within each
point-depth pair; the code rejects inconsistent targets. Each depth layer is
modeled independently. Nested `GroupKFold` splits by `Amostra`, so all
observations from a sampling point remain in one fold.

Within each outer fold, the baseline is the mean TOC in that layer calculated
from training points only. NIR models are trained to predict deviations from
that mean. Model and preprocessing selection occur inside grouped inner folds.
Raw spectra and Savitzky–Golay first derivatives are compared.

## Interpretation limits

There are only about 20–27 sampling points per layer. The nine layer-wise
comparisons are exploratory and subject to substantial uncertainty and
multiple-comparison effects. A favorable layer does not constitute validation
of a general NIR method, prove chemical specificity, or establish external
validity. TOC units and laboratory reference method remain to be confirmed.
