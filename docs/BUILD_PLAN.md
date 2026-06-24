# MLOps Project — Build Plan (modular, per-pipeline spec)

> The buildable spec for the UCI Credit Card Default project. Derived from a
> 4-way audit (rubric, labs, `_knowledge`, the bank example). Source of truth
> for *what to build*; the rubric [`../MLOps_project.pdf`](../MLOps_project.pdf)
> wins on conflicts. Pair with the coaching cadence in
> [`ROADMAP.md`](ROADMAP.md).

---

## 0. Locked decisions

| Decision | Choice | Why |
|---|---|---|
| **Dataset** | UCI Credit Card Default (id=350) | 30k rows, binary `default` (~22% pos), 4 feature groups, real temporal drift angle |
| **Target / problem** | Binary classification (`default` 0/1) | imbalanced → metric below |
| **Primary metric** | **ROC-AUC** (report PR-AUC + F1 + confusion matrix too) | accuracy lies on 22% imbalance; AUC is threshold-free; defensible |
| **Candidate models** | LogisticRegression, RandomForest, GradientBoosting | the lab trio; linear vs bagging vs boosting inductive biases |
| **Feature store** | **Hopsworks** (write + read-back) **+ local `04_feature` parquet fallback** | faithful to wk1-2 labs; parquet path keeps the grader able to reproduce |
| **Orchestration** | **Kedro** (build) **+ Prefect** (schedule) | faithful to wk3-4 labs; Prefect = creativity differentiator |
| **Serving** | **FastAPI + Docker** (load champion from registry) | rubric component 4; wk4-5 labs |
| **Kubernetes** | **report discussion only** (not built) | no lab code; lecture-only — goes in §5 production discussion |
| **Drift tooling** | Evidently **0.6.5** + from-scratch PSI/JS/KS + PCA reconstruction | wk6 lab pins `evidently==0.6.5`; faithful |
| **Raw header** | keep `header=0` (`X1..X23`) in raw; rename in `data_cleaning` | raw stays untouched (8-layer rule) |

**Teaching split:** I (Claude) scaffold *plumbing* — deps, `settings.py`,
`pipeline_registry.py`, `catalog.yml`, `parameters.yml` — with full explanation.
**You type the node logic**, coached, *retyping* (not copying) from the
`_knowledge/*.py` modules as reference. Concept-before-code per ROADMAP §1.

---

## 1. Guiding invariants

1. **8-layer data convention** — data flows downward only; `01_raw` is never
   mutated. (See [`../../_knowledge/kedro-fundamentals.ipynb`](../../_knowledge/kedro-fundamentals.ipynb).)
2. **One pipeline = one rubric component = independently runnable.** Each runs
   alone (`kedro run --pipeline=<name>`) AND in full sequence (`kedro run`).
3. **Reproducible** — `random_seed: 42` threaded everywhere; package versions
   frozen; a data sample shipped so the grader reproduces results.
4. **Every node is a pure function** → unit-testable (pytest, target ~100% of
   nodes, per the bank example).
5. **Nothing fabricated** — you run final execution and save outputs; I never
   invent metrics.

---

## 2. Phase 0 — Foundation (unblock everything) — *plumbing, ~½ day*

Nothing runs until these are done. **This is the one phase I scaffold fully.**

1. **Dependencies** (`pyproject.toml`): ADD `kedro`, `scikit-learn`, `shap`,
   `fastapi`, `uvicorn`, `xlrd`, `pyarrow`; PIN `evidently==0.6.5`; PRUNE
   `vadersentiment`, `confluent-kafka` (vestigial). Keep `kedro-mlflow`,
   `mlflow`, `optuna`, `great-expectations`, `hopsworks`, `prefect`,
   `ucimlrepo`, `ydata-profiling`, `setuptools<81`.
   - ⚠️ **Risk:** the lecture warns *Great Expectations latest conflicts with
     Hopsworks*. Resolve at install: pin a GX/Hopsworks-compatible pair, or
     isolate GX usage. Verify `uv sync` succeeds before proceeding.
2. **`settings.py`** — enable `OmegaConfigLoader` (so `${globals:...}` resolves)
   and register the kedro-mlflow `MlflowHook` in `HOOKS`.
3. **`pipeline_registry.py`** — import all 8 `create_pipeline` factories; return
   the 8 named pipelines + a `__default__` = full sequential composition.
4. **`pyproject.toml`** — add `[tool.kedro]` (package_name, project_name) so the
   Kedro CLI resolves.
5. **`conf/local/mlflow.yml`** — experiment name `credit_default`, nested runs,
   tracking URI from `globals.yml` (`sqlite:///mlflow.db`).
