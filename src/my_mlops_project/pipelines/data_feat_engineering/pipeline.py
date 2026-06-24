"""Kedro pipeline wiring for the `data_feat_engineering` sub-pipeline.

    cleaned_data ──engineer_features──> feature_table (04_feature, canonical)
    feature_table ──sync_to_feature_store──> feature_store_status (08_reporting)

`engineer_features` always runs (local). `sync_to_feature_store` writes the
feature groups to Hopsworks and reads one back, but is best-effort: it never
fails the pipeline (see nodes.py). Downstream depends only on `feature_table`.

Class reference: Week 1 (feature store).
"""
from kedro.pipeline import Pipeline, node, pipeline

from my_mlops_project.pipelines.data_feat_engineering import nodes


def create_pipeline(**kwargs) -> Pipeline:
    """Build and return the Kedro `Pipeline` for `data_feat_engineering`.

    Args:
        **kwargs: Reserved for Kedro keyword arguments. Ignored.

    Returns:
        The pipeline: engineer features, then sync to the feature store.
    """
    return pipeline(
        [
            node(
                func=nodes.engineer_features,
                inputs=["cleaned_data", "params:data_feat_engineering"],
                outputs="feature_table",
                name="engineer_features",
            ),
            node(
                func=nodes.sync_to_feature_store,
                inputs=["feature_table", "params:data_feat_engineering"],
                outputs="feature_store_status",
                name="sync_to_feature_store",
            ),
        ]
    )
