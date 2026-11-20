import pandas as pd
from fastapi.testclient import TestClient

from carbonapp.api import create_app


def test_api_depth_metadata_and_health(tmp_path):
    client = TestClient(create_app(tmp_path / "missing.csv"))
    assert client.get("/health").json()["status"] == "ok"
    result = client.get("/api/v1/metadata/depths")
    assert result.status_code == 200
    assert result.json()["intervals"][-1]["bottom_cm"] == 200


def test_api_reports_missing_dataset_as_service_unavailable(tmp_path):
    client = TestClient(create_app(tmp_path / "missing.csv"))
    assert client.get("/api/v1/dataset/summary").status_code == 503
