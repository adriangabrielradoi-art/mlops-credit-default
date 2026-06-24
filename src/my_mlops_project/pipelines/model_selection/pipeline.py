"""Kedro pipeline wiring for the `model_selection` sub-pipeline.

    trained_models + training_metrics ──select_champion──> champion_model (06_models)
                                                       └──> champion_info (08_reporting)
    champion_model ──explain_champion──> shap_summary (08_reporting)

select_champion also registers the winner in the MLflow registry (alias Champion).

Class reference: Week 2 (registry) + Week 6 (SHAP).
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.model_selection import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `model_selection`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The pipeline: pick + register the champion, then explain it with SHAP.
    """
    return pipeline(
        [
            node(
                func=nodes.select_champion,
                inputs=["trained_models", "training_metrics", "X_train", "params:model_selection"],
                outputs=["champion_model", "champion_info"],
                name="select_champion",
            ),
            node(
                func=nodes.explain_champion,
                inputs=["champion_model", "X_train", "params:model_selection"],
                outputs="shap_summary",
                name="explain_champion",
            ),
        ]
    )
