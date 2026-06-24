"""Tests for the `model_train` pipeline.

Trains two fast families with 2 Optuna trials on small synthetic data, logging
to a temporary MLflow store. (GradientBoosting is exercised by the full pipeline
run, not the unit test.)
"""
import mlflow
import pandas as pd
from sklearn.datasets import make_classification

from my_mlops_project.pipelines.model_train.nodes import train_and_tune


def _synthetic_split():
    """Small imbalanced classification data, split into train/val frames."""
    X, y = make_classification(
        n_samples=300, n_features=8, weights=[0.78, 0.22], random_state=0
    )
    cols = [f"f{i}" for i in range(8)]
    X = pd.DataFrame(X, columns=cols)
    y = pd.DataFrame({"default": y})
    return X.iloc[:200], y.iloc[:200], X.iloc[200:], y.iloc[200:]


def test_train_and_tune_returns_models_and_metrics(tmp_path):
    """Each family yields a fitted model and valid metrics; MLflow runs logged."""
    mlflow.set_tracking_uri((tmp_path / "mlruns").as_uri())
    X_train, y_train, X_val, y_val = _synthetic_split()

    params = {
        "candidate_models": ["LogisticRegression", "RandomForest"],
        "optuna_trials": 2,
        "primary_metric": "roc_auc",
        "random_seed": 42,
    }
    models, metrics = train_and_tune(X_train, y_train, X_val, y_val, params)

    assert set(models) == {"LogisticRegression", "RandomForest"}
    assert set(metrics) == {"LogisticRegression", "RandomForest"}
    for fam, m in metrics.items():
        # every model can predict and the metrics are in range
        assert hasattr(models[fam], "predict")
        assert 0.0 <= m["roc_auc"] <= 1.0
        assert 0.0 <= m["f1"] <= 1.0

    # The two families were logged as MLflow runs.
    runs = mlflow.search_runs(search_all_experiments=True)
    assert len(runs) >= 2
