# MLOps Project — Self-Coaching Roadmap

> Solo scaffolding from the empty Kedro shell at `Project/` to a working
> end-to-end pipeline by **23/06/2026** (one-week buffer before the **30/06**
> deadline). Today's anchor: 26/05/2026. Five sprint-weeks remain.

## Table of Contents

1. [Mindset baseline (re-read every session)](#1-mindset-baseline-re-read-every-session)
2. [5-sprint roadmap](#2-5-sprint-roadmap)
3. [Per-file learning sequence (worked example: `data_quality`)](#3-per-file-learning-sequence-worked-example-data_quality)
4. [How to use Claude as a coach, not a crutch — prompt patterns](#4-how-to-use-claude-as-a-coach-not-a-crutch--prompt-patterns)
5. [Notebook discipline](#5-notebook-discipline)
6. [Red flags — stop and re-learn](#6-red-flags--stop-and-re-learn)

---

## 1. Mindset baseline (re-read every session)

Pin these three rules above your screen. They compress the global
[Teaching Contract](../../../CLAUDE.md) into project form.

1. **I type every line.** Claude never hands me code I copy. If I receive
   a snippet longer than two lines, I retype it from the side and explain
   each line aloud before I keep it.
2. **Concept before code.** Before I open `nodes.py` for a pipeline, I've
   re-read its lecture and its lab, and I can answer in plain English:
   *what is this stage for, what does it consume, what does it produce,
   what would break downstream if I skipped it?*
3. **Hints, not fixes.** When stuck, I ask Claude to ask me a question —
   not to give me the answer. If I can't rephrase the hint as my own next
   action, the hint was too big.

The anti-dependency proof: at any moment I should be able to close all
chat windows and keep typing for 15 minutes.

---

## 2. 5-sprint roadmap

Order is non-negotiable: it follows [`../CLAUDE.md` §4](../CLAUDE.md#4-pipeline-order--tooling-from-the-pdf-and-weeks-1-6-lectures).
Sprint scope is sized by risk, not by pipeline count.

### Sprint 1 — Foundations + Data In (26/05 → 01/06)

- **Goal:** Dataset chosen & committed. `data_quality` and `data_cleaning`
  working end-to-end in their notebooks (not yet promoted to `nodes.py`).
  Kedro CLI runnable.
- **Pipelines / notebooks (in order):**
  [`01_data_quality.ipynb`](../notebooks/01_data_quality.ipynb) →
  [`data_quality/`](../src/my_mlops_project/pipelines/data_quality/);
  then `02_data_cleaning.ipynb` → `data_cleaning/`.
- **Re-read FIRST:** Lecture 1 PDF (Data Unit Tests, Feature Stores);
  [`Labs/week_01/.../01_Data_Unit_Tests.ipynb`](../../Labs/week_01/week_01/01_Data_Unit_Tests.ipynb);
  `Labs/week_03/.../bank-example/` for Kedro shape.
- **Smallest first code unit:** a node that takes `pd.DataFrame` and
  returns it with a full docstring (the placeholder is already there —
  replace it once you understand the signature).
- **Self-check:** `python -m pytest tests/` green;
  `python -m kedro run --pipeline data_quality` exits 0;
  one Great Expectations assertion fails on purpose when you corrupt a value.

### Sprint 2 — Features + Split (02/06 → 08/06)

- **Goal:** `data_feat_engineering` and `data_split` complete; `04_feature/`
  and `05_model_input/` artifacts exist on disk; **`reference_distribution.parquet`
  written** (required by `data_drifts` in Sprint 5).
- **Pipelines / notebooks:** `03_data_feat_engineering.ipynb`, `04_data_split.ipynb`.
- **Re-read FIRST:** Lecture 1 (Feature Management slides);
  `Labs/week_01/.../01_Feature_Store_Feature_Group_Creation.ipynb`,
  `02_Feature_Store_Feature_View.ipynb`.
- **Smallest first code unit:** a `split_train_test` node that takes a
  DataFrame + a `test_size: float` parameter and returns a `(train, test)`
  tuple.
- **Self-check:** shapes assert `len(train) + len(test) == len(df)`;
  target is present in both; `reference_distribution.parquet` exists in
  `data/03_primary/`.

### Sprint 3 — Train + Select (09/06 → 15/06)

- **Goal:** One trained model logged to MLflow with metrics; one Optuna
  sweep; best run promoted in the MLflow registry; SHAP **global** plot
  saved to `data/08_reporting/shap_summary.png`.
- **Pipelines / notebooks:** `05_model_train.ipynb`, `06_model_selection.ipynb`.
- **Re-read FIRST:** Lecture 2 PDF (MLflow, Optuna);
  `Labs/week_02/.../01_MLflow_intro.ipynb`, `02_Optuna_MLFlow.ipynb`;
  Lecture 6 on SHAP.
- **Smallest first code unit:** a `train_baseline` node that fits one
  default-hyperparam model and returns the fitted estimator — **no MLflow yet**.
- **Self-check:** `mlflow ui` shows ≥1 run with metric + parameter + artifact;
  `shap_summary.png` exists; the **PCA for multivariate drift** is fit and
  saved to `data/06_models/drift_pca.pkl` (Week 6 dependency).

### Sprint 4 — Serve (RISKIEST WEEK — 16/06 → 22/06)

- **Goal:** FastAPI endpoint returning predictions, loading the champion
  from the MLflow registry at startup (Week 5 lecture slide 35).
  **Stretch:** Docker image tagged by git SHA (never `:latest`).
- **Pipelines / notebooks:** `07_model_predict.ipynb`.
- **Re-read FIRST:** Lecture 4 + Lecture 5 PDFs (Containers, Model Serving,
  release patterns); `Labs/week_04/docker_recommendation`,
  `Labs/week_04/bank-example`.
- **Smallest first code unit:** a `predict_one(payload: dict) -> dict`
  pure function in `nodes.py`. Wrap it in FastAPI **only after** it works
  in the notebook.
- **Self-check:** `curl http://localhost:8000/predict` with a sample
  payload returns a JSON prediction; per-prediction SHAP values land in
  `data/08_reporting/shap_predictions.parquet`.
- **Honest risk note.** FastAPI + Docker on Windows historically eats
  whole weekends. **If by Fri 19/06 EOD** the FastAPI endpoint is not
  returning JSON for a hand-crafted payload, **cut Docker entirely** and
  document the cut in the report's risks section. The rubric rewards
  quality of report and code, not unfinished Docker images.

### Sprint 5 — Drift + Report + Buffer (23/06 only — hard stop)

- **Goal:** `data_drifts` produces PSI table + Evidently HTML +
  `monitoring_dashboard.html` (the single artifact the grader opens);
  6-page report PDF drafted; `kedro run` passes end-to-end.
- **Pipelines / notebooks:** `08_data_drifts.ipynb`, then the report.
- **Re-read FIRST:** Lecture 6 PDF (drift taxonomy, PSI bands, KS, JS,
  PCA reconstruction error); evidently.ai quickstart.
- **Smallest first code unit:** a `compute_psi(reference: pd.Series,
  current: pd.Series) -> float` function returning one value before
  reaching for Evidently. Then expand: KS for numerics, JS for
  categoricals, PCA-reconstruction-error for multivariate.
- **Self-check:** `monitoring_dashboard.html` opens in a browser and shows
  GE summary + training metrics + SHAP + drift table; the full
  `kedro run` ends in `Pipeline execution completed successfully`;
  PSI bands are interpreted in the report (<0.1 stable, <0.2 moderate,
  ≥0.2 significant).
- **Buffer:** 24/06 → 29/06 absorbs slippage. **No new features after 23/06.**

---

## 3. Per-file learning sequence (worked example: `data_quality`)

Apply this same 8-step pattern to all 8 pipelines. The folder is
[`data_quality/`](../src/my_mlops_project/pipelines/data_quality/) and
its notebook is
[`01_data_quality.ipynb`](../notebooks/01_data_quality.ipynb).

1. **Read the README, write the purpose in your own words.** Open
   `data_quality/README.md`. Then open `nodes.py` and **replace** the
   existing module docstring's "Purpose" line with your own rephrasing —
   same meaning, your wording.
   *Self-check:* if you re-read your sentence in 24 hours it still
   makes sense.
2. **Trace the data contract.** From the README "Inputs / Outputs", write
   a one-line comment at the top of `nodes.py`:
   `# in: raw_data (DataFrame, schema TODO) -> out: validated_data + ge_report`.
   *Self-check:* the contract matches [`../CLAUDE.md` §4](../CLAUDE.md#4-pipeline-order--tooling-from-the-pdf-and-weeks-1-6-lectures) for this pipeline.
3. **Open the notebook and load real data.** In `01_data_quality.ipynb`
   section 2, replace `df = pd.DataFrame()` with a real `pd.read_csv(...)`
   against your chosen dataset in `data/01_raw/`.
   *Self-check:* `df.shape` is non-zero.
4. **Sketch ONE assertion as a plain Python `assert`.** In notebook
   section 4: `assert df['target_col'].notna().all(), 'target has nulls'`.
   Just one. Run it.
   *Self-check:* flip the assertion (`.any()`) and confirm it fires.
5. **Lift that assertion into a Great Expectations expectation.**
   Translate to the GE syntax from
   [`Labs/week_01/.../01_Data_Unit_Tests.ipynb`](../../Labs/week_01/week_01/01_Data_Unit_Tests.ipynb)
   (`expect_column_values_to_not_be_null`).
   *Self-check:* suite returns `success: True` on clean data and
   `success: False` when you `df.loc[0, 'target_col'] = None`.
6. **Promote the working code into `nodes.py`.** Delete `placeholder_node`.
   Write `validate_raw(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]`.
   Apply the [course-level documentation style](../../CLAUDE.md#2-documentation-style--exhaustive-override-of-global-no-comments-default)
   (full docstring + line-by-line comments).
   *Self-check:* `from my_mlops_project.pipelines.data_quality.nodes import validate_raw`
   works from the notebook with no path hacks.
7. **Wire it into `pipeline.py`.** Uncomment Kedro imports; replace
   `return None` with
   `pipeline([node(func=validate_raw, inputs="raw_data", outputs=["validated_data", "ge_report"], name="validate_raw_node")])`.
   *Self-check:* `python -m kedro run --pipeline data_quality` runs.
8. **Write the test.** In `tests/pipelines/data_quality/test_nodes.py`:
   `test_validate_raw_passes_on_clean_df()` and
   `test_validate_raw_flags_nulls()`. Each builds a tiny `pd.DataFrame`
   literal.
   *Self-check:* `python -m pytest tests/pipelines/data_quality/ -v` →
   2 passed.

When all 8 steps are green, copy this checklist into a comment at the
top of `data_cleaning/nodes.py` and start again. By pipeline #4 you
won't need to re-read it.

---

## 4. How to use Claude as a coach, not a crutch — prompt patterns

Copy these verbatim. Notice none of them say "fix it" or "write it".

> **Pattern A — Stuck before typing.**
> "I'm about to write the `validate_raw` function in
> `data_quality/nodes.py`. Before I type anything, ask me three short
> questions that will tell you whether I actually understand what this
> function should do. Don't tell me the answers — just ask."

> **Pattern B — Stuck on an error.**
> "I wrote this code [paste 5-15 lines] and I'm getting [paste the full
> traceback]. Don't tell me the fix. Ask me one question that would
> lead me to find it myself."

> **Pattern C — Concept check.**
> "I just wrote [paste code]. Explain to me *why* the line `[line]`
> is necessary. If I removed it, what specifically would break and when?"

> **Pattern D — Smaller building block.**
> "I am trying to wire this Kedro pipeline and the abstraction is too
> big for me. Give me the smallest possible standalone Kedro
> pipeline — one node, one input, one output, no real logic — that I
> can type into a scratch file to feel how the pieces connect. Do not
> give me code for *my* pipeline yet."

> **Pattern E — Concept-to-code bridge.**
> "I've read the Great Expectations section of Lecture 1 and I
> understand what an expectation suite is conceptually. I don't
> understand how a suite becomes a Python object I can call from
> `nodes.py`. Without writing code for me, point at the 3-5 sentences
> in `Labs/week_01/.../01_Data_Unit_Tests.ipynb` that bridge that gap."

> **Pattern F — Code review on something I wrote.**
> "Here is the `validate_raw` function I just finished [paste]. Tell
> me one thing that is correct and *why* it works (per Teaching
> Contract rule 5). Then tell me one thing that is suspicious — but
> don't fix it; just point at the line and ask me what I think it does."

---

## 5. Notebook discipline

The 9 notebooks under [`../notebooks/`](../notebooks/) are
**scratchpads**, not deliverables. The deliverable is the code in
`src/.../pipelines/`. Rules:

- **Always export before reading**, even your own notebook (see
  [`../CLAUDE.md` §5](../CLAUDE.md#5-notebook-workflow-project-specific-paths)):

  ```powershell
  .\.venv-mlops\Scripts\python.exe -m jupyter nbconvert --to script `
    "notebooks\<file>.ipynb" --stdout 2>$null
  ```

- **Code lives in the notebook only while it's unstable.** The moment a
  function passes its assertion in section 5, promote to `nodes.py`
  (section 6 of every notebook lists the promotion steps). Then
  *replace* the notebook cell with
  `from my_mlops_project.pipelines.<pipe>.nodes import <fn>` and call
  it. Two copies of the same logic is a bug.
- **Never silently insert cells.** If you ask Claude to add a cell,
  Claude must (a) export the notebook fresh, (b) propose location,
  (c) wait for your "yes". Enforce this on yourself too.
- **Keep the TOC in sync.** Each notebook has a TOC at cell 0. When
  you add a section, update the TOC in the same edit.
- **Commit cadence.** Commit at the end of every step in section 3
  above (8 commits per pipeline). Format:
  `<pipeline>: <step-number> <what you did>` —
  e.g. `data_quality: 4 raw assertion on target nulls`.
- **Never commit `data/01_raw/<large file>`.** Sample only if
  < 5 MB. Otherwise document the download in the README.

---

## 6. Red flags — stop and re-learn

If any of these happen: close the chat, close the file, take a five-minute
walk, come back to the **previous** step.

1. **"I can't explain line 4 without re-reading it."** Stop. Add a
   comment to line 4 in your own words. If you can't write the comment,
   you don't own the line — revert it and rewrite from scratch.
2. **"I have three Claude responses open and I'm picking pieces from each."**
   You're pattern-matching, not thinking. Close all three. Re-state
   the problem out loud in one sentence. Type the smallest thing
   you're 100% sure of.
3. **"My pipeline works but I'm not sure why a test passes."** A test
   you don't understand is worse than no test. Open the test, comment
   every line, then deliberately break it to confirm it actually
   checks what you think.
4. **"I added 50+ lines without running anything."** The atomic unit is
   "write 3-10 lines → run → confirm → comment." If you skipped
   run/confirm three times in a row, your feedback loop is broken —
   revert to the last green state and restart smaller.
5. **"I'm copy-pasting from a lab notebook into a project file."** Labs
   are reference, not source. Open both side-by-side, **retype** (don't
   paste), and as you retype rename at least one variable to fit the
   project's domain. Retyping forces the parser in your head to actually run.
