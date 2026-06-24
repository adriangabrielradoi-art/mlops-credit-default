"""Node functions for the `model_train` pipeline.

Trains three candidate model families (Logistic Regression, Random Forest,
Gradient Boosting), tunes each with **Optuna** (maximising validation ROC-AUC,
the honest metric on this ~22% imbalanced target), and logs every family's best
run to **MLflow** (params, metrics, the signed model).

One MLflow run per family (nested under the kedro-mlflow parent run when present)
so the three are directly comparable in the MLflow UI and feed the report's
model-comparison table.

Class reference: Week 2. Primary tooling: MLflow, Optuna, scikit-learn.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import mlflow
import optuna
from mlflow.models import infer_signature
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    accuracy_score,
)

optuna.logging.set_verbosity(optuna.logging.WARNING)


def _suggest(trial: optuna.Trial, name: str) -> dict:
    """Return an Optuna-sampled hyperparameter dict for one model family."""
    if name == "LogisticRegression":
        return {"C": trial.suggest_float("C", 1e-3, 100.0, log=True)}
    if name == "RandomForest":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 16),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 20),
        }
    if name == "GradientBoosting":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 200),
            "max_depth": trial.suggest_int("max_depth", 2, 5),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        }
    raise ValueError(f"Unknown model family: {name}")


def _build(name: str, hp: dict, seed: int):
    """Construct an (unfitted) estimator from a family name + hyperparameters.

    Logistic Regression is wrapped with a StandardScaler (it is scale-sensitive
    and the bill/payment amounts are large); the tree models need no scaling.
    `class_weight="balanced"` counters the class imbalance where supported.
    """
    if name == "LogisticRegression":
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed, **hp),
        )
    if name == "RandomForest":
        return RandomForestClassifier(
            class_weight="balanced", n_jobs=-1, random_state=seed, **hp
        )
    if name == "GradientBoosting":
        return GradientBoostingClassifier(random_state=seed, **hp)
    raise ValueError(f"Unknown model family: {name}")


def _evaluate(model, X: pd.DataFrame, y: pd.Series) -> dict:
    """Compute the metric suite for a fitted model on (X, y)."""
    proba = model.predict_proba(X)[:, 1]
    pred = model.predict(X)
    return {
        "roc_auc": float(roc_auc_score(y, proba)),
        "pr_auc": float(average_precision_score(y, proba)),
        "f1": float(f1_score(y, pred)),
        "accuracy": float(accuracy_score(y, pred)),
    }


def train_and_tune(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
    params: dict[str, Any],
) -> tuple[dict, dict]:
    """Tune + train each candidate family and log the best of each to MLflow.

    Args:
        X_train, y_train: Training split (y as a single-column frame).
        X_val, y_val: Validation split used for tuning + reported metrics.
        params: The ``model_train`` block (candidate_models, optuna_trials,
            primary_metric, random_seed).

    Returns:
        ``(trained_models, training_metrics)`` — a dict of fitted best models per
        family and a dict of their validation metrics.
    """
    seed = params["random_seed"]
    n_trials = params["optuna_trials"]
    metric = params["primary_metric"]
    y_tr = y_train.squeeze("columns")  # 1-col frame -> Series
    y_va = y_val.squeeze("columns")

    trained_models: dict = {}
    training_metrics: dict = {}

    for name in params["candidate_models"]:
        # --- Optuna study: maximise the validation primary metric ---
        def objective(trial: optuna.Trial) -> float:
            model = _build(name, _suggest(trial, name), seed)
            model.fit(X_train, y_tr)
            return _evaluate(model, X_val, y_va)[metric]

        study = optuna.create_study(
            direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed)
        )
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        # --- Refit the best config and evaluate on validation ---
        best_model = _build(name, study.best_params, seed).fit(X_train, y_tr)
        val_metrics = _evaluate(best_model, X_val, y_va)

        # --- Log one MLflow run for this family (nested under the kedro run) ---
        nested = mlflow.active_run() is not None
        with mlflow.start_run(nested=nested, run_name=name):
            mlflow.set_tag("model_family", name)
            mlflow.log_param("optuna_trials", n_trials)
            mlflow.log_params(study.best_params)
            mlflow.log_metrics(val_metrics)
            signature = infer_signature(X_train, best_model.predict(X_train))
            mlflow.sklearn.log_model(best_model, name="model", signature=signature)

        trained_models[name] = best_model
        training_metrics[name] = val_metrics
        print(
            f"model_train [{name}]: best {metric}={val_metrics[metric]:.4f} "
            f"(f1={val_metrics['f1']:.3f}, pr_auc={val_metrics['pr_auc']:.3f}) "
            f"over {n_trials} Optuna trials"
        )

    return trained_models, training_metrics
