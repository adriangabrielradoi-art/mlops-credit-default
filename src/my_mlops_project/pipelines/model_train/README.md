# Pipeline: Model Training (`model_train`)

## Purpose

Train one or more candidate models, tune hyperparameters, and log everything to MLflow.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** MLflow, Optuna
- **Class reference:** Week 2

## Inputs (catalog entries this pipeline consumes)

- X_train, y_train, X_val, y_val (data/05_model_input/)

## Outputs (catalog entries this pipeline produces)

- trained_models (data/06_models/), mlflow_run_ids (data/08_reporting/)

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline model_train
```

## Companion notebook

[`notebooks/`. Find the entry for `model_train`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/model_train/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
