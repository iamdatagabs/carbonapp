# NIR preprocessing comparison protocol

## Objective
Compare raw spectra, SNV, MSC, Savitzky-Golay smoothing and first derivative
for total organic carbon (TOC). No method is assumed to be preferable.

## Methods
- Raw: original reflectance values, unchanged.
- SNV: row-wise centering and scaling by each spectrum's sample standard deviation.
- MSC: multiplicative scatter correction against the mean spectrum of the
  current training partition. The reference is re-estimated in every fold.
- Savitzky-Golay smoothing: 9-band window, polynomial order 2, derivative 0.
- Savitzky-Golay first derivative: 9-band window, polynomial order 2,
  derivative 1, wavelength spacing 2 nm.

Feature selection and scaling are also inside each estimator pipeline. No
transformation is fitted once on the complete dataset.

## Validation
For each preprocessing method, nested GroupKFold is used. Inner folds select
among Bayesian Ridge, Elastic Net, Huber and Extra Trees. The selected pipeline
is refitted on the outer training partition and evaluated on untouched outer
test groups. A fold-specific training-mean predictor is the no-skill baseline.

The comparison is run twice: grouping by Sample Number keeps repeated
reference identifiers together; grouping by Amostra evaluates transfer to
previously unseen sampling points. These are distinct generalization questions.
Neither proves spatial independence without coordinates and sampling-design data.

## Outputs
- preprocessing-sample-number.json
- preprocessing-amostra.json
- preprocessing-comparison-summary.csv

The JSON files retain fold metrics, selected models, outer predictions and
residuals. The CSV is a compact summary.

## Interpretation safeguards
- Pooled outer-fold metrics are uncertain with only 28 sampling points.
- Compare methods against their fold-specific mean baseline and inspect
  fold-level variability, residual structure and model-selection stability.
- Do not select a method solely from a small difference in pooled RMSE.
- Savitzky-Golay delta is 2 nm, matching the wavelength spacing.
- Preserve original CSV values; no row or wavelength is automatically removed.
- TOC units and laboratory reference method remain to be confirmed.
- This experiment does not validate nitrogen prediction, external transfer,
  chemical calibration or deployment.
