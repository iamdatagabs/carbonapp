"""Point-aware soil-profile aggregation and 3D-ready payloads."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import validate_dataset
from .depth import depth_metadata


def _point_depth_table(frame: pd.DataFrame, point_column: str = "Amostra") -> pd.DataFrame:
    validate_dataset(frame)
    required = {point_column, "Profundidade", "Sample Number", "TOC", "N"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing profile columns: {sorted(missing)}")
    # First collapse repeated spectral rows sharing a sample/reference identifier.
    sample_level = (
        frame.groupby([point_column, "Profundidade", "Sample Number"], dropna=False, as_index=False)
        .agg(TOC=("TOC", "mean"), N=("N", "mean"))
    )
    # Then give each unique sample/reference equal weight within point and layer.
    return (
        sample_level.groupby([point_column, "Profundidade"], as_index=False)
        .agg(TOC=("TOC", "mean"), N=("N", "mean"), n_sample_numbers=("Sample Number", "nunique"))
    )


def build_vertical_profile(
    frame: pd.DataFrame,
    point_id: object,
    point_column: str = "Amostra",
    target: str = "TOC",
) -> dict:
    """Return one sampling point's layer-weighted vertical profile."""
    if target not in ("TOC", "N"):
        raise ValueError("target must be TOC or N")
    table = _point_depth_table(frame, point_column)
    subset = table.loc[table[point_column].astype(str) == str(point_id)].copy()
    if subset.empty:
        raise KeyError(f"Unknown sampling point: {point_id}")
    meta = pd.DataFrame(depth_metadata())
    subset = meta.merge(subset, left_on="code", right_on="Profundidade", how="left")
    layers = []
    for row in subset.itertuples(index=False):
        value = getattr(row, target)
        layers.append({
            "code": row.code, "top_cm": int(row.top_cm), "bottom_cm": int(row.bottom_cm),
            "thickness_cm": int(row.thickness_cm), "midpoint_cm": float(row.midpoint_cm),
            "value": None if pd.isna(value) else float(value),
            "n_sample_numbers": 0 if pd.isna(row.n_sample_numbers) else int(row.n_sample_numbers),
        })
    return {
        "point_id": str(point_id), "point_column": point_column, "target": target,
        "depth_extent_cm": [0, 200], "layers": layers,
        "vertical_axis_convention": "depth increases downward; z_cm = -midpoint_cm",
        "spatial_warning": "Amostra identifies sampling points but no geographic coordinates are available. The point axis is categorical, not geographic space.",
    }


def build_profile_summary(
    frame: pd.DataFrame,
    target: str = "TOC",
    point_column: str = "Amostra",
) -> pd.DataFrame:
    """Summarize layer values by giving each sampling point equal weight."""
    if target not in ("TOC", "N"):
        raise ValueError("target must be TOC or N")
    table = _point_depth_table(frame, point_column)
    summary = (
        table.groupby("Profundidade")[target]
        .agg(mean="mean", std="std", median="median", min="min", max="max", n_points="count")
        .reset_index()
    )
    return pd.DataFrame(depth_metadata()).merge(
        summary, left_on="code", right_on="Profundidade", how="left"
    ).drop(columns=["Profundidade"])


def build_profile_3d_payload(
    frame: pd.DataFrame,
    target: str = "TOC",
    point_column: str = "Amostra",
) -> dict:
    """Create a 3D-ready point-by-depth matrix without inventing spatial coordinates."""
    if target not in ("TOC", "N"):
        raise ValueError("target must be TOC or N")
    table = _point_depth_table(frame, point_column)
    points = sorted(table[point_column].dropna().astype(str).unique())
    depths = depth_metadata()
    lookup = table.assign(_point=table[point_column].astype(str)).set_index(["_point", "Profundidade"])
    x, y, z, values = [], [], [], []
    for point_index, point in enumerate(points):
        for layer in depths:
            key = (point, layer["code"])
            value = lookup[target].get(key, np.nan)
            if pd.isna(value):
                continue
            x.append(point_index)
            y.append(float(value))
            z.append(-float(layer["midpoint_cm"]))
            values.append({
                "point_id": point, "depth_code": layer["code"],
                "top_cm": layer["top_cm"], "bottom_cm": layer["bottom_cm"],
                "thickness_cm": layer["thickness_cm"], "value": float(value),
            })
    return {
        "target": target, "point_ids": points,
        "axes": {"x": "sampling point (categorical index; not geographic)", "y": target, "z": "depth (cm; negative downward)"},
        "x": x, "y": y, "z": z, "points": values,
        "depth_intervals": depths,
        "spatial_warning": "This is a point-by-depth visualization, not a geographic 3D soil volume. Spatial coordinates and a sampling design are required for interpolation or volumetric claims.",
    }
