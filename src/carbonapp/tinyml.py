"""TinyML export and benchmark utilities for compact linear NIR models.

The ONNX path deliberately supports linear sklearn pipelines only. Benchmark
figures describe the current host/runtime, not embedded-device performance.
"""
from __future__ import annotations

from pathlib import Path
from time import perf_counter_ns
import tracemalloc

import numpy as np
import pandas as pd
import joblib


def _optional_onnx():
    try:
        import onnx
    except ImportError as exc:
        raise ImportError("Install TinyML dependencies with: pip install -e '.[tinyml]'") from exc
    return onnx


def export_linear_pipeline_onnx(estimator, feature_names: list[str], output_path: str | Path) -> dict:
    """Export a fitted SelectKBest + optional StandardScaler + linear sklearn pipeline."""
    onnx = _optional_onnx()
    steps = getattr(estimator, "named_steps", {})
    if set(steps).difference({"select", "scale", "model"}):
        raise ValueError("Pipeline contains unsupported transformations")
    if "select" not in steps or "model" not in steps:
        raise ValueError("Expected a fitted pipeline with 'select' and 'model' steps")
    selector, model = steps["select"], steps["model"]
    if not hasattr(selector, "get_support") or not hasattr(model, "coef_"):
        raise ValueError("Only fitted linear regression pipelines are supported")
    if len(feature_names) != int(selector.n_features_in_):
        raise ValueError("feature_names length must match the pipeline input feature count")
    selected = selector.get_support(indices=True)
    coefficients = np.asarray(model.coef_, dtype=np.float64).reshape(-1)
    if len(coefficients) != len(selected):
        raise ValueError("Selected feature count does not match linear coefficient count")
    intercept = float(np.asarray(model.intercept_).reshape(-1)[0])
    if "scale" in steps:
        scaler = steps["scale"]
        scales = np.asarray(scaler.scale_, dtype=np.float64)
        means = np.asarray(scaler.mean_, dtype=np.float64)
        coefficients_raw = coefficients / scales[selected]
        intercept -= float(np.sum(coefficients * means[selected] / scales[selected]))
    else:
        coefficients_raw = coefficients
    weights = np.zeros(len(feature_names), dtype=np.float32)
    weights[selected] = coefficients_raw.astype(np.float32)
    bias = np.asarray([intercept], dtype=np.float32)

    helper, TensorProto = onnx.helper, onnx.TensorProto
    input_info = helper.make_tensor_value_info("spectra", TensorProto.FLOAT, [None, len(feature_names)])
    output_info = helper.make_tensor_value_info("prediction", TensorProto.FLOAT, [None, 1])
    initializers = [
        helper.make_tensor("weights", TensorProto.FLOAT, [len(feature_names), 1], weights.tolist()),
        helper.make_tensor("bias", TensorProto.FLOAT, [1], bias.tolist()),
    ]
    matmul = helper.make_node("MatMul", ["spectra", "weights"], ["linear_output"])
    add_bias = helper.make_node("Add", ["linear_output", "bias"], ["prediction"])
    graph = helper.make_graph([matmul, add_bias], "carbonapp_linear_regressor", [input_info], [output_info], initializers)
    model_proto = helper.make_model(graph, producer_name="carbonapp", opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model_proto)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    onnx.save_model(model_proto, output)
    return {
        "path": str(output), "size_bytes": int(output.stat().st_size),
        "n_input_features": len(feature_names), "n_selected_features": int(len(selected)),
        "selected_bands": [feature_names[i] for i in selected],
        "model_type": type(model).__name__,
    }


