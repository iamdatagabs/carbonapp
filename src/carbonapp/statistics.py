"""Exploratory descriptive statistics for soil targets and NIR spectra.

Inferential p-values for band-wise associations are screening statistics: the
current implementation does not model within-profile dependence. Interpret them
as exploratory and use the Benjamini-Hochberg q-values to control multiplicity.
"""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from .data import spectral_columns, validate_dataset
from .depth import depth_metadata

WAVELENGTH_PATTERN = re.compile(r"^r(\d+)$")


def _numeric_summary(values: pd.Series) -> dict[str, float | int]:
    """Return a consistent set of descriptive statistics without assuming units."""
    x = pd.to_numeric(values, errors="coerce").dropna()
    if x.empty:
        raise ValueError("Cannot summarize an empty numeric series")
    return {
        "n": int(x.size),
        "mean": float(x.mean()),
        "std": float(x.std(ddof=1)) if x.size > 1 else 0.0,
        "median": float(x.median()),
        "q1": float(x.quantile(0.25)),
        "q3": float(x.quantile(0.75)),
        "min": float(x.min()),
        "max": float(x.max()),
    }


def describe_targets(
    frame: pd.DataFrame, targets: Iterable[str] = ("TOC", "N")
) -> dict[str, dict[str, float | int]]:
    """Describe stored target values; no physical units are inferred."""
    validate_dataset(frame)
    result = {}
    for target in targets:
        if target not in ("TOC", "N"):
            raise ValueError("Only TOC and N are supported targets")
        result[target] = _numeric_summary(frame[target])
    return result


def describe_by_depth(
    frame: pd.DataFrame, targets: Iterable[str] = ("TOC", "N")
) -> pd.DataFrame:
    """Summarize targets by the authoritative, unequal-thickness depth layers."""
    validate_dataset(frame)
    supported = tuple(targets)
    if not supported or any(target not in ("TOC", "N") for target in supported):
        raise ValueError("targets must contain TOC and/or N")

    metadata = pd.DataFrame(depth_metadata())
    rows: list[dict] = []
    for code, group in frame.groupby("Profundidade", sort=False, observed=True):
        layer = metadata.loc[metadata["code"] == code].iloc[0].to_dict()
        for target in supported:
            rows.append({
                **layer,
                "target": target,
                **_numeric_summary(group[target]),
            })
    return pd.DataFrame(rows).sort_values(
        ["top_cm", "target"], kind="stable"
    ).reset_index(drop=True)


def describe_spectra(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize reflectance distribution at each wavelength (nm)."""
    validate_dataset(frame)
    rows = []
    for column in spectral_columns(frame):
        wavelength = int(WAVELENGTH_PATTERN.match(column).group(1))
        rows.append({
            "wavelength_nm": wavelength,
            **_numeric_summary(frame[column]),
        })
    return pd.DataFrame(rows).sort_values("wavelength_nm").reset_index(drop=True)


def _benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values, returned in original order."""
    p = np.asarray(p_values, dtype=float)
    adjusted = np.full(p.shape, np.nan, dtype=float)
    valid = np.isfinite(p)
    if not valid.any():
        return adjusted
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    m = ranked.size
    q = ranked * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    restored = np.empty(m, dtype=float)
    restored[order] = np.minimum(q, 1.0)
    adjusted[valid] = restored
    return adjusted


def target_band_associations(
    frame: pd.DataFrame, target: str = "TOC", method: str = "spearman"
) -> pd.DataFrame:
    """Rank/linear association of each wavelength with a target plus BH q-values.

    P-values are conventional row-independent tests and are not cluster-aware.
    Because samples may share profiles or laboratory references, these values
    are exploratory screening outputs, not confirmatory inference.
    """
    validate_dataset(frame)
    if target not in ("TOC", "N"):
        raise ValueError("target must be 'TOC' or 'N'")
    if method not in ("pearson", "spearman"):
        raise ValueError("method must be 'pearson' or 'spearman'")

    y = frame[target].astype(float).to_numpy()
    rows = []
    for column in spectral_columns(frame):
        x = frame[column].astype(float).to_numpy()
        if np.ptp(x) == 0 or np.ptp(y) == 0:
            coefficient, p_value = np.nan, np.nan
        elif method == "pearson":
            coefficient, p_value = pearsonr(x, y)
        else:
            coefficient, p_value = spearmanr(x, y)
        rows.append({
            "wavelength_nm": int(WAVELENGTH_PATTERN.match(column).group(1)),
            "band": column,
            "target": target,
            "method": method,
            "n": int(len(frame)),
            "coefficient": float(coefficient),
            "p_value": float(p_value),
        })

    result = pd.DataFrame(rows)
    result["q_value_bh"] = _benjamini_hochberg(result["p_value"].to_numpy())
    return result.sort_values(
        "coefficient", key=lambda s: s.abs(), ascending=False, na_position="last"
    ).reset_index(drop=True)
