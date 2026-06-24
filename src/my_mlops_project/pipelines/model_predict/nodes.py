"""Node functions for the `model_predict` pipeline (batch inference).

Batch-scores the held-out test set with the champion, writes a decision log, and
logs per-prediction SHAP (the explanation-level monitoring signal from week 6).
The *online* serving counterpart is the FastAPI app under ``serving/`` (see its
README), which loads the champion from the MLflow registry at startup.

Class reference: Week 4/5 (serving) + Week 6 (per-prediction SHAP).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def batch_predict(
    X_test: pd.DataFrame, champion_model, params: dict[str, Any]
) -> tuple[pd.DataFrame, dict]:
    """Score the test set and summarise the decisions.

    Args:
        X_test: Held-out features.
        champion_model: The registered champion (loaded from the catalog; the
            same object registered under the Champion alias).
        params: The ``model_predict`` block (prediction_threshold).

    Returns:
        ``(predictions, decision_log)`` — per-row probability + decision, and a
        summary dict (score distribution, predicted default rate).
    """
    threshold = params["prediction_threshold"]
    proba = champion_model.predict_proba(X_test)[:, 1]
    decision = (proba >= threshold).astype(int)

    predictions = pd.DataFrame(
        {"default_proba": proba, "prediction": decision}, index=X_test.index
    )

    decision_log = {
        "n_scored": int(len(decision)),
        "threshold": float(threshold),
        "n_predicted_default": int(decision.sum()),
        "predicted_default_rate": float(decision.mean()),
        "proba_mean": float(proba.mean()),
        "proba_median": float(np.median(proba)),
        "proba_p95": float(np.quantile(proba, 0.95)),
    }
    print(
        f"batch_predict: scored {len(decision)} rows -> predicted default rate "
        f"{decision.mean():.3f} at threshold {threshold}"
    )
    return predictions, decision_log


def per_prediction_shap(
    X_test: pd.DataFrame, champion_model, params: dict[str, Any]
) -> pd.DataFrame:
    """Log per-prediction SHAP values for a sample of test rows.

    This is the explanation-level monitoring signal (week 6): every production
    score can be explained, which is what lets you diagnose *why* the model
    flagged a customer (and catch drift via shifting attributions).

    Args:
        X_test: Held-out features.
        champion_model: The champion (a tree model -> TreeSHAP).
        params: The ``model_predict`` block (shap_sample).

    Returns:
        A DataFrame of per-row SHAP values (one column per feature).
    """
    import shap

    n = min(len(X_test), params["shap_sample"])
    sample = X_test.sample(n, random_state=42)
    try:
        explainer = shap.TreeExplainer(champion_model)
        values = np.asarray(explainer.shap_values(sample))
        if values.ndim == 3:  # binary tree ensemble -> positive class
            values = values[:, :, 1]
        shap_df = pd.DataFrame(values, columns=sample.columns, index=sample.index)
    except Exception as exc:  # noqa: BLE001 — non-tree fallback
        print(f"per_prediction_shap: skipped ({type(exc).__name__})")
        shap_df = pd.DataFrame(index=sample.index)
    print(f"per_prediction_shap: logged SHAP for {len(sample)} predictions")
    return shap_df
