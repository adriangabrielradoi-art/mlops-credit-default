"""Kedro project settings.

This module is read by Kedro at startup to discover where the project
configuration lives, which session store to use, and which hooks (if
any) to register. Most teams customize:

- ``CONFIG_LOADER_CLASS``: which config loader (OmegaConfLoader is the
  modern default and supports templating).
- ``CONFIG_LOADER_ARGS``: where to look for ``catalog.yml``,
  ``parameters.yml``, ``globals.yml``.
- ``HOOKS``: lifecycle hooks (e.g. mlflow_kedro hooks register here so
  that every Kedro run automatically becomes an MLflow run).

TODO(week_3_lab): once Kedro is installed, uncomment the relevant
imports below and confirm ``kedro run`` discovers the pipelines.
"""

# OmegaConfigLoader is Kedro's modern config loader; it resolves the
# ${globals:...} templating used across catalog.yml / parameters.yml.
# MlflowHook makes every `kedro run` automatically open an MLflow run and
# log params/metrics/artifacts declared via MlflowArtifactDataset.
from kedro.config import OmegaConfigLoader
from kedro_mlflow.framework.hooks import MlflowHook

# Tell Kedro to use the OmegaConf loader (enables ${globals:...}).
CONFIG_LOADER_CLASS = OmegaConfigLoader  # type: ignore[assignment]

# Where the Kedro config loader looks for YAML files. The defaults map
# to ``conf/base`` (shared, gitted) and ``conf/local`` (per-developer,
# gitignored).
CONFIG_LOADER_ARGS: dict = {
    # Base config patterns — what filenames in conf/base/ are picked up.
    "config_patterns": {
        "catalog": ["catalog*", "catalog*/**", "**/catalog*"],
        "parameters": ["parameters*", "parameters*/**", "**/parameters*"],
        "globals": ["globals*", "globals*/**", "**/globals*"],
    },
}

# Lifecycle hooks that wrap every Kedro run. The MlflowHook ties Kedro
# runs to MLflow experiments/runs (kedro-mlflow). Reads conf/base/mlflow.yml.
HOOKS: tuple = (MlflowHook(),)
