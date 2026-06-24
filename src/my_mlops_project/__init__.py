"""my_mlops_project — root package.

Top-level package for the MLOps course project. The package name
``my_mlops_project`` matches the project name in ``pyproject.toml``
(with hyphens replaced by underscores, as Python module names require).

The package is a Kedro project: configuration lives in ``conf/``, data
under ``data/``, and the modular sub-pipelines under
``my_mlops_project.pipelines``.
"""

# __version__ tracks the project version so MLflow runs and model
# artifacts can be tagged with the code version that produced them.
__version__ = "0.1.0"
