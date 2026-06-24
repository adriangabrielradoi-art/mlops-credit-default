"""Tests for the `data_split` pipeline.

Checks the split sizes, that stratification preserves the class balance, that
the target does not leak into the feature matrix, and that the reference
distribution matches the training features.
"""
import numpy as np
import pandas as pd

from my_mlops_project.pipelines.data_split.nodes import (
    split_data,
    make_reference_distribution,
)

SPLIT_PARAMS = {
    "test_size": 0.20,
    "val_size": 0.10,
    "stratify": True,
    "shuffle": True,
    "random_seed": 42,
    "target_column": "default",
    "id_columns": ["customer_id", "event_time"],
}


def _synthetic_features(n: int = 1000) -> pd.DataFrame:
    """A feature-table-shaped frame with a ~22% imbalanced target."""
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "customer_id": range(n),
            "event_time": pd.Timestamp("2024-01-01"),
            "f1": rng.normal(size=n),
            "f2": rng.normal(size=n),
            "default": (rng.random(n) < 0.22).astype(int),
        }
    )


def test_split_sizes_and_no_leakage():
    """Splits sum to the whole, and the id/target columns are excluded."""
    df = _synthetic_features(1000)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(df, SPLIT_PARAMS)

    # Sizes: 70 / 10 / 20 of 1000 (+/- rounding).
    assert len(X_test) == 200
    assert len(X_val) == 100
    assert len(X_train) == 700
    assert len(X_train) + len(X_val) + len(X_test) == len(df)

    # No leakage: target and id columns are not in the feature matrix.
    for bad in ("default", "customer_id", "event_time"):
        assert bad not in X_train.columns


def test_stratification_preserves_class_balance():
    """Each split keeps roughly the overall ~22% positive rate."""
    df = _synthetic_features(2000)
    _, _, _, y_train, y_val, y_test = split_data(df, SPLIT_PARAMS)
    overall = df["default"].mean()
    for y in (y_train, y_val, y_test):
        assert abs(y["default"].mean() - overall) < 0.03


def test_reference_distribution_matches_training_features():
    """The drift baseline equals the training feature matrix."""
    df = _synthetic_features(500)
    X_train, *_ = split_data(df, SPLIT_PARAMS)
    ref = make_reference_distribution(X_train)
    assert ref.shape == X_train.shape
    assert list(ref.columns) == list(X_train.columns)
