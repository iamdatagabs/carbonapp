import pandas as pd
from fastapi.testclient import TestClient

from carbonapp.api import create_app


def synthetic_csv(path):
    rows = []
    for point in (1, 2):
        for index, depth in enumerate("ABCDEFGHI", start=1):
            for repeat in (1, 2):
                rows.append({
                    "Indice": len(rows), "Amostra": point, "Profundidade": depth,
                    "Sample Number": f"P{point}-{depth}", "TOC": float(index + point),
                    "N": float(index / 10), "r1100": float(index), "r1102": float(index + 0.1),
                })
    pd.DataFrame(rows).to_csv(path, index=False)


def test_api_depth_metadata_and_health(tmp_path):
    client = TestClient(create_app(tmp_path / "missing.csv"))
    assert client.get("/health").json()["status"] == "ok"
    result = client.get("/api/v1/metadata/depths")
    assert result.status_code == 200
    assert result.json()["intervals"][-1]["bottom_cm"] == 200


def test_api_reports_missing_dataset_as_service_unavailable(tmp_path):
    client = TestClient(create_app(tmp_path / "missing.csv"))
    assert client.get("/api/v1/dataset/summary").status_code == 503


def test_api_exposes_summary_point_profile_and_3d_payload(tmp_path):
    path = tmp_path / "spectra.csv"
    synthetic_csv(path)
    client = TestClient(create_app(path))
    summary = client.get("/api/v1/dataset/summary").json()
    assert summary["n_points"] == 2
    assert len(summary["profile_summary"]) == 9
    profile = client.get("/api/v1/profiles/1").json()
    assert profile["layers"][0]["thickness_cm"] == 10
    payload = client.get("/api/v1/profiles-3d").json()
    assert len(payload["point_ids"]) == 2
    assert "not geographic" in payload["spatial_warning"]