def quantize_onnx_dynamic(input_path: str | Path, output_path: str | Path) -> dict:
    """Apply ONNX Runtime dynamic INT8 weight quantization."""
    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic
    except ImportError as exc:
        raise ImportError("Install TinyML dependencies with: pip install -e '.[tinyml]'") from exc
    source, output = Path(input_path), Path(output_path)
    if source.resolve() == output.resolve():
        raise ValueError("input_path and output_path must be different")
    if not source.exists():
        raise FileNotFoundError(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    quantize_dynamic(str(source), str(output), weight_type=QuantType.QInt8, op_types_to_quantize=["MatMul"])
    return {
        "path": str(output),
        "float_size_bytes": int(source.stat().st_size),
        "quantized_size_bytes": int(output.stat().st_size),
        "size_reduction_fraction": float(1 - output.stat().st_size / source.stat().st_size),
        "quantization": "dynamic INT8 weights",
    }


def benchmark_onnx_model(
    model_path: str | Path,
    spectra: pd.DataFrame | np.ndarray,
    repeats: int = 100,
    warmup: int = 10,
) -> dict:
    """Measure host CPU latency and Python allocation peak for an ONNX model."""
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise ImportError("Install TinyML dependencies with: pip install -e '.[tinyml]'") from exc
    if repeats < 1 or warmup < 0:
        raise ValueError("repeats must be >= 1 and warmup must be >= 0")
    x = np.asarray(spectra, dtype=np.float32)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    if x.ndim != 2:
        raise ValueError("spectra must be a 1D or 2D numeric array")
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    expected_features = session.get_inputs()[0].shape[1]
    if isinstance(expected_features, int) and x.shape[1] != expected_features:
        raise ValueError(f"Expected {expected_features} features, received {x.shape[1]}")
    for _ in range(warmup):
        session.run(None, {input_name: x})
    durations = []
    tracemalloc.start()
    for _ in range(repeats):
        start = perf_counter_ns()
        session.run(None, {input_name: x})
        durations.append((perf_counter_ns() - start) / 1_000_000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "path": str(model_path), "runtime": "ONNX Runtime CPUExecutionProvider",
        "batch_size": int(x.shape[0]), "repeats": repeats,
        "model_size_bytes": int(Path(model_path).stat().st_size),
        "latency_ms_median": float(np.median(durations)),
        "latency_ms_p95": float(np.percentile(durations, 95)),
        "python_peak_allocated_bytes": int(peak),
        "memory_note": "Python-traced allocations only; not process RSS or embedded-device RAM.",
    }


def benchmark_sklearn_estimator(
    estimator, spectra: pd.DataFrame | np.ndarray, repeats: int = 100, warmup: int = 10,
) -> dict:
    """Measure joblib artifact size and host prediction latency for a fitted estimator."""
    if repeats < 1 or warmup < 0:
        raise ValueError("repeats must be >= 1 and warmup must be >= 0")
    x = np.asarray(spectra, dtype=np.float64)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    if x.ndim != 2:
        raise ValueError("spectra must be a 1D or 2D numeric array")
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        artifact = Path(directory) / "estimator.joblib"
        joblib.dump(estimator, artifact)
        size_bytes = artifact.stat().st_size
    for _ in range(warmup):
        estimator.predict(x)
    durations = []
    tracemalloc.start()
    for _ in range(repeats):
        start = perf_counter_ns()
        estimator.predict(x)
        durations.append((perf_counter_ns() - start) / 1_000_000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "runtime": "scikit-learn host CPU",
        "batch_size": int(x.shape[0]), "repeats": repeats,
        "model_size_bytes": int(size_bytes),
        "latency_ms_median": float(np.median(durations)),
        "latency_ms_p95": float(np.percentile(durations, 95)),
        "python_peak_allocated_bytes": int(peak),
        "memory_note": "Python-traced allocations only; not process RSS or embedded-device RAM.",
    }



def compare_onnx_models(
    reference_path: str | Path,
    candidate_path: str | Path,
    spectra: pd.DataFrame | np.ndarray,
) -> dict:
    """Compare two ONNX artifacts on identical spectra, measuring prediction drift."""
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise ImportError("Install TinyML dependencies with: pip install -e '.[tinyml]'") from exc
    x = np.asarray(spectra, dtype=np.float32)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    if x.ndim != 2:
        raise ValueError("spectra must be a 1D or 2D numeric array")
    reference = ort.InferenceSession(str(reference_path), providers=["CPUExecutionProvider"])
    candidate = ort.InferenceSession(str(candidate_path), providers=["CPUExecutionProvider"])
    ref_input, cand_input = reference.get_inputs()[0], candidate.get_inputs()[0]
    if ref_input.shape[1] != cand_input.shape[1] or (isinstance(ref_input.shape[1], int) and x.shape[1] != ref_input.shape[1]):
        raise ValueError("Reference, candidate and spectra feature dimensions must match")
    y_ref = np.asarray(reference.run(None, {ref_input.name: x})[0], dtype=np.float64).reshape(-1)
    y_candidate = np.asarray(candidate.run(None, {cand_input.name: x})[0], dtype=np.float64).reshape(-1)
    delta = y_candidate - y_ref
    return {
        "n_predictions": int(len(delta)),
        "reference_model_bytes": int(Path(reference_path).stat().st_size),
        "candidate_model_bytes": int(Path(candidate_path).stat().st_size),
        "size_reduction_fraction": float(1 - Path(candidate_path).stat().st_size / Path(reference_path).stat().st_size),
        "prediction_mae": float(np.mean(np.abs(delta))),
        "prediction_rmse": float(np.sqrt(np.mean(delta ** 2))),
        "prediction_max_absolute_error": float(np.max(np.abs(delta))),
        "reference_predictions": y_ref.tolist(),
        "candidate_predictions": y_candidate.tolist(),
        "interpretation": "Prediction drift is measured against the float/reference ONNX artifact. Task accuracy must additionally be evaluated against laboratory targets on held-out groups.",
    }
