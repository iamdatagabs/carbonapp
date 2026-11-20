# Statistical analysis module

The `carbonapp.statistics` module currently provides reproducible exploratory
summaries for the stored TOC/N targets and NIR reflectance matrix.

## Available functions

- `describe_targets(frame)`: sample count, mean, standard deviation, median,
  quartiles, minimum and maximum for TOC and N.
- `describe_by_depth(frame)`: target summaries by the measured depth classes,
  including their actual top/bottom limits, midpoint and unequal thickness.
- `describe_spectra(frame)`: distribution summaries for each wavelength.
- `target_band_associations(frame, target, method)`: Pearson or Spearman
  band/target associations, conventional p-values and Benjamini-Hochberg
  adjusted q-values across the wavelength family.

No physical unit is assigned to TOC or N until the laboratory metadata and
reference method are confirmed.

## Inferential limitations

The row-level p-values in band association are screening statistics. They do
not account for repeated observations, shared profiles, or possible technical
replicates. The dataset audit found repeated `Sample Number` values and
identical target values within some repeated IDs. Their experimental meaning
must be confirmed before confirmatory hypothesis tests are implemented.

Likewise, comparisons across depth layers should use a repeated-measures,
cluster-aware, or hierarchical design that matches the actual sampling unit.
The current depth summaries are descriptive and must not be presented as
independent-sample inferential tests.

The Benjamini-Hochberg adjustment addresses multiplicity across the tested
spectral bands; it does not correct dependence between observations or
establish causality.
