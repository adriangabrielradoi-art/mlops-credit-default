# Pipeline — Data Split (`data_split`)

## Purpose

Produce reproducible train/validation/test splits with stratification when appropriate.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** scikit-learn
- **Class reference:** --

## Inputs (catalog entries this pipeline consumes)

- feature_table (data/04_feature/)

## Outputs (catalog entries this pipeline produces)

- `X_train, X_val, X_test, y_train, y_val, y_test` (`data/05_model_input/`).
- **`reference_distribution`** (`data/03_primary/reference_distribution.parquet`)
  — a snapshot of the training feature distribution (column stats,
  quantiles) that `data_drifts` will diff against in production. This
  is the canonical drift baseline; only `data_split` writes it, and it
  is rewritten only when retraining. Its hash is logged to MLflow by
  `model_train` so a drift report can be tied back to the exact run.

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_split
```

## Companion notebook

[`notebooks/` — find the entry for `data_split`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/data_split/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
