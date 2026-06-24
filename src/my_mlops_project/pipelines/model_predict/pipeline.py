"""Kedro pipeline wiring for the `model_predict` sub-pipeline (batch inference).

    X_test + champion_model ──batch_predict──> predictions (07), decision_log (08)
    X_test + champion_model ──per_prediction_shap──> shap_predictions (08)

The online serving counterpart is the FastAPI app under `serving/`.

Class reference: Week 4/5 (serving) + Week 6 (per-prediction SHAP).
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.model_predict import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `model_predict`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The pipeline: batch-score the test set and log per-prediction SHAP.
    """
    return pipeline(
        [
            node(
                func=nodes.batch_predict,
                inputs=["X_test", "champion_model", "params:model_predict"],
                outputs=["predictions", "decision_log"],
                name="batch_predict",
            ),
            node(
                func=nodes.per_prediction_shap,
                inputs=["X_test", "champion_model", "params:model_predict"],
                outputs="shap_predictions",
                name="per_prediction_shap",
            ),
        ]
    )
