# Pipeline: Data Quality (`data_quality`)

## Purpose

Validate raw inputs against an expectation suite; fail loudly when assumptions break.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** Great Expectations, Hopsworks (optional)
- **Class reference:** Week 1

## Inputs (catalog entries this pipeline consumes)

- raw_data (data/01_raw/)

## Outputs (catalog entries this pipeline produces)

- validated_data (data/02_intermediate/), ge_report (data/08_reporting/)

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_quality
```

## Companion notebook

[`notebooks/`. Find the entry for `data_quality`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/data_quality/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
