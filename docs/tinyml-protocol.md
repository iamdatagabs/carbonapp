# TinyML export and benchmark protocol

## Supported first target

The first deployable path exports fitted linear regression pipelines containing `SelectKBest`, optional `StandardScaler`, and a linear estimator (Huber, Elastic Net, or Bayesian Ridge) to a compact ONNX Gemm graph. The selector and scaler are algebraically folded into one full-input coefficient vector. Tree ensembles are not exported by this first implementation.

Install optional dependencies:

```bash
pip install -e ".[tinyml]"
```

## Quantization and measurements

- Dynamic INT8 quantization compresses ONNX weights; it is not a guarantee of lower latency on every CPU.
- Compare float and quantized prediction error on a held-out dataset before deployment.
- The benchmark records artifact bytes, median/p95 host CPU latency and Python-traced peak allocations.
- Python-traced allocations are not process RSS, peak native memory, flash usage on a microcontroller, or energy consumption.
- No embedded-device, RAM, flash, or energy claims should be made until the artifact is measured on the target hardware.

## Scientific safeguards

Export only a model configuration selected and evaluated under the grouped validation protocol. Keep the test groups untouched during quantization calibration/comparison. Report prediction agreement and task metrics alongside size and latency. Preserve original float model, quantized artifact, dataset version, feature order, selected wavelengths, and random seed.

## Example

```python
from carbonapp.data import load_dataset, spectral_columns
from carbonapp.model_comparison import build_model_pipeline
from carbonapp.tinyml import export_linear_pipeline_onnx, quantize_onnx_dynamic, benchmark_onnx_model

df = load_dataset("data/raw/[quad]base_nirs_refletancia.csv")
bands = spectral_columns(df)
model = build_model_pipeline("huber", k=40).fit(df[bands], df["TOC"])
export_linear_pipeline_onnx(model, bands, "models/onnx/toc_huber.onnx")
quantize_onnx_dynamic("models/onnx/toc_huber.onnx", "models/onnx/toc_huber_int8.onnx")
```