6. **`conf/local/credentials.yml`** (gitignored) — `FS_API_KEY`,
   `FS_PROJECT_NAME` for Hopsworks.
7. **Smoke test:** `kedro run` executes (pipelines are still empty no-ops) and
   `mlflow ui` opens.

**Exit criteria:** `uv sync` clean · `kedro run` no-errors · MLflow UI live.

---

## 3. The pipelines (build order = data flow)

Each spec: **purpose · consumes → produces (catalog layers) · nodes (you type) ·
reuse (knowledge `.py` + lab recipe) · params · test · report artifact.**

### 3.1 `data_quality` — rubric component 1 (data tests)
- **Purpose:** gate the raw data; fail loud on a broken batch.
- **Consumes:** `raw_data` (01_raw, `pandas.ExcelDataset`, `header:0`).
  **Produces:** `ge_results` (08_reporting JSON via `MlflowArtifactDataset`); passes raw through unchanged.
- **Nodes (you type):** `validate_raw(df, params) -> df` — build a GX suite with
  several asserts, run it, **raise on failure**. Expectations to include
  (≥6): `AGE` between 18-100; `SEX` in {1,2}; `EDUCATION` in {1,2,3,4} (flags the
  undocumented 5,6 — teachable!); `MARRIAGE` in {0,1,2,3}; `LIMIT_BAL` ≥ 0;
  `default` in {0,1}; table column count = 24; `PAY_*` not null.
- **Reuse:** `great_expectations_data_validation.py` →
  `build_suite`/`validate_dataframe`/`parse_results`; lab
  `week_03/bank-example/.../data_unit_tests/nodes.py` (the hard-gate `raise`).
- **Params:** add a `data_quality` block (allowed value-sets, ranges).
- **Test:** `test_validate_raw_passes_clean` + `test_validate_raw_raises_on_bad`.
- **Report → §3** (data exploration / quality).

### 3.2 `data_cleaning` — (no rubric # of its own; enables 1 & 3)
- **Purpose:** first value manipulation. Raw `X1..X23` → readable, typed, deduped.
- **Consumes:** `raw_data` (01_raw). **Produces:** `cleaned_data` (03_primary, parquet).
- **Nodes (you type):** `rename_columns(df)` (the X→name map below); `drop_id(df)`;
  `coerce_types(df)`; `handle_undocumented(df, params)` (decide: keep `EDUCATION
  5,6`→`4 other`, `MARRIAGE 0`→`3`, `PAY -2/0` policy); `dedup(df)`.
- **Reuse:** no dedicated knowledge notebook — author yourself; `clean_data`
  template in `kedro_nodes_and_pipelines.py` is the wiring shape only.
- **Params:** `data_cleaning` block (undocumented-category policy).
- **Test:** assert no `ID` col, renamed headers present, dtypes, row-count drop on dups.
- **Report → §3.**

### 3.3 `data_feat_engineering` — rubric components 1 (feature store) + features
- **Purpose:** engineer features over the 4 groups; persist to feature store.
- **Consumes:** `cleaned_data` (03_primary). **Produces:** `feature_table`
  (04_feature parquet) AND a Hopsworks feature-group write.
- **Nodes (you type):**
  - `engineer_features(df)` — derived features: `util_ratio = BILL_AMT/LIMIT_BAL`,
    `pay_delay_max = max(PAY_0..PAY_6)`, `avg_bill`, `avg_pay_amt`,
    `pct_paid = PAY_AMT/BILL_AMT`, age bands.
  - `to_feature_store(df, groups, settings)` — write the 4 feature groups to
    Hopsworks (demographic / payment_history / bill_history / payment_amounts).
  - `read_back_features(settings) -> df` — read the feature view back (beats the
    bank example, which only wrote). **Falls back to local parquet if no creds.**
- **Reuse:** `featuretools_dfs.py` (`build_entityset`/`run_dfs`) optional for
  automated features; `feature_stores.py` (`to_feature_store`,
  `get_feature_view_training_data`); lab `feature_utils.py`,
  `week_01/01_Feature_Store_Feature_Group_Creation.ipynb`.
- **Params:** `data_feat_engineering` (feature-group versions, derived-feature config).
- **Test:** `engineer_features` produces expected columns; feature-store funcs
  mocked (no live call in tests).
- **Report → §3** (feature importance later ties here).

### 3.4 `data_split` — (enables modeling + drift baseline)
- **Purpose:** stratified splits + **the drift baseline**.
- **Consumes:** `feature_table` (04_feature). **Produces:** `X_train,y_train,
  X_val,y_val,X_test,y_test` (05_model_input) + **`reference_distribution`**
  (03_primary parquet) + `drift_pca.pkl` (06_models) for multivariate drift.
