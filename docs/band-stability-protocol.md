# Repeated grouped band-selection stability

## Question
Which NIR wavelengths are repeatedly selected across independent sampling groups, after removing average spectral and TOC differences attributable to depth?

## Protocol
- Average repeated records within group × point × depth.
- Primary grouping: `Amostra` (new sampling points); secondary sensitivity analysis: `Sample Number`.
- Default: 100 `GroupShuffleSplit` resamples.
- In each split, calculate depth-specific means of each band and TOC using training groups only.
- Center training spectra and target by their training-depth means, then apply `SelectKBest(f_regression)` to select up to 40 bands.
- Report selection frequency and mean univariate rank.

## Interpretation
Selection frequency measures stability of this feature-selection procedure, not chemical specificity, causal relevance or validated predictive value. Collinear adjacent wavelengths can exchange importance. Promising regions must be assessed in a separately nested predictive pipeline and ultimately on independent laboratory samples.
