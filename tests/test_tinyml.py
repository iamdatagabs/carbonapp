import numpy as np
import pytest
from sklearn.linear_model import HuberRegressor
from carbonapp.model_comparison import build_model_pipeline
from carbonapp.tinyml import benchmark_sklearn_estimator, export_linear_pipeline_onnx


def test_sklearn_benchmark_reports_size_and_latency():
    rng = np.random.default_rng(9)
    x = rng.normal(size=(40, 6))
    y = 2 * x[:, 0] - x[:, 1]
    model = build_model_pipeline("huber", k=4).fit(x, y)
    result = benchmark_sklearn_estimator(model, x[:5], repeats=3, warmup=1)
    assert result["model_size_bytes"] > 0
    assert result["latency_ms_median"] >= 0
    assert result["batch_size"] == 5


def test_onnx_export_matches_fitted_linear_pipeline(tmp_path):
    onnx = pytest.importorskip("onnx")
    pytest.importorskip("onnxruntime")
    rng = np.random.default_rng(19)
    x = rng.normal(size=(50, 7))
    y = 3 * x[:, 0] - 0.7 * x[:, 3] + 0.2
    model = build_model_pipeline("huber", k=5).fit(x, y)
    path = tmp_path / "huber.onnx"
    result = export_linear_pipeline_onnx(model, [f"r{1100+2*i}" for i in range(7)], path)
    import onnxruntime as ort
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    actual = session.run(None, {session.get_inputs()[0].name: x[:8].astype(np.float32)})[0].ravel()
    expected = model.predict(x[:8])
    assert result["size_bytes"] > 0
    assert np.allclose(actual, expected, atol=2e-4)
