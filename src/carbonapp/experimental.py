"""Sampling-point audit and cluster-aware paired depth contrasts.

`Amostra` identifies the numeric sampling point/plot. `Profundidade` identifies
the vertical layer (A-I) within that point. `Sample Number` is a lower-level
spectral/laboratory identifier; its technical-replicate meaning must still be
confirmed before collapsing repeated rows.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .data import spectral_columns, validate_dataset
from .depth import DEPTH_BY_CODE


def audit_sample_structure(
    frame: pd.DataFrame,
    profile_column: str = "Amostra",
    replicate_column: str = "Sample Number",
    depth_column: str = "Profundidade",
    targets: tuple[str, ...] = ("TOC", "N"),
) -> dict[str, Any]:
    """Describe point-by-depth nesting, repeated IDs, and target consistency.

`Amostra` is the point/plot identifier; `Profundidade` is the within-point
layer code. Legacy `n_profiles` and `profile_column` keys are retained for
backward compatibility and refer to points, not separate profile objects.
"""
    validate_dataset(frame)
    for column in (profile_column, replicate_column, depth_column):
        if column not in frame:
            raise ValueError(f"Missing design column: {column}")
    if frame[[profile_column, replicate_column, depth_column]].isna().any().any():
        raise ValueError("Design identifiers cannot contain missing values")
    if any(target not in ("TOC", "N") for target in targets):
        raise ValueError("targets must contain only TOC and/or N")

    by_replicate = frame.groupby(replicate_column, dropna=False)
    inconsistent = {}
    for target in targets:
        counts = by_replicate[target].nunique(dropna=False)
        inconsistent[target] = int((counts > 1).sum())

    replicate_nesting = by_replicate.agg(
        profiles=(profile_column, "nunique"),
        depths=(depth_column, "nunique"),
        rows=(depth_column, "size"),
    )
    profile_depth = frame.groupby(
        [profile_column, depth_column], observed=True
    ).size()

    return {
        "n_rows": int(len(frame)),
        "n_points": int(frame[profile_column].nunique()),
        "n_profiles": int(frame[profile_column].nunique()),
        "n_replicate_ids": int(frame[replicate_column].nunique()),
        "n_replicate_ids_repeated": int((by_replicate.size() > 1).sum()),
        "n_profile_depth_combinations": int(profile_depth.size),
        "n_duplicate_profile_depth_combinations": int((profile_depth > 1).sum()),
        "replicate_ids_spanning_multiple_profiles": int(
            (replicate_nesting["profiles"] > 1).sum()
        ),
        "replicate_ids_spanning_multiple_depths": int(
            (replicate_nesting["depths"] > 1).sum()
        ),
        "inconsistent_target_ids": inconsistent,
        "profile_column": profile_column,
        "replicate_column": replicate_column,
        "depth_column": depth_column,
        "depth_codes_present": sorted(
            frame[depth_column].dropna().unique().tolist(),
            key=lambda code: DEPTH_BY_CODE[code].top_cm,
        ),
    }


def aggregate_replicate_rows(
    frame: pd.DataFrame,
    replicate_column: str = "Sample Number",
    profile_column: str = "Amostra",
    depth_column: str = "Profundidade",
) -> pd.DataFrame:
    """Collapse repeated rows per Sample Number after checking metadata/targets.

    Spectral bands are averaged. Targets and design identifiers must be
    identical within a replicate ID; otherwise aggregation is rejected.
    This operation is appropriate only if repeated IDs are confirmed technical
    replicate scans of the same laboratory reference.
    """
    validate_dataset(frame)
    required = (replicate_column, profile_column, depth_column, "TOC", "N")
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    if frame[[replicate_column, profile_column, depth_column]].isna().any().any():
        raise ValueError("Replicate, profile, and depth identifiers cannot be missing")

    invariant = [profile_column, depth_column, "TOC", "N"]
    counts = frame.groupby(replicate_column)[invariant].nunique(dropna=False)
    if (counts > 1).any().any():
        raise ValueError(
            "A replicate ID maps to conflicting profile, depth, TOC, or N values"
        )

    bands = spectral_columns(frame)
    metadata = frame.groupby(replicate_column, sort=False)[invariant].first()
    spectra = frame.groupby(replicate_column, sort=False)[bands].mean()
    result = metadata.join(spectra).reset_index()
    return result[[replicate_column, *invariant, *bands]]


def paired_depth_bootstrap(
    frame: pd.DataFrame,
    target: str = "TOC",
    depth_a: str = "A",
    depth_b: str = "B",
    profile_column: str = "Amostra",
    replicate_column: str = "Sample Number",
    n_bootstrap: int = 4000,
    confidence: float = 0.95,
    random_state: int = 42,
) -> dict[str, Any]:
    """Estimate paired depth difference by resampling whole sampling points.

    Difference is depth_b minus depth_a. Repeated scan rows are first collapsed
    within Sample Number, then Sample Numbers are averaged within point/depth.
    Only points observed at both requested depths contribute. The percentile
    interval resamples points as clusters; this assumes distinct Amostra IDs
    are independent sampling units under the actual field design.
    """
    if target not in ("TOC", "N"):
        raise ValueError("target must be 'TOC' or 'N'")
    if depth_a not in DEPTH_BY_CODE or depth_b not in DEPTH_BY_CODE:
        raise ValueError("depth_a and depth_b must be valid depth codes A-I")
    if depth_a == depth_b:
        raise ValueError("Choose two different depth codes")
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    collapsed = aggregate_replicate_rows(
        frame, replicate_column, profile_column
    )
    layer_means = collapsed.groupby(
        [profile_column, "Profundidade"], observed=True
    )[target].mean().unstack("Profundidade")

    if depth_a not in layer_means or depth_b not in layer_means:
        raise ValueError("One or both requested depths are absent")
    paired = layer_means[[depth_a, depth_b]].dropna()
    if len(paired) < 2:
        raise ValueError(
            "At least two profiles must contain both requested depth layers"
        )

    differences = (paired[depth_b] - paired[depth_a]).to_numpy(dtype=float)
    rng = np.random.default_rng(random_state)
    indices = rng.integers(0, len(differences), size=(n_bootstrap, len(differences)))
    bootstrap_means = differences[indices].mean(axis=1)
    alpha = 1.0 - confidence
    lower, upper = np.quantile(
        bootstrap_means, [alpha / 2.0, 1.0 - alpha / 2.0]
    )

    return {
        "target": target,
        "contrast": f"{depth_b} - {depth_a}",
        "depth_a_interval_cm": [
            DEPTH_BY_CODE[depth_a].top_cm, DEPTH_BY_CODE[depth_a].bottom_cm
        ],
        "depth_b_interval_cm": [
            DEPTH_BY_CODE[depth_b].top_cm, DEPTH_BY_CODE[depth_b].bottom_cm
        ],
        "point_column": profile_column,
        "profile_column": profile_column,
        "n_paired_points": int(len(differences)),
        "n_paired_profiles": int(len(differences)),
        "mean_paired_difference": float(np.mean(differences)),
        "median_paired_difference": float(np.median(differences)),
        "confidence_level": confidence,
        "bootstrap_ci": [float(lower), float(upper)],
        "n_bootstrap": int(n_bootstrap),
        "random_state": int(random_state),
        "resampling_unit": f"sampling point ({profile_column})",
        "interpretation": (
            "Exploratory point-cluster bootstrap interval. Treat as confirmatory only "
            "if distinct sampling points are independent units and the "
            "sampling design supports this contrast."
        ),
    }
