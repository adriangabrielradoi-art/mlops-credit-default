"""Node functions for the `model_selection` pipeline.

Picks the champion (best validation primary metric) from the trained families,
registers it in the **MLflow Model Registry** with a ``Champion`` alias (the
data-scientist -> engineer hand-off the FastAPI service loads from), and computes
the **SHAP** global summary — a required explainability deliverable.

Class reference: Week 2 (registry) + Week 6 (SHAP). Tooling: MLflow, SHAP.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def select_champion(
    trained_models: dict,
    training_metrics: dict,
    X_train: pd.DataFrame,
    params: dict[str, Any],
) -> tuple[Any, dict]:
    """Choose the best model family and register it as ``Champion`` in MLflow.

    Args:
        trained_models: ``{family: fitted model}`` from model_train.
        training_metrics: ``{family: metrics}`` from model_train.
        X_train: Training features (for the model signature).
        params: The ``model_selection`` block (primary_metric, higher_is_better,
            registered_model_name).

    Returns:
        ``(champion_model, champion_info)`` — the selected model and a dict
        describing the choice + registry version.
    """
    metric = params["primary_metric"]
    higher = params["higher_is_better"]

    # Rank families by the primary metric (reverse=True => higher is better).
    ranked = sorted(
        training_metrics,
        key=lambda fam: training_metrics[fam][metric],
        reverse=higher,
    )
    best = ranked[0]
    champion_model = trained_models[best]

    champion_info: dict = {
        "champion_family": best,
        "primary_metric": metric,
        "value": training_metrics[best][metric],
        "ranking": ranked,
    }

    # Register the champion in the MLflow Model Registry (best-effort: never fail
    # the pipeline if the tracking store is unavailable).
    try:
        import mlflow
        from mlflow.models import infer_signature
        from mlflow import MlflowClient

        nested = mlflow.active_run() is not None
        with mlflow.start_run(nested=nested, run_name=f"champion_{best}"):
            mlflow.set_tag("champion_family", best)
            mlflow.log_metrics(training_metrics[best])
            signature = infer_signature(X_train, champion_model.predict(X_train))
            logged = mlflow.sklearn.log_model(
                champion_model,
                name="model",
                signature=signature,
                registered_model_name=params["registered_model_name"],
            )
        # Promote this version with the Champion alias (replaces stages).
        MlflowClient().set_registered_model_alias(
            params["registered_model_name"], "Champion", logged.registered_model_version
        )
        champion_info["registered_model_name"] = params["registered_model_name"]
        champion_info["registered_version"] = logged.registered_model_version
        champion_info["alias"] = "Champion"
    except Exception as exc:  # noqa: BLE001
        champion_info["registration_note"] = (
            f"Registry step skipped ({type(exc).__name__}: {exc})"
        ).encode("ascii", "replace").decode()

    print(
        f"model_selection: champion = {best} "
        f"({metric}={champion_info['value']:.4f}), "
        f"registry version = {champion_info.get('registered_version', 'n/a')}"
    )
    return champion_model, champion_info


def explain_champion(champion_model, X_train: pd.DataFrame, params: dict[str, Any]):
    """Compute the SHAP global summary plot for the champion.

    Uses TreeSHAP (exact, fast) for the tree champion. Returns a matplotlib
    figure that the catalog saves as ``shap_summary.png``.

    Args:
        champion_model: The fitted champion (a tree model here).
        X_train: Training features to explain.
        params: The ``model_selection`` block (shap_max_samples).

    Returns:
        A matplotlib Figure of the SHAP beeswarm summary.
    """
    import shap
    import matplotlib
    matplotlib.use("Agg")  # headless backend for pipeline runs
    import matplotlib.pyplot as plt

    # Sample to keep SHAP fast on the full training set.
    n = min(len(X_train), params["shap_max_samples"])
    sample = X_train.sample(n, random_state=42)

    plt.figure()
    try:
        explainer = shap.TreeExplainer(champion_model)
        shap_values = np.asarray(explainer.shap_values(sample))
        # Binary tree ensembles may return (n, features, 2) — take the positive class.
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, 1]
        shap.summary_plot(shap_values, sample, show=False)
        print(f"explain_champion: SHAP summary over {n} samples")
    except Exception as exc:  # noqa: BLE001 — non-tree champion fallback
        importances = getattr(champion_model, "feature_importances_", None)
        if importances is not None:
            order = np.argsort(importances)[-15:]
            plt.barh(np.array(sample.columns)[order], importances[order])
            plt.xlabel("feature importance")
        else:
            plt.text(0.5, 0.5, f"SHAP unavailable: {type(exc).__name__}", ha="center")
        print(f"explain_champion: SHAP fallback ({type(exc).__name__})")

    fig = plt.gcf()
    fig.set_size_inches(9, 6)
    fig.tight_layout()
    return fig
