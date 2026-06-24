"""Kedro pipeline wiring for the `data_drifts` sub-pipeline (week-6 monitoring).

    X_test ──make_drift_samples──> current_clean, current_drifted
    reference_distribution + both batches ──compute_drift──> drift_summary, psi_per_feature
    reference_distribution + current_drifted ──evidently_report──> drift_report (html)
    drift_summary + psi_per_feature ──build_monitoring_dashboard──> monitoring_dashboard (html)

Validates drift detection: stays quiet on the clean batch, fires on the biased
batch. ``monitoring_dashboard.html`` is the final report artifact.
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.data_drifts import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `data_drifts`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The pipeline: build batches, detect drift, and emit the dashboard.
    """
    return pipeline(
        [
            node(
                func=nodes.make_drift_samples,
                inputs=["X_test", "params:data_drifts"],
                outputs=["current_clean", "current_drifted"],
                name="make_drift_samples",
            ),
            node(
                func=nodes.compute_drift,
                inputs=[
                    "reference_distribution",
                    "current_clean",
                    "current_drifted",
                    "params:data_drifts",
                ],
                outputs=["drift_summary", "psi_per_feature"],
                name="compute_drift",
            ),
            node(
                func=nodes.evidently_report,
                inputs=["reference_distribution", "current_drifted"],
                outputs="drift_report",
                name="evidently_report",
            ),
            node(
                func=nodes.build_monitoring_dashboard,
                inputs=["drift_summary", "psi_per_feature"],
                outputs="monitoring_dashboard",
                name="build_monitoring_dashboard",
            ),
        ]
    )