- **Nodes (you type):** `split_data(df, params)` (stratified, seeded);
  `make_reference_distribution(X_train)` (snapshot for `data_drifts`);
  `fit_drift_pca(X_train)` (fit `ReconstructionDriftDetector`, save).
- **Reuse:** `kedro_nodes_and_pipelines.py:split_data`;
  `multivariate_drift_detection.py:ReconstructionDriftDetector.fit`.
- **Params:** `data_split` (already present: test 0.20 / val 0.10 / stratify / shuffle / seed).
- **Test:** split sizes + stratification ratio preserved; reference file written.
- **Report → §2** (planning) / §4 (drift setup).

### 3.5 `model_train` — rubric component 2 (MLflow) + tuning
- **Purpose:** train the candidate models with Optuna, log everything to MLflow.
- **Consumes:** `X_train,y_train,X_val,y_val` (05_model_input).
  **Produces:** `trained_models` + per-run MLflow logs; best per family to 06_models.
- **Nodes (you type):** `train_candidates(X_train,y_train,X_val,y_val,params)` —
  loop the 3 model families, run an Optuna study per family (YAML-driven search
  space), log params/metrics/model+signature to MLflow.
- **Reuse:** `mlflow_experiment_tracking.py`
  (`get_or_create_experiment`/`log_sklearn_run`);
  `optuna_hyperparameter_optimization.py` (`make_rf_objective`/`run_study`);
  lab `week_05/.../parameters_optuna.yml` (generic `suggest_*` dispatch);
  math [`bayesian_optimization`](../../_math/applied/bayesian_optimization.ipynb).
- **Params:** `model_train` (present: experiment name, `optuna_trials: 30`) +
  fill `candidate_models` list + `parameters_optuna.yml` search spaces.
- **Test:** objective returns a float in [0,1]; study completes n_trials.
- **Report → §3** (modelling).

### 3.6 `model_selection` — rubric components 2 (registry) + 3 (SHAP)
- **Purpose:** pick champion, register with alias, log SHAP.
- **Consumes:** `trained_models` + their val metrics (05/06). **Produces:**
  champion in MLflow registry (alias **Champion**); `shap_summary.png`
  (08_reporting via `MlflowArtifactDataset(MatplotlibDataset)`).
- **Nodes (you type):** `select_champion(models, metrics, params)` (max ROC-AUC →
  `register_and_alias(..., "Champion")`); `explain_champion(model, X_val)`
  (`shap.TreeExplainer` → `summary_plot(show=False)` → **return `plt`**).
- **Reuse:** `mlflow_experiment_tracking.py:register_and_alias`;
  `shap_explainability.py` (`explain_tree_model`/`global_importance`); lab
  `week_03/bank-example/.../model_train/nodes.py` (SHAP→plt→catalog logging);
  math [`shapley_values`](../../_math/applied/shapley_values.ipynb).
- **Params:** `model_selection` (set `primary_metric: roc_auc` — currently TODO; shap sample cap).
- **Test:** champion = max-metric model; SHAP returns a Figure.
- **Report → §3** (feature importance + explainability — a graded line).

### 3.7 `model_predict` — rubric component 4 (serving + containers)
- **Purpose:** serve the champion; batch + online inference.
- **Consumes:** `X_test` (05) + champion from registry. **Produces:**
  `predictions` (07_model_output) + `decision_log` + per-prediction SHAP; a
  running **FastAPI** app + **Dockerfile**.
- **Nodes (you type):** `batch_predict(X_test, params)` (load champion by alias,
  predict, threshold, log score distribution); `log_prediction_shap(...)`.
  **Serving (outside Kedro):** `app/main.py` (FastAPI, `lifespan` loads champion
  at startup, `/predict` + `/health` + `/ready`, Pydantic schema);
  `app/model/loader.py`; `Dockerfile`.
- **Reuse:** `fastapi_model_serving.py` (`create_app`/`make_load_test`); lab
  `week_05/spotify_recommender/app/main.py` (lifespan + probes),
  `week_05/.../Dockerfile`; concept
  [`batch-vs-online-inference`](../../_knowledge/batch-vs-online-inference.ipynb).
- **Params:** `model_predict` (present: registry URI, champion name/alias, threshold 0.5).
- **Test:** `batch_predict` shape/threshold; FastAPI via `TestClient` (`/health`,
  `/predict`).
- **Report → §4** (serving) / §5 (production — K8s scaling discussion here).

