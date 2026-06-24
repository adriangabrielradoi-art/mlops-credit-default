"""Kedro pipeline wiring for the `data_cleaning` sub-pipeline.

    validated_data ──clean_credit_data──> cleaned_data (03_primary)

Decisions (drop ID, rename target, merge undocumented EDUCATION/MARRIAGE codes,
keep PAY_*) are documented in notebooks/02_data_cleaning.ipynb.

Class reference: Week 1 (data prep).
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.data_cleaning import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `data_cleaning`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The `data_cleaning` pipeline: one node, validated -> cleaned.
    """
    return pipeline(
        [
            node(
                func=nodes.clean_credit_data,
                inputs=["validated_data", "params:data_cleaning"],
                outputs="cleaned_data",
                name="clean_credit_data",
            ),
        ]
    )
