"""Node functions for the `data_split` pipeline.

Two nodes:

1. ``split_data`` — stratified, seeded train/validation/test split of the
   feature table (drops the feature-store id/time columns, separates the target).
2. ``make_reference_distribution`` — snapshot the training features as the drift
   baseline the ``data_drifts`` pipeline compares future data against.

Stratification preserves the ~22% default rate in every split; the fixed seed
makes the partition reproducible (rubric: "everyone produces the same results").

Class reference: Week 1 (data prep). Primary tooling: scikit-learn.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split


def split_data(
    feature_table: pd.DataFrame, params: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split the feature table into stratified train/val/test sets.

    The target and the feature-store identifier columns (``customer_id``,
    ``event_time``) are removed from the feature matrix. The split is done in two
    steps so the validation fraction is taken from the post-test remainder.

    Args:
        feature_table: The engineered features (from data_feat_engineering).
        params: The ``data_split`` params block (test_size, val_size, stratify,
            shuffle, target_column, id_columns).

    Returns:
        ``(X_train, X_val, X_test, y_train, y_val, y_test)`` — features as
        DataFrames, targets as single-column DataFrames (parquet-friendly).
    """
    target = params["target_column"]
    seed = params["random_seed"]

    # Feature matrix excludes the target and the id/time columns (not predictors).
    drop_cols = [target] + [c for c in params["id_columns"] if c in feature_table.columns]
    X = feature_table.drop(columns=drop_cols)
    y = feature_table[target]

    # Stratify on the target only for classification; honour the toggle.
    strat = y if params["stratify"] else None

    # Step 1: carve out the test set.
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y,
        test_size=params["test_size"],
        stratify=strat,
        shuffle=params["shuffle"],
        random_state=seed,
    )

    # Step 2: carve the validation set out of the remainder. Express val_size as
    # a fraction of the remaining rows so it stays val_size of the TOTAL.
    val_relative = params["val_size"] / (1.0 - params["test_size"])
    strat_temp = y_temp if params["stratify"] else None
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=val_relative,
        stratify=strat_temp,
        shuffle=params["shuffle"],
        random_state=seed,
    )

    print(
        f"split_data: train={X_train.shape} val={X_val.shape} test={X_test.shape} | "
        f"default rate train/val/test = "
        f"{y_train.mean():.3f}/{y_val.mean():.3f}/{y_test.mean():.3f}"
    )

    # Targets as single-column frames so the parquet datasets save cleanly.
    return (
        X_train,
        X_val,
        X_test,
        y_train.to_frame(),
        y_val.to_frame(),
        y_test.to_frame(),
    )


def make_reference_distribution(X_train: pd.DataFrame) -> pd.DataFrame:
    """Snapshot the training feature distribution as the drift baseline.

    The ``data_drifts`` pipeline compares production batches against this
    reference (PSI/JS per feature, PCA reconstruction error). Capturing it at
    split time fixes the baseline to the exact data the model trains on.

    Args:
        X_train: The training feature matrix.

    Returns:
        A copy of ``X_train`` to persist as ``reference_distribution``.
    """
    print(f"make_reference_distribution: baseline snapshot {X_train.shape}")
    return X_train.copy()
