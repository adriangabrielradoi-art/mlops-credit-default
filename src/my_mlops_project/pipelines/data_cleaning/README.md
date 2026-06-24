# Pipeline — Data Cleaning (`data_cleaning`)

## Purpose

Coerce dtypes, drop or impute missing values, deduplicate, and standardize column names.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** pandas
- **Class reference:** --

## Inputs (catalog entries this pipeline consumes)

- validated_data (data/02_intermediate/)

## Outputs (catalog entries this pipeline produces)

- cleaned_data (data/03_primary/)

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_cleaning
```

## Companion notebook

[`notebooks/` — find the entry for `data_cleaning`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/data_cleaning/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
