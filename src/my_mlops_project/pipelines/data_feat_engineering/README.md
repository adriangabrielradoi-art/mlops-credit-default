# Pipeline — Feature Engineering (`data_feat_engineering`)

## Purpose

Derive model-ready features from cleaned data and (optionally) push them to a feature store.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** Hopsworks feature store, pandas
- **Class reference:** Week 1

## Inputs (catalog entries this pipeline consumes)

- cleaned_data (data/03_primary/)

## Outputs (catalog entries this pipeline produces)

- feature_table (data/04_feature/)

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_feat_engineering
```

## Companion notebook

[`notebooks/` — find the entry for `data_feat_engineering`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/data_feat_engineering/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
