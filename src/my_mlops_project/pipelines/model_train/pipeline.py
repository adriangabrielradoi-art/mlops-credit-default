"""Kedro pipeline wiring for the `model_train` sub-pipeline.

    X_train/y_train/X_val/y_val ──train_and_tune──> trained_models (06_models)
                                                 └──> training_metrics (08_reporting)

Each candidate family is Optuna-tuned and logged to MLflow as its own run.

Class reference: Week 2 (MLflow + Optuna).
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.model_train import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `model_train`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The pipeline: tune + train the candidate models, log to MLflow.
    """
    return pipeline(
        [
            node(
                func=nodes.train_and_tune,
                inputs=["X_train", "y_train", "X_val", "y_val", "params:model_train"],
                outputs=["trained_models", "training_metrics"],
                name="train_and_tune",
            ),
        ]
    )
