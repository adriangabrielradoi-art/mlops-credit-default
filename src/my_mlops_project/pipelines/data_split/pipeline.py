"""Kedro pipeline wiring for the `data_split` sub-pipeline.

    feature_table ──split_data──> X_train/X_val/X_test, y_train/y_val/y_test (05_model_input)
    X_train ──make_reference_distribution──> reference_distribution (03_primary)

The reference distribution is the drift baseline the `data_drifts` pipeline
compares production batches against.

Class reference: Week 1 (data prep).
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.data_split import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `data_split`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The pipeline: stratified split, then snapshot the drift baseline.
    """
    return pipeline(
        [
            node(
                func=nodes.split_data,
                inputs=["feature_table", "params:data_split"],
                outputs=["X_train", "X_val", "X_test", "y_train", "y_val", "y_test"],
                name="split_data",
            ),
            node(
                func=nodes.make_reference_distribution,
                inputs="X_train",
                outputs="reference_distribution",
                name="make_reference_distribution",
            ),
        ]
    )
