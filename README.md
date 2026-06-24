# MLOps Project — `my_mlops_project`

> Group project for the MLOps course (NOVA IMS, Spring 2026).
> Final submission: **30 June 2026**.

Simulates a real-world ML deployment pipeline: data quality → cleaning →
feature engineering → splitting → training → selection → serving → drift
monitoring. Built on **Kedro** for modular orchestration, with MLflow,
Great Expectations, SHAP, FastAPI, Docker, and Evidently slotted into
their respective stages.

The authoritative project spec is [`MLOps_project.pdf`](MLOps_project.pdf).

---

## Table of Contents

1. [Dataset](#dataset)
2. [Repository layout](#repository-layout)
3. [Environment setup](#environment-setup)
4. [Running the pipelines](#running-the-pipelines)
5. [Running the tests](#running-the-tests)
6. [Notebooks](#notebooks)
7. [Report](#report)
8. [Tooling per pipeline stage](#tooling-per-pipeline-stage)

---

## Dataset

**UCI Credit Card Default** ([id 350](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients)) — 30,000 Taiwanese credit-card clients, fetched reproducibly via `ucimlrepo`.

- **Target:** `default` (default next month), binary, ~22% positive (imbalanced).
- **Features:** 23 across four groups — demographic (`LIMIT_BAL`, `SEX`, `EDUCATION`, `MARRIAGE`, `AGE`), repayment status (`PAY_0`/`PAY_2..6`), bill amounts (`BILL_AMT1..6`), previous payments (`PAY_AMT1..6`).
- **Primary metric:** ROC-AUC (threshold-free; honest on the class imbalance); also report PR-AUC / F1 / confusion matrix.
- **Why:** rich enough for real feature engineering, genuine data-quality quirks (undocumented category codes), and a credible drift story (PSI is built for credit scorecards).

## Repository layout

```
Project/
├── conf/             Kedro configuration (catalog, parameters, globals)
│   ├── base/         Shared across environments
│   └── local/        Per-developer overrides (gitignored)
├── data/             Kedro 8-layer data convention
│   ├── 01_raw/       Untouched inputs
│   ├── 02_intermediate/  Type-coerced, deduped
│   ├── 03_primary/   Domain-validated
│   ├── 04_feature/   Engineered features
│   ├── 05_model_input/   Train/val/test splits
│   ├── 06_models/    Serialized models
│   ├── 07_model_output/  Predictions
│   └── 08_reporting/ SHAP plots, drift reports, metrics
├── docs/             Architecture notes, ADRs
├── notebooks/        Exploration + per-pipeline narrative notebooks
├── report/           6-page report skeleton + final PDF
├── src/my_mlops_project/
│   ├── settings.py
│   ├── pipeline_registry.py
│   └── pipelines/
│       ├── data_quality/
│       ├── data_cleaning/
│       ├── data_feat_engineering/
│       ├── data_split/
│       ├── model_train/
│       ├── model_selection/
│       ├── model_predict/
│       └── data_drifts/
└── tests/            Pytest suite mirroring pipelines/
```

## Environment setup

This project uses **uv**, not conda. The locked dependency tree lives
in [`uv.lock`](uv.lock).

```powershell
# Install uv (one-time, if not already)
# https://docs.astral.sh/uv/getting-started/installation/

# Sync the locked deps into .venv-mlops
$env:UV_PROJECT_ENVIRONMENT = ".venv-mlops"
uv sync

# Activate (PowerShell)
.\.venv-mlops\Scripts\Activate.ps1
```

If `uv sync` ever complains about Python version, install Python 3.13
via [python.org](https://www.python.org/downloads/) (>=3.13 is pinned in
`pyproject.toml`).

## Running the pipelines

The pipeline runs **two equivalent ways** — pick whichever you prefer.

### Option A — from a notebook (no terminal needed)

1. Open [`notebooks/00_main.ipynb`](notebooks/00_main.ipynb).
2. Select the **`.venv-mlops`** kernel (top-right kernel picker) — this is the only setup step.
3. **Run All.** It runs the full pipeline via `KedroSession.run()` (identical to `kedro run`) and prints a summary of each stage's output.

### Option B — from the terminal

The uv `.exe` shims are broken, so invoke through the venv's Python with `python -m`:

```powershell
# Full pipeline end-to-end
.\.venv-mlops\Scripts\python.exe -m kedro run

# A single sub-pipeline (each is independently runnable — e.g. only the drift check)
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_quality
.\.venv-mlops\Scripts\python.exe -m kedro run --pipeline data_drifts
```

Both produce the same layered artifacts under `data/` and log to MLflow.

## Running the tests

```powershell
.\.venv-mlops\Scripts\python.exe -m pytest tests/ -v
```

## Notebooks

See [`notebooks/00_main.ipynb`](notebooks/00_main.ipynb) — the master
notebook with a Table of Contents linking to one notebook per pipeline
stage. Each per-pipeline notebook has its own TOC and is the narrative
companion to the corresponding `src/my_mlops_project/pipelines/<name>/`
module.

## Report

The 6-page report skeleton lives in
[`report/REPORT_OUTLINE.md`](report/REPORT_OUTLINE.md). It enumerates
every section required by the project PDF.

## Tooling per pipeline stage

| Stage                   | Tool(s)                       | Class week |
| ----------------------- | ----------------------------- | ---------- |
| `data_quality`          | Great Expectations, Hopsworks | 1          |
| `data_cleaning`         | pandas                        | —          |
| `data_feat_engineering` | Hopsworks feature store       | 1          |
| `data_split`            | scikit-learn                  | —          |
| `model_train`           | MLflow + Optuna               | 2          |
| `model_selection`       | MLflow registry + SHAP        | 2 / 6      |
| `model_predict`         | FastAPI + Docker              | 4 / 5      |
| `data_drifts`           | Evidently                     | 6          |

Pipeline orchestration: **Kedro** (with optional Prefect overlay later).
