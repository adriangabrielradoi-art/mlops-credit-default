# Pipeline — Data Drift Monitoring (`data_drifts`)

## Purpose

Compare the production data sample against the training reference; report drift via Evidently.

## Position in the end-to-end flow

See the full ordering in the [project CLAUDE.md](../../../../CLAUDE.md#4-pipeline-order-from-the-pdf).

## Tooling

- **Primary:** Evidently for the consolidated HTML report.
- **Statistical tests done explicitly** (Week 6 lecture):
  - **PSI** per feature — interpret with the bands `<0.1` stable,
    `<0.2` moderate, `≥0.2` significant drift.
  - **KS test** for numeric features (CDF-based, p-value driven).
  - **JS divergence** for categorical features (symmetric, handles zero
    probabilities — preferred over KL).
  - **PCA reconstruction error** for *multivariate* drift (univariate
    tests miss correlated shifts — Week 6 lecture slide 26). The PCA
    object itself is fit once in `model_train` and cached at
    `data/06_models/drift_pca.pkl`.
  - Optional: **ADWIN** (sliding-window) for concept drift on the
    prediction stream.
- **Class reference:** Week 6.

## Inputs (catalog entries this pipeline consumes)

- `reference_distribution` (`data/03_primary/`, written by `data_split`)
- `current_data` (`data/01_raw/` sample or live)
- `predictions` (`data/07_model_output/`, written by `model_predict`)
- `drift_pca` (`data/06_models/drift_pca.pkl`, fit in `model_train`)

## Outputs (catalog entries this pipeline produces)

- `psi_per_feature` (`data/08_reporting/psi.csv`) — table with PSI band.
- `drift_report.html` (`data/08_reporting/`) — Evidently consolidated.
- `drift_flags` (`data/07_model_output/drift_flags.json`) — boolean per
  feature + overall, used by the retrain-trigger hook.
- `monitoring_dashboard.html` (`data/08_reporting/`) — **final node**
  aggregates GE summary, training metrics, SHAP, drift table. This is
  the single artifact the grader will open.

## Run this pipeline in isolation

```powershell
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_drifts
```

## Companion notebook

[`notebooks/` — find the entry for `data_drifts`](../../../../notebooks/)

## TODOs before this pipeline is production-ready

- [ ] Replace `placeholder_node` in `nodes.py` with the real
      transformation(s).
- [ ] Fill in the `create_pipeline` body in `pipeline.py` and bind
      to real catalog entries declared in `conf/base/catalog.yml`.
- [ ] Add a unit test under `tests/pipelines/data_drifts/`.
- [ ] Add a row in this README documenting any non-obvious assumptions.
