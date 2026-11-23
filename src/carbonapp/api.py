"""Optional FastAPI application exposing the CarbonApp scientific core."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from .data import load_dataset
from .depth import depth_metadata
from .profile import build_profile_3d_payload, build_profile_summary, build_vertical_profile


def create_app(data_path: str | Path | None = None):
    """Create the API; dataset loading is lazy so health checks work without data."""
    try:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:
        raise ImportError("Install API dependencies with: pip install -e '.[api]'") from exc

    resolved_path = Path(data_path or os.getenv("CARBONAPP_DATA_PATH", "data/raw/[quad]base_nirs_refletancia.csv"))
    app = FastAPI(
        title="CarbonApp Research API",
        version="0.1.0",
        description="Reproducible soil NIR spectroscopy, statistics and vertical-profile endpoints.",
    )

    cors_origins = [origin.strip() for origin in os.getenv("CARBONAPP_CORS_ORIGINS", "").split(",") if origin.strip()]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=cors_origins, allow_credentials=False,
            allow_methods=["GET"], allow_headers=["*"],
        )

    def dataset():
        if not resolved_path.exists():
            raise HTTPException(status_code=503, detail=f"Dataset not found at {resolved_path}")
        try:
            return load_dataset(resolved_path)
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=422, detail=f"Dataset validation failed: {exc}") from exc

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "service": "CarbonApp Research API",
            "version": app.version,
            "status": "ok",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "dataset_configured": resolved_path.is_file(),
            "dataset_size_bytes": resolved_path.stat().st_size if resolved_path.is_file() else None,
        }

    @app.get("/api/v1/metadata/depths")
    def depths():
        return {"depth_extent_cm": [0, 200], "intervals": depth_metadata()}

    @app.get("/api/v1/dataset/summary")
    def summary(target: str = Query(default="TOC", pattern="^(TOC|N)$")):
        frame = dataset()
        profile_summary = build_profile_summary(frame, target)
        profile_records = profile_summary.astype(object).where(pd.notna(profile_summary), None).to_dict(orient="records")
        return {
            "n_rows": int(len(frame)),
            "n_points": int(frame["Amostra"].nunique()),
            "n_sample_numbers": int(frame["Sample Number"].nunique()),
            "n_spectral_bands": int(len([c for c in frame.columns if c.startswith("r") and c[1:].isdigit()])),
            "target": target,
            "profile_summary": profile_records,
        }

    @app.get("/api/v1/profiles/{point_id}")
    def profile(point_id: str, target: str = Query(default="TOC", pattern="^(TOC|N)$")):
        try:
            return build_vertical_profile(dataset(), point_id, target=target)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/profiles-3d")
    def profiles_3d(target: str = Query(default="TOC", pattern="^(TOC|N)$")):
        return build_profile_3d_payload(dataset(), target)

    return app
