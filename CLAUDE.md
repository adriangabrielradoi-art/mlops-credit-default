# MLOps Project — Local Claude Instructions

These instructions **extend and override** the global
[`Masters Program/CLAUDE.md`](../../CLAUDE.md) and the course-level
[`Masters Program/ML Ops/CLAUDE.md`](../CLAUDE.md). More specific overrides
more general. The Teaching Contract (global) and the documentation style
(course level §2) still apply in full and are not repeated here.

---

## 1. Source of truth

The authoritative spec for this project is
[`MLOps_project.pdf`](MLOps_project.pdf). If anything in this file ever
contradicts the PDF, the PDF wins — flag it.

## 2. Project environment

- **Working venv:** `.venv-mlops/` (Python 3.13.7, uv 0.11.8). Do not
  rename, recreate, or replace it without explicit user confirmation.
- **Empty `.venv/`:** stray from a default uv command — leave it alone.
- **Invocation:**

  ```powershell
  .\.venv-mlops\Scripts\python.exe -m <module>
  ```

  Or with uv (auto-discovers `.venv-mlops` when `VIRTUAL_ENV` is set):

  ```powershell
  $env:VIRTUAL_ENV = ".\.venv-mlops"; uv run python -m <module>
  ```

  Never run bare `python`.

## 3. Project identity

- **Package name (Python module):** `my_mlops_project` (matches `name` in
  [`pyproject.toml`](pyproject.toml) with hyphens → underscores).
- **Dataset:** *not yet chosen.* Every notebook and pipeline contains
  `TODO(dataset)` markers. Do not invent a dataset silently — ask first.
- **Group project**, 3-5 students. Each pipeline folder under
  `src/my_mlops_project/pipelines/` is one ownership boundary.

## 4. Pipeline order + tooling (from the PDF and Weeks 1-6 lectures)

The 8 sub-pipelines live under `src/my_mlops_project/pipelines/` and run in
this canonical order; each is independently runnable.

```
data_quality
  → data_cleaning
    → data_feat_engineering
      → data_split
        → model_train
          → model_selection
            → model_predict
              → data_drifts
```

| Pipeline                | Class week | Primary tooling                                                | Notable techniques (per lectures)                          |
| ----------------------- | ---------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| `data_quality`          | Week 1     | Great Expectations, Hopsworks                                  | Expectation suites; fail-loud assertions                   |
| `data_cleaning`         | —          | pandas                                                         | Dtype coercion, dedup, null handling                       |
| `data_feat_engineering` | Week 1     | Hopsworks feature store                                        | Feature groups, feature views                              |
| `data_split`            | —          | scikit-learn                                                   | **Also writes** `reference_distribution` for drift baseline |
| `model_train`           | Week 2     | MLflow + Optuna                                                | Run logging, HPO sweeps                                    |
| `model_selection`       | Week 2 / 6 | MLflow registry + SHAP                                         | Champion tagging; SHAP global summary                      |
| `model_predict`         | Week 4 / 5 | FastAPI + Docker                                               | Batch + online inference; load champion from registry at startup; tag images by git SHA (never `:latest`); per-prediction SHAP logging |
| `data_drifts`           | Week 6     | Evidently + statistical tests                                  | PSI (bands <0.1 / <0.2 / ≥0.2), KS (continuous), JS (categorical), PCA reconstruction error (multivariate); ADWIN optional; unified `monitoring_dashboard.html` is the final artifact |

Cross-cutting concerns that touch multiple pipelines:
- **MLflow** tracks `model_train` → tags champion in `model_selection` →
  logs production inference in `model_predict`.
- **`data/08_reporting/`** is the gather-point for the 6-page report
  artifacts (GE JSON, SHAP plots, drift HTML, monitoring dashboard).

## 5. Notebook workflow (project-specific paths)

Per the global notebook rules:

1. Export fresh before reviewing:

   ```powershell
   .\.venv-mlops\Scripts\python.exe -m jupyter nbconvert --to script `
     "notebooks\<notebook_name>.ipynb" --stdout 2>$null
   ```

2. Before adding any cell: read the full notebook, check for duplicates,
   propose the location, wait for approval.
3. Never silently insert cells.

## 6. Coaching roadmap

The 5-sprint self-coaching plan lives at
[`docs/ROADMAP.md`](docs/ROADMAP.md). It maps each pipeline to a sprint
week, a lecture/lab to re-read first, the smallest first code unit, and
self-checks. Re-read sections 1 and 6 of the roadmap before every coding
session.

## 7. Report skeleton

The 6-page report outline lives at
[`report/REPORT_OUTLINE.md`](report/REPORT_OUTLINE.md). Section 5
(production discussion) absorbs lecture content that doesn't translate to
code: K8s/Kubeflow scaling, canary/shadow/A-B deployment, the
mitigation playbook from Week 6.

## 8. Known issue — broken uv trampolines in `.venv-mlops/Scripts/`

The `.exe` shims (`jupyter.exe`, `kedro.exe`, etc.) fail with:

```
error: uv trampoline failed to canonicalize script path
```

Workaround — invoke via `python -m`:

```powershell
.\.venv-mlops\Scripts\python.exe -m jupyter notebook
.\.venv-mlops\Scripts\python.exe -m pytest tests/
.\.venv-mlops\Scripts\python.exe -m kedro run
```

Proper fix (run once, when convenient):

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".venv-mlops"; uv sync --reinstall
```

## 9. What auto-runs without asking

Inherits the global and course `.claude/settings.json` allowlists. Project
overrides go in `Project/.claude/settings.json`, not here.
