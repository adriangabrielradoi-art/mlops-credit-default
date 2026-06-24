"""Kedro pipeline registry — single source of truth for runnable pipelines.

Kedro discovers runnable pipelines through ``register_pipelines`` below. Each
sub-pipeline lives under ``my_mlops_project.pipelines`` and exposes a
``create_pipeline()`` factory. We import those factories and assemble:

1. ``__default__`` — the full end-to-end run, in the order mandated by
   ``MLOps_project.pdf`` (data_quality → ... → data_drifts).
2. One named pipeline per sub-pipeline so each stage runs independently, e.g.
   ``kedro run --pipeline data_drifts`` once the model is in production.

Phase 0: every sub-pipeline currently returns an EMPTY pipeline, so the project
is runnable end-to-end (a no-op) while real nodes are filled in per phase.
"""
from kedro.pipeline import Pipeline

# One import per sub-pipeline factory module.
from my_mlops_project.pipelines.data_quality import pipeline as dq
from my_mlops_project.pipelines.data_cleaning import pipeline as dc
from my_mlops_project.pipelines.data_feat_engineering import pipeline as dfe
from my_mlops_project.pipelines.data_split import pipeline as dsplit
from my_mlops_project.pipelines.model_train import pipeline as mt
from my_mlops_project.pipelines.model_selection import pipeline as ms
from my_mlops_project.pipelines.model_predict import pipeline as mp
from my_mlops_project.pipelines.data_drifts import pipeline as dd


def register_pipelines() -> dict[str, Pipeline]:
    """Return the ``{pipeline_name: Pipeline}`` mapping Kedro runs.

    ``__default__`` is special — it runs when ``kedro run`` is called with no
    ``--pipeline`` flag. Every stage is also exposed by name for independent
    execution (the rubric's "run separated pipelines" requirement).

    Returns:
        Mapping of pipeline name to ``kedro.pipeline.Pipeline``. The eight named
        stages plus the ``__default__`` full-sequence composition.
    """
    # Instantiate each stage's pipeline once.
    stages: dict[str, Pipeline] = {
        "data_quality": dq.create_pipeline(),
        "data_cleaning": dc.create_pipeline(),
        "data_feat_engineering": dfe.create_pipeline(),
        "data_split": dsplit.create_pipeline(),
        "model_train": mt.create_pipeline(),
        "model_selection": ms.create_pipeline(),
        "model_predict": mp.create_pipeline(),
        "data_drifts": dd.create_pipeline(),
    }

    # The default pipeline is the full sequence, in canonical order. Summing
    # Kedro pipelines composes them; an empty pipeline contributes nothing.
    default = sum(stages.values(), Pipeline([]))

    # Named stages + the default. Independent runs use the named keys.
    return {"__default__": default, **stages}
