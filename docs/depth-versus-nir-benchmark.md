# Depth-versus-NIR benchmark

## Scientific question

Does the NIR spectrum predict total organic carbon (TOC) beyond the information
already represented by the sample's depth layer?

## Prespecified scenarios

- `depth_only`: categorical one-hot identity of the nine predefined layers.
- `nir_raw`: raw reflectance only.
- `nir_raw_plus_depth`: raw reflectance and layer identity.
- `nir_savgol_first_derivative`: first derivative (9-band window, polynomial
  order 2, wavelength spacing 2 nm), without depth.
- `nir_savgol_first_derivative_plus_depth`: derivative and layer identity.

Depth is categorical rather than a continuous midpoint. This avoids assuming
that layer codes or unequal layer thicknesses represent a linear response.

## Validation and leakage safeguards

Nested GroupKFold compares Bayesian Ridge, Elastic Net, Huber and Extra Trees.
The outer split estimates generalization; inner grouped out-of-fold predictions
select the model. NIR transformations, one-hot encoding, feature selection and
scaling are fitted inside each training pipeline. The fold-specific training
mean is the no-skill baseline.

Two groupings are reported:
- `Amostra`: primary assessment of transfer to unseen sampling points.
- `Sample Number`: keeps repeated reference identifiers together, a different
  and less spatially demanding generalization question.

All scenarios use the same outer partitions for a given grouping. Reported
pooled metrics are accompanied by fold-level results and selected-model counts.

## Interpretation

Depth-only performance quantifies how much layer identity predicts TOC in this
dataset. NIR-only quantifies spectral prediction without depth. Comparing the
combined model with depth-only estimates whether spectra add predictive value
conditional on layer identity. This is a predictive comparison, not proof of
causal or chemically specific information.

There are only 28 sampling points. Fold-level variability and uncertainty matter;
no small pooled difference should be treated as a validated gain. Spatial
independence cannot be established without coordinates and sampling-design
metadata. TOC units and laboratory reference method remain to be confirmed.

No observations or wavelengths are removed or modified.
