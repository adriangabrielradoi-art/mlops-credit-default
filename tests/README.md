# `tests/` — Pytest suite

Mirrors `src/my_mlops_project/pipelines/`. One folder per sub-pipeline.

## Run all tests

```powershell
.\.venv-mlops\Scripts\python.exe -m pytest tests/ -v
```

## Run tests for a single pipeline

```powershell
.\.venv-mlops\Scripts\python.exe -m pytest tests/pipelines/data_quality/ -v
```

## Conventions

- Test files: `test_<thing>.py` (pytest auto-discovery).
- Test functions: `test_<behavior>()`.
- Import node functions from `nodes.py` directly — do **not** import
  Kedro to unit-test pure-Python nodes.
- Shared synthetic DataFrames live in `tests/conftest.py`.
