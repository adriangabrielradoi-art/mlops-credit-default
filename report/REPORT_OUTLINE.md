# Project Report — Outline (max 6 pages)

> Skeleton for the final report. Every required section from
> [`../MLOps_project.pdf`](../MLOps_project.pdf) is represented as a
> heading below. Fill each one in; do not delete the section
> headings — they map 1:1 to the grading rubric.

**Front page must include:** group members, dataset name, link to the
GitHub repo with the code, and instructions to run.

---

## Table of Contents

1. [Problem & dataset](#1-problem--dataset)
2. [Success metrics](#2-success-metrics)
3. [Project planning (agile sprints)](#3-project-planning-agile-sprints)
4. [Data exploration & modelling results](#4-data-exploration--modelling-results)
5. [Production discussion: advantages, risks, mitigations](#5-production-discussion-advantages-risks-mitigations)
6. [Packages & versions](#6-packages--versions)

---

## 1. Problem & dataset

- **Dataset:** TODO(dataset)
- **Why this dataset:** TODO — be honest about why you chose it (group
  interest, drift story, public availability, etc.).
- **What you are trying to achieve:** TODO — one paragraph on the
  business / scientific objective.
- **Target variable:** TODO
- **Task type:** TODO (binary classification / regression / ...)

## 2. Success metrics

> The PDF asks specifically for "your success metrics" — name them and
> state the threshold that would mean success.

- **Primary metric:** TODO (e.g. ROC-AUC ≥ 0.80 on hold-out)
- **Secondary metrics:** TODO
- **Operational metrics:** TODO (latency, drift detection lead time)

## 3. Project planning (agile sprints)

> The PDF: "how you organized and scheduled the different steps (you
> can be inspired by sprints in the agile methodology)."

Suggested 5-week sprint plan (current date: 2026-05-26, due 2026-06-30):

| Sprint | Dates           | Focus                                     | Owner |
| ------ | --------------- | ----------------------------------------- | ----- |
| 1      | 26/05 – 01/06   | Dataset commit, EDA, `data_quality`       | TODO  |
| 2      | 02/06 – 08/06   | `data_cleaning`, `data_feat_engineering`  | TODO  |
| 3      | 09/06 – 15/06   | `data_split`, `model_train` + MLflow      | TODO  |
| 4      | 16/06 – 22/06   | `model_selection` + SHAP, `model_predict` + Docker/FastAPI | TODO |
| 5      | 23/06 – 29/06   | `data_drifts`, tests, report, presentation | TODO |
| Buffer | 30/06           | Submission                                | all   |

## 4. Data exploration & modelling results

> The PDF: "Results and conclusions from data exploration and data
> modelling (plots, feature importance, explainability)."

Suggested subsections:

- **EDA highlights** — 2-3 plots, key takeaways.
- **Feature importance** — table or bar chart, ordered.
- **SHAP explainability** — summary plot + 1-2 paragraphs of
  interpretation (which features drive predictions, where the model
  disagrees with intuition).
- **Model comparison table** — candidate models × primary/secondary
  metrics, MLflow run IDs.

## 5. Production discussion: advantages, risks, mitigations

> The PDF: "Since this is a proof of concept, discuss how this would be
> implemented in production and what are the advantages of the
> technologies used, risks and possible mitigations."
>
> Example given by the professor: "we are using only Pandas, so if the
> amount of data scales up, our pipeline will not be efficient. We
> propose more X weeks to build in Spark, as a mitigation solution."

Suggested table:

| Technology used | Production advantage | Risk | Proposed mitigation |
| --------------- | -------------------- | ---- | ------------------- |
| Kedro           | Modular, testable    | TODO | TODO                |
| MLflow          | Experiment tracking  | TODO | TODO                |
| FastAPI         | Low-latency serving  | TODO | TODO                |
| Docker          | Reproducible runtime | TODO | TODO                |
| Evidently       | Drift detection      | TODO | TODO                |
| pandas          | Easy to write        | Single-machine only | Re-implement in Spark/Polars if data > 50M rows |

### 5.1 Deployment strategy (from Week 5 lecture)

Discuss which **release pattern** we'd use to move a new champion into
production, and why:

- **Blue/Green** — full new system beside the stable one, switch all
  traffic at once. Lowest infra complexity, highest rollback speed,
  but doubles infra cost during cutover.
- **Canary** — route a small % of traffic to the challenger, scale up
  if metrics hold. Best for safety + observability; needs a traffic
  splitter (K8s ingress, service mesh).
- **Shadow** — challenger runs in parallel, predictions logged but
  *not used*. Risk-free quality check on real traffic before any
  user exposure.
- **A/B** — formal statistical comparison (sample size + duration).
  Best when measuring business impact, not just model accuracy.

Recommend one; justify against our dataset's blast radius and how
fast we'd want to roll back.

### 5.2 Scaling roadmap (from Week 5 lecture — Kubernetes / Kubeflow)

Our POC ships Docker; the natural production progression is:

| Stage              | What it adds                                   | When to upgrade                      |
| ------------------ | ---------------------------------------------- | ------------------------------------ |
| Single Docker      | Reproducible runtime                           | (current)                            |
| Docker Compose     | API + MLflow + (optional) feature-store local  | Multi-service local stack            |
| Kubernetes + HPA   | Horizontal autoscaling on CPU thresholds       | Latency-SLA breaches at peak traffic |
| Kubeflow Pipelines | ML-native DAG orchestration on K8s             | Multiple production pipelines        |
| Kubeflow Serving   | Multi-model serving (Seldon / TF-Serving / KServe) | More than 3-5 models in prod     |

### 5.3 Monitoring & retraining playbook (from Week 6 lecture)

Mitigation sequence the lecture proposes — show our position on it:

1. Effective logging system (we have `decision_log.csv` + `predictions.parquet`).
2. Store FP / TN counts + drift indicators (we have `drift_flags.json`).
3. Threshold adjustment before retraining (`prediction_threshold` param).
4. Trigger retrain on sustained drift (`trigger_retrain_on_drift` flag).
5. Add features → new algorithm → shadow/A-B (deferred to v2).

## 6. Packages & versions

> Generate the list from the locked environment so it matches what the
> grader will install.
>
> ```powershell
> .\.venv-mlops\Scripts\python.exe -m pip list --format=freeze > report/requirements_frozen.txt
> ```
>
> Then copy the relevant subset into the report (do not paste hundreds
> of transitive deps — pick the direct ones from
> [`../pyproject.toml`](../pyproject.toml) and their pinned versions).
