"""Tests for the `data_quality` pipeline nodes.

Two behaviours matter: the gate PASSES on clean data, and it RAISES on a broken
batch. Uses the ``sample_raw_df`` fixture (tests/conftest.py) — never the real
file on disk.
"""
import pytest

from my_mlops_project.pipelines.data_quality.nodes import (
    validate_credit_data,
    gate_on_quality,
)

# The same shape as the conf/base/parameters.yml `data_quality` block.
DQ_PARAMS = {
    "expected_column_count": 25,
    "target_column": "default payment next month",
    "ranges": {"AGE": {"min": 18, "max": 100}, "LIMIT_BAL": {"min": 0}},
    "value_sets": {
        "SEX": [1, 2],
        "EDUCATION": [0, 1, 2, 3, 4, 5, 6],
        "MARRIAGE": [0, 1, 2, 3],
        "default payment next month": [0, 1],
    },
    "not_null": ["ID", "LIMIT_BAL", "AGE", "default payment next month"],
}


def test_validate_passes_on_clean_data(sample_raw_df):
    """A clean batch satisfies every expectation and the gate does not raise."""
    validated, report = validate_credit_data(sample_raw_df, DQ_PARAMS)
    assert report["success"] is True
    assert report["n_failed"] == 0
    # validated_data is the unchanged frame (validation, not cleaning).
    assert validated.shape == sample_raw_df.shape
    # The gate stays silent on a clean report.
    gate_on_quality(report)


def test_gate_raises_on_broken_batch(sample_raw_df):
    """An out-of-range AGE trips an expectation and the gate halts the run."""
    broken = sample_raw_df.copy()
    broken.loc[0, "AGE"] = -5  # impossible age -> ExpectColumnValuesToBeBetween fails

    _, report = validate_credit_data(broken, DQ_PARAMS)
    assert report["success"] is False
    assert report["n_failed"] >= 1

    with pytest.raises(ValueError, match="Data quality gate FAILED"):
        gate_on_quality(report)
