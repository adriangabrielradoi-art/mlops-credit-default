"""Kedro pipeline wiring for the `data_quality` sub-pipeline.

Wires the pure-Python functions in `nodes.py` into a Kedro `Pipeline` by binding
them to named catalog entries. Two nodes:

    raw_data ──validate_credit_data──> validated_data (02_intermediate)
                                   └──> ge_report (08_reporting)
    ge_report ──gate_on_quality──> (raises if any expectation failed)

The gate depends on ``ge_report`` so it runs AFTER validation; if it raises, the
run halts before any downstream pipeline (data_cleaning) consumes the data.

Class reference: Week 1.
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.data_quality import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `data_quality`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The `data_quality` pipeline: validate the raw data, then gate on it.
    """
    return pipeline(
        [
            node(
                func=nodes.validate_credit_data,
                # The raw .xls + the data_quality parameter block.
                inputs=["raw_data", "params:data_quality"],
                # Pass-through typed copy + the JSON results report.
                outputs=["validated_data", "ge_report"],
                name="validate_credit_data",
            ),
            node(
                func=nodes.gate_on_quality,
                inputs="ge_report",
                outputs=None,  # raises on failure; nothing to persist
                name="gate_on_quality",
            ),
        ]
    )
