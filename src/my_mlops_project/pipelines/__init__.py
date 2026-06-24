"""my_mlops_project.pipelines — collection of modular sub-pipelines.

Each sub-package under ``pipelines/`` is a self-contained Kedro
pipeline. The canonical order, mandated by ``MLOps_project.pdf``, is::

    data_quality
      -> data_cleaning
        -> data_feat_engineering
          -> data_split
            -> model_train
              -> model_selection
                -> model_predict
                  -> data_drifts

Each sub-package follows the same three-file layout:

- ``nodes.py``   — pure-Python node functions (no Kedro imports).
- ``pipeline.py`` — the ``create_pipeline()`` factory that wires nodes
  together using Kedro's ``Pipeline``/``node`` API.
- ``__init__.py`` — re-exports ``create_pipeline`` for the registry.
"""
