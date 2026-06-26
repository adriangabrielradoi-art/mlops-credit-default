# `notebooks/`

Companion notebooks for the project. Open [`00_main.ipynb`](00_main.ipynb)
first. It is the master entry point with a Table of Contents linking
to one notebook per pipeline stage.

Notebook ↔ pipeline mapping:

| Notebook | Pipeline module |
| ----------------------------------- | ---------------------------------------------------------------- |
| `00_main.ipynb` | (navigation hub) |
| `01_data_quality.ipynb` | `src/my_mlops_project/pipelines/data_quality/` |
| `02_data_cleaning.ipynb` | `src/my_mlops_project/pipelines/data_cleaning/` |
| `03_data_feat_engineering.ipynb` | `src/my_mlops_project/pipelines/data_feat_engineering/` |
| `04_data_split.ipynb` | `src/my_mlops_project/pipelines/data_split/` |
| `05_model_train.ipynb` | `src/my_mlops_project/pipelines/model_train/` |
| `06_model_selection.ipynb` | `src/my_mlops_project/pipelines/model_selection/` |
| `07_model_predict.ipynb` | `src/my_mlops_project/pipelines/model_predict/` |
| `08_data_drifts.ipynb` | `src/my_mlops_project/pipelines/data_drifts/` |

## Workflow

Per [`../CLAUDE.md`](../CLAUDE.md) sections 5 and 6:

1. Always export the notebook fresh before reviewing. Never rely on a
   cached read.
2. Before adding any cell, read the whole notebook, propose where the
   cell goes, wait for approval.
3. Every notebook keeps its TOC up to date with new sections.
