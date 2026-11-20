# Statistical and experimental methodology

## Descriptive analysis

The `carbonapp.statistics` module provides reproducible exploratory summaries:
- `describe_targets(frame)`: sample count, mean, standard deviation, median, quartiles, minimum and maximum for TOC and N.
- `describe_by_depth(frame)`: target summaries by depth class, including actual top/bottom limits, midpoint and unequal thickness.
- `describe_spectra(frame)`: distribution summaries for each wavelength.
- `target_band_associations(frame, target, method)`: Pearson or Spearman band/target associations, conventional p-values and Benjamini-Hochberg adjusted q-values across wavelengths.

No physical unit is assigned to TOC or N until laboratory metadata and reference methods are confirmed.

## Experimental-design audit

`carbonapp.experimental.audit_sample_structure(frame)` reports row counts, point/plot counts, repeated `Sample Number` identifiers, point-depth coverage, and target inconsistencies within repeated IDs. In this dataset, `Amostra` identifies the sampling point/plot (the numeric point identifier), while `Profundidade` identifies its layer (A-I). The point is therefore the cluster for within-point depth comparisons.

`aggregate_replicate_rows(frame)` collapses repeated rows sharing a `Sample Number`. It requires profile, depth, TOC and N to be invariant within that identifier, averages the spectral bands, and retains one target value. Use this only if laboratory records confirm that repeated rows are technical scans of the same sample/reference. If they are independent laboratory samples, do not collapse them.

## Paired depth contrast

`paired_depth_bootstrap(frame, target, depth_a, depth_b, profile_column="Amostra")` uses `Amostra` as the sampling point/plot cluster:
1. collapses repeated spectral rows per `Sample Number` after checking invariant metadata and targets;
2. averages distinct `Sample Number` values within each profile and depth;
3. retains profiles observed at both requested depths;
4. calculates the paired difference (depth B minus depth A);
5. obtains a percentile confidence interval by resampling whole profiles.

This is an exploratory cluster-bootstrap procedure, not a substitute for a finalized sampling-design model. `Amostra` is the point/plot identifier and is the resampling cluster for paired depth contrasts. Repeated rows under `Sample Number` are still collapsed only conditionally: the laboratory meaning of that identifier must be confirmed. Do not interpret the interval as confirmatory until the independence of points, missing-depth mechanism, and target reference procedure are established.

## Inferential limitations

The row-level p-values in band association are screening statistics. They do not account for repeated observations, shared profiles, or possible technical replicates. Benjamini-Hochberg controls the false-discovery rate across the tested bands under its assumptions; it does not correct dependence between observations or establish causality.

Depth summaries are descriptive. Paired profile bootstrap is available as an explicitly conditional exploratory analysis. Confirmatory comparisons may require a repeated-measures or mixed-effects model once the field sampling hierarchy is verified.

## Questions to resolve from source records

- Confirm whether distinct `Amostra` point/plot identifiers are independent sampling units (and whether there are blocks, treatments, or spatial clusters).
- Does `Sample Number` identify one laboratory reference sample with repeated NIR scans, or separate physical/laboratory samples?
- What are the laboratory methods and physical units for TOC and N?
- Were all depth layers sampled within every profile, and what explains absent profile-depth combinations?
- Were the samples collected under a design with blocks, treatments, sites, or temporal repetitions?
