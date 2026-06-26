# Pipeline: Model Prediction & Serving (`model_predict`)

## Purpose

Generate predictions on hold-out / fresh data; expose the champion model behind a FastAPI service in a Docker container.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** FastAPI (the inference service), Docker (the runtime).
- **Class reference:** Week 4 / 5.
- **Patterns from Week 5 lecture to apply:**
  - **Two prediction modes** , `predict_batch` (consumes `X_test`,
    writes `predictions.parquet`) and `predict_online` (FastAPI
    handler). Same scoring function, different drivers.
  - **Load champion at startup, not at build time.** The FastAPI app
    reads the champion URI from the MLflow registry on startup. Models are NOT baked into the image (Week 5 slide 35).
  - **Image tagging:** tag by git SHA, never `:latest`. The build
    script lives at `scripts/build_image.ps1`.
  - **Container scope:** the Docker image ships *only* the serving
    path (FastAPI + scoring), not the whole Kedro project. One
    process per container.
- **Per-prediction explainability** (Week 6 lecture, monitoring
  level 3): `log_shap_per_prediction` writes individual SHAP values to
  `data/08_reporting/shap_predictions.parquet` so the global SHAP
  summary from `model_selection` can be drilled into per-row.
- **Decision logging:** `log_decision_metrics` writes
  `data/08_reporting/decision_log.csv` per run (threshold used,
  FP/TN counts). Feeds the Week 6 mitigation playbook.

## Inputs (catalog entries this pipeline consumes)

- `champion_model` (loaded via MLflow registry URI, not the pickle)
- `X_test` (for `predict_batch`) or HTTP payload (for `predict_online`)

## Outputs (catalog entries this pipeline produces)

- `predictions` (`data/07_model_output/predictions.parquet`)
- `shap_predictions` (`data/08_reporting/shap_predictions.parquet`)
- `decision_log` (`data/08_reporting/decision_log.csv`)
- `/predict` HTTP endpoint (served by the Docker container)

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline model_predict
```

## Companion notebook

[`notebooks/`. Find the entry for `model_predict`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/model_predict/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
