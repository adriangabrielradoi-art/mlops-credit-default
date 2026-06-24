"""Champion-model loader for the serving API.

Resolution order (first that works wins):
1. ``CHAMPION_PATH`` env var pointing at a pickled model — used inside the Docker
   image, where the model is copied in.
2. The MLflow Model Registry alias ``credit_default_champion@Champion`` — the
   production-correct path (model loaded at startup, not baked in). Used locally.
3. The project's ``data/06_models/champion_model.pkl`` fallback.

This mirrors the lecture's guidance ("load the model when the container starts")
while staying runnable both locally and in a container.
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    """Project root = two levels up from this file (serving/app/loader.py)."""
    return Path(__file__).resolve().parents[2]


def load_champion() -> Any:
    """Load the champion model from env path, MLflow registry, or pickle."""
    # 1. Explicit pickle path (the Docker image sets this).
    env_path = os.getenv("CHAMPION_PATH")
    if env_path and Path(env_path).exists():
        with open(env_path, "rb") as fh:
            return pickle.load(fh)

    root = _project_root()

    # 2. MLflow registry by alias (production-correct, used locally).
    try:
        import mlflow

        mlflow.set_tracking_uri(f"sqlite:///{(root / 'mlflow.db').as_posix()}")
        return mlflow.sklearn.load_model(
            "models:/credit_default_champion@Champion"
        )
    except Exception:
        pass

    # 3. Local pickle fallback.
    with open(root / "data" / "06_models" / "champion_model.pkl", "rb") as fh:
        return pickle.load(fh)