### 3.8 `data_drifts` — rubric component 5 (drift)
- **Purpose:** detect drift of a production sample vs the reference baseline.
- **Consumes:** `reference_distribution` (03), `drift_pca.pkl` (06), a current
  sample (a biased slice of `X_test` to *force* drift). **Produces:**
  `drift_report` + `monitoring_dashboard.html` (08_reporting).
- **Nodes (you type):** `make_current_sample(X_test, params)` (bias it, e.g.
  `AGE>=45`, to demonstrate detection); `univariate_drift(ref, cur)` (PSI bands +
  JS + KS per feature); `multivariate_drift(pca, cur)` (reconstruction error);
  `evidently_report(ref, cur)` (DataDriftPreset → HTML + `detect_dataset_drift`).
- **Reuse:** `drift_statistical_tests.py`
  (`calculate_psi`/`psi_band`/`js_distance`/`ks_test`);
  `multivariate_drift_detection.py:ReconstructionDriftDetector`;
  `evidently_drift_monitoring.py`; lab `week_06/01_PSI`,`02_JS`,`04_evidently`;
  math [`js_divergence`](../../_math/applied/js_divergence.ipynb).
- **Params:** `data_drifts` (present: ks 0.05, js 0.10, PSI 0.10/0.20) + fill
  `pca_recon_error_threshold`, `reference_window`, `current_window`.
- **Test:** PSI≈0 on identical samples, PSI≥0.2 on the biased sample.
- **Report → §3/§4** (drift results) / §5 (monitoring strategy).

---

## 4. Cross-cutting wiring

- **MLflow (kedro-mlflow):** wrap any artifact output (`shap_summary.png`,
  champion `.pkl`, GE JSON, drift HTML) in
  `kedro_mlflow.io.artifacts.MlflowArtifactDataset` in `catalog.yml` — the node
  just returns the object; logging is automatic. Registry uses **aliases**
  (Champion/Challenger), not deprecated stages.
- **Reproducibility:** `random_seed: 42` (globals/params) into every split/model;
  freeze versions with `uv pip freeze` for the report's package list.
- **Prefect (after the 8 pipelines run):** wrap the Kedro pipelines in
  `@flow`/`@task` (`prefect_orchestration.py`; lab `kedro_prefect_flow.py`),
  add a `CronSchedule` deployment for nightly drift+retrain.
- **`08_reporting/`** is the gather-point for all report figures.

## 5. Column rename map (`X` → real name) — for `data_cleaning`
`X1→LIMIT_BAL · X2→SEX · X3→EDUCATION · X4→MARRIAGE · X5→AGE ·
X6→PAY_0, X7→PAY_2, X8→PAY_3, X9→PAY_4, X10→PAY_5, X11→PAY_6 ·
X12..X17→BILL_AMT1..6 · X18..X23→PAY_AMT1..6 · Y→default` (drop `ID`).
Value codes: SEX{1,2} · EDUCATION{1,2,3,4}(+undoc 5,6) · MARRIAGE{1,2,3}(+undoc 0)
· PAY_*{-1..9}(+undoc -2,0).

## 6. Seven-day calendar (today 23/06 → deadline 30/06)

| Day | Phase | Deliverable |
|---|---|---|
| **1 (23/06)** | P0 + start P1 | deps+config green; `data_quality` passing |
| **2 (24/06)** | P1 | `data_cleaning` + `data_feat_engineering` (incl. Hopsworks) + `data_split` |
| **3 (25/06)** | P2 | `model_train` (MLflow + Optuna) |
| **4 (26/06)** | P2 | `model_selection` (champion + SHAP) |
| **5 (27/06)** | P3 | `model_predict` (FastAPI + Docker) |
| **6 (28/06)** | P4 | `data_drifts` (Evidently + PSI/JS + PCA) + Prefect wrap |
| **7 (29/06)** | P5 | tests + freeze + 6-page report; **30/06 buffer/submit** |

## 7. Report (6 pages) ← evidence each phase emits
1. **Data & goal + success metrics** — dataset rationale, ROC-AUC choice (P0/P1).
2. **Project planning** — this plan + sprint table (P0).
3. **Results** — EDA plots, model comparison table, **SHAP** importance (P1-P2).
4. **Production discussion** — serving, drift results, **K8s scaling**, risks +
   mitigations (the "Pandas→Spark +X weeks" framing) (P3-P5).
5. **Packages + versions** — frozen list (P5).
Front page: members, dataset, Git link, run instructions (REPORT_OUTLINE).

## 8. Open items to confirm during Phase 0
- GX ↔ Hopsworks version compatibility (install-time risk).
- Final `EDUCATION 5,6` / `MARRIAGE 0` / `PAY -2,0` cleaning policy.
- Confirm `primary_metric: roc_auc` + the 3 candidate models (defaults set above).
