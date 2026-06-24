"""Tests for the `model_selection` pipeline.

Champion selection by metric, and the SHAP node returning a figure. Registration
is best-effort (the file-store test backend has no registry — the node handles
it gracefully; the full pipeline run exercises the real sqlite registry).
"""
import mlflow
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from my_mlops_project.pipelines.model_selection.nodes import (
    select_champion,
    explain_champion,
)

PARAMS = {
    "primary_metric": "roc_auc",
    "higher_is_better": True,
    "shap_max_samples": 50,
    "registered_model_name": "test_champion",
}


def _fitted_models():
    X, y = make_classification(
        n_samples=200, n_features=6, weights=[0.78, 0.22], random_state=0
    )
    X = pd.DataFrame(X, columns=[f"f{i}" for i in range(6)])
    rf = RandomForestClassifier(n_estimators=20, random_state=0).fit(X, y)
    gb = GradientBoostingClassifier(n_estimators=20, random_state=0).fit(X, y)
    return X, {"RandomForest": rf, "GradientBoosting": gb}


def test_select_champion_picks_highest_metric(tmp_path):
    """The family with the best roc_auc is chosen as champion."""
    mlflow.set_tracking_uri((tmp_path / "mlruns").as_uri())
    X, models = _fitted_models()
    metrics = {
        "RandomForest": {"roc_auc": 0.79, "pr_auc": 0.60, "f1": 0.55, "accuracy": 0.78},
        "GradientBoosting": {"roc_auc": 0.80, "pr_auc": 0.59, "f1": 0.48, "accuracy": 0.82},
    }
    champion, info = select_champion(models, metrics, X, PARAMS)
    assert info["champion_family"] == "GradientBoosting"
    assert champion is models["GradientBoosting"]
    assert info["ranking"][0] == "GradientBoosting"


def test_explain_champion_returns_a_figure():
    """SHAP node returns a saveable matplotlib figure for a tree model."""
    X, models = _fitted_models()
    fig = explain_champion(models["GradientBoosting"], X, PARAMS)
    assert fig is not None
    assert hasattr(fig, "savefig")
