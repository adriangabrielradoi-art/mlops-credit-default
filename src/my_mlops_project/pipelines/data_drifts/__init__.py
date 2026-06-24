"""`data_drifts` sub-pipeline — re-exports `create_pipeline`.

This thin shim lets the project's pipeline registry import
`create_pipeline` directly from the sub-package without reaching into
`pipeline.py`.
"""

# Re-export so `from my_mlops_project.pipelines.data_drifts import create_pipeline`
# is the canonical import path used by `pipeline_registry.py`.
from my_mlops_project.pipelines.data_drifts.pipeline import create_pipeline  # noqa: F401

__all__ = ["create_pipeline"]
