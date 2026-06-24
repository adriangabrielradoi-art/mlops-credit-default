# Package list (direct dependencies)

Resolved versions in the project environment (`.venv-mlops`, Python 3.13).
Full transitive pins are in [`uv.lock`](../uv.lock).

| Role | Package | Version |
|---|---|---|
| Orchestration / framework | `kedro` | 1.3.1 |
|  | `kedro-datasets` | 9.4.0 |
|  | `kedro-mlflow` | 2.0.2 |
| Experimentation | `mlflow` | 3.11.1 |
|  | `optuna` | 4.8.0 |
| Data quality / feature store | `great-expectations` | 1.16.1 |
|  | `hopsworks` | 5.0.0 |
|  | `ydata-profiling` | 4.18.1 |
|  | `confluent-kafka` | 2.14.2 |
| Modelling | `scikit-learn` | 1.8.0 |
|  | `shap` | 0.52.0 |
|  | `pandas` | 2.3.3 |
|  | `pyarrow` | 23.0.1 |
|  | `xlrd` | 2.0.2 |
| Serving | `fastapi` | 0.136.0 |
|  | `uvicorn` | 0.44.0 |
|  | `docker` | 7.1.0 |
| Monitoring | `evidently` | 0.7.21 |
| Scheduling | `prefect` | 3.6.27 |
| Data / tooling | `ucimlrepo` | 0.0.7 |
|  | `ipywidgets` | 8.1.8 |
|  | `jupyterlab` | 4.5.6 |
|  | `setuptools` | 80.10.2 |

**Dev / testing:** `pytest` 9.1.1, `pytest-cov` 7.1.0
