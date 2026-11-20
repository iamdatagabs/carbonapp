# Reproducible end-to-end execution

Install the complete research runtime:

```bash
pip install -e ".[dev,api,tinyml]"
```

Run the TOC workflow:

```bash
python scripts/run_research_pipeline.py \
  --data "data/raw/[quad]base_nirs_refletancia.csv" \
  --output reports/latest-run \
  --seed 42 --splits 5
```

The script creates a dataset SHA-256 manifest, nested grouped CV results at both reference and sampling-point levels, group-aware interpretability tables, split-conformal diagnostics, point-weighted depth summaries, a 3D-ready profile payload, and a float-vs-INT8 ONNX comparison on a held-out group split.

The exported TinyML model is chosen by the most frequent inner-CV selection among the linear families supported by the current ONNX exporter (Huber, Elastic Net and Bayesian Ridge). It may differ from the overall nested-CV winner if Extra Trees is selected more often. The chosen linear model is refitted only on the training side of a separate grouped holdout. The held-out groups are used only for model/quantization comparison and benchmarking. The script intentionally does not claim that host measurements represent embedded-device performance.

This pipeline can be computationally demanding because it runs nested CV for four model families. It writes results to the output directory and should be run against the original dataset only after laboratory metadata and group semantics have been checked. N is summarized as exploratory only; predictive evaluation is restricted to TOC.
