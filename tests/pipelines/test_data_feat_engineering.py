"""Tests for the `data_feat_engineering` pipeline.

Tests `engineer_features` only (pure, local). `sync_to_feature_store` is not
exercised here — it needs live Hopsworks credentials and is guarded to never
fail the pipeline.
"""
import pandas as pd

from my_mlops_project.pipelines.data_feat_engineering.nodes import engineer_features

FE_PARAMS = {"primary_key": "customer_id", "event_time": "event_time"}


def _cleaned(sample_raw_df) -> pd.DataFrame:
    """Approximate a cleaned frame from the raw fixture (drop ID, rename target)."""
    df = sample_raw_df.drop(columns=["ID"]).rename(
        columns={"default payment next month": "default"}
    )
    return df


def test_engineer_features_adds_expected_columns(sample_raw_df):
    """Derived features, primary key and event_time are all present."""
    out = engineer_features(_cleaned(sample_raw_df), FE_PARAMS)

    for col in [
        "customer_id", "event_time",
        "pay_delay_max", "pay_delay_mean", "n_months_delayed",
        "avg_bill", "max_bill", "bill_trend",
        "avg_pay_amt", "total_pay", "util_ratio", "pct_paid",
    ]:
        assert col in out.columns, f"missing engineered column {col}"

    # The primary key is unique per row.
    assert out["customer_id"].is_unique
    # util_ratio is finite (no inf/NaN from divide-by-zero).
    assert out["util_ratio"].notna().all()
    assert (out["util_ratio"].abs() < 1e9).all()


def test_engineer_features_values(sample_raw_df):
    """Spot-check a couple of derived values for correctness."""
    cleaned = _cleaned(sample_raw_df)
    out = engineer_features(cleaned, FE_PARAMS)
    # n_months_delayed counts PAY_* > 0; the fixture has no positive PAY values.
    assert (out["n_months_delayed"] == 0).all()
    # bill_trend = BILL_AMT1 - BILL_AMT6 (all bill cols equal in the fixture -> 0).
    assert (out["bill_trend"] == 0).all()
