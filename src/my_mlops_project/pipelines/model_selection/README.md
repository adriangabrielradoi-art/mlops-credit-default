# Pipeline: Model Selection (`model_selection`)

## Purpose

Compare candidate runs in MLflow, register the winner, and emit SHAP explainability.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** MLflow registry, SHAP
- **Class reference:** Week 2 / 6

## Inputs (catalog entries this pipeline consumes)

- trained_models (data/06_models/), X_val, y_val

## Outputs (catalog entries this pipeline produces)

- `champion_model` (`data/06_models/`). Also tagged in the MLflow
  registry; downstream services (FastAPI) load from the registry, not
  the pickle file.
- `shap_summary.png` (`data/08_reporting/`), the **global** SHAP
  summary across the validation set. Per-prediction SHAP values are
  emitted by `model_predict` (Week 6 monitoring level 3), not here.

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline model_selection
```

## Companion notebook

[`notebooks/`. Find the entry for `model_selection`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/model_selection/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
