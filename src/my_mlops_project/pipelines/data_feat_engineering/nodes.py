"""Node functions for the `data_feat_engineering` pipeline.

Two nodes:

1. ``engineer_features`` — derive predictive features over the four credit
   feature groups (demographic / payment-status / bill / payment-amount), add a
   ``customer_id`` primary key and a dummy ``event_time`` (both required by the
   feature store), and return the feature table. This is the **canonical** local
   artifact every downstream pipeline uses.
2. ``sync_to_feature_store`` — write the feature groups to **Hopsworks** and read
   one back (round-trip proof). Fully wrapped so that if Hopsworks is
   unavailable (no creds / cluster down), it logs and returns a status WITHOUT
   failing the pipeline — the local feature table is the source of truth.

Class reference: Week 1 (feature store). Primary tooling: pandas, Hopsworks.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

# Repayment-status / bill / previous-payment column groups (post-cleaning names).
PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLS = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
PAYAMT_COLS = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]


def _safe_print(msg: str) -> None:
    """Print without ever raising on the Windows cp1252 console.

    Hopsworks error messages can contain non-ASCII characters (e.g. ``↳``) that
    crash a plain ``print`` on Windows — which would defeat the never-fail guard.
    """
    try:
        print(msg)
    except Exception:
        print(msg.encode("ascii", "replace").decode())


def engineer_features(cleaned_data: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Derive model-ready features and add feature-store keys.

    Adds behavioural features that summarise the six-month history into single
    signals a model (and SHAP) can use directly:
      * payment-status: max/mean delay, number of delayed months;
      * bill: average/max bill, recent-vs-old trend;
      * payment-amount: average/total paid;
      * cross-group: credit utilisation and repayment ratio.

    Args:
        cleaned_data: The cleaned primary table (from data_cleaning).
        params: The ``data_feat_engineering`` params block (primary_key,
            event_time).

    Returns:
        The feature table: original columns + derived features + ``customer_id``
        + ``event_time``.
    """
    df = cleaned_data.copy()

    # --- payment-status features (how late, how often) ---
    df["pay_delay_max"] = df[PAY_COLS].max(axis=1)            # worst delay across 6 months
    df["pay_delay_mean"] = df[PAY_COLS].mean(axis=1)          # average repayment status
    df["n_months_delayed"] = (df[PAY_COLS] > 0).sum(axis=1)   # count of months in arrears

    # --- bill features (how much, trending which way) ---
    df["avg_bill"] = df[BILL_COLS].mean(axis=1)
    df["max_bill"] = df[BILL_COLS].max(axis=1)
    df["bill_trend"] = df["BILL_AMT1"] - df["BILL_AMT6"]      # most-recent minus oldest

    # --- payment-amount features (how much they actually pay) ---
    df["avg_pay_amt"] = df[PAYAMT_COLS].mean(axis=1)
    df["total_pay"] = df[PAYAMT_COLS].sum(axis=1)

    # --- cross-group ratios ---
    # Credit utilisation: average bill relative to the credit limit.
    df["util_ratio"] = (df["avg_bill"] / df["LIMIT_BAL"]).replace([np.inf, -np.inf], 0).fillna(0)
    # Repayment ratio: total paid over total billed (guard against zero bills).
    total_bill = df[BILL_COLS].sum(axis=1)
    df["pct_paid"] = (df["total_pay"] / total_bill.where(total_bill > 0, np.nan)).fillna(0).clip(0, 2)

    # Feature store requires a primary key + an event-time column. The dataset is
    # a single snapshot, so event_time is a constant placeholder.
    df.insert(0, params["primary_key"], range(len(df)))
    df[params["event_time"]] = pd.Timestamp("2024-01-01")

    print(f"engineer_features: {cleaned_data.shape[1]} -> {df.shape[1]} columns ({df.shape[0]} rows)")
    return df


def _load_hopsworks_creds() -> Optional[dict]:
    """Load Hopsworks credentials from conf/local/credentials.yml or env vars.

    Resolves the credentials file relative to this module so it works regardless
    of the working directory. Returns None if neither source has a real key.

    Returns:
        Dict with FS_API_KEY / FS_PROJECT_NAME, or None.
    """
    import os
    import yaml

    # Project root is four parents up from this file (src/<pkg>/pipelines/<this>).
    creds_path = Path(__file__).resolve().parents[4] / "conf" / "local" / "credentials.yml"
    if creds_path.exists():
        creds = (yaml.safe_load(creds_path.read_text()) or {}).get("hopsworks", {})
        key = creds.get("FS_API_KEY", "")
        if key and "PASTE_YOUR" not in key:
            return {"FS_API_KEY": key, "FS_PROJECT_NAME": creds.get("FS_PROJECT_NAME")}
    # Fall back to environment variables.
    if os.getenv("FS_API_KEY"):
        return {"FS_API_KEY": os.getenv("FS_API_KEY"), "FS_PROJECT_NAME": os.getenv("FS_PROJECT_NAME")}
    return None


def sync_to_feature_store(feature_table: pd.DataFrame, params: dict[str, Any]) -> dict:
    """Write the feature groups to Hopsworks and read one back (best-effort).

    Demonstrates the feature store (write + read-back) but NEVER fails the
    pipeline: every Hopsworks interaction is guarded, and on any error the local
    ``feature_table`` remains the source of truth for downstream pipelines.

    Args:
        feature_table: The engineered features (from ``engineer_features``).
        params: The ``data_feat_engineering`` params block (primary_key,
            event_time, feature_group_version, feature_groups).

    Returns:
        A status dict (connected, feature_groups_written, rows_written,
        read_back_rows, note) — saved as a report artifact.
    """
    status: dict = {
        "connected": False,
        "feature_groups_written": [],
        "rows_written": 0,
        "read_back_rows": 0,
        "note": "",
    }

    creds = _load_hopsworks_creds()
    if creds is None:
        status["note"] = "No Hopsworks credentials found - skipped; local feature_table is canonical."
        _safe_print(status["note"])
        return status

    try:
        import os
        import hopsworks

        # Hopsworks hard-codes /tmp for SSL/Kafka files; create it on Windows.
        os.makedirs(os.path.abspath("/tmp"), exist_ok=True)
        project = hopsworks.login(
            api_key_value=creds["FS_API_KEY"], project=creds["FS_PROJECT_NAME"]
        )
        fs = project.get_feature_store()
        status["connected"] = True

        pk = params["primary_key"]
        et = params["event_time"]
        version = params["feature_group_version"]

        # Write each feature group (a versioned table keyed by customer_id).
        #
        # We write to the ONLINE store (online_enabled=True + storage="online").
        # On this free serverless cluster the OFFLINE store (Delta Lake -> HDFS)
        # rejects writes from an external Python client ("HDFS RPC listener
        # disconnected"); the online store (RonDB) uses a different path and works.
        for name, columns in params["feature_groups"].items():
            subset = feature_table[[pk, et] + columns].copy()
            fg = fs.get_or_create_feature_group(
                name=name,
                version=version,
                primary_key=[pk],
                event_time=et,
                online_enabled=True,
                description=f"Credit default — {name} feature group",
            )
            fg.insert(subset, storage="online")
            status["feature_groups_written"].append(name)

        status["rows_written"] = int(len(feature_table))
        status["storage"] = "online"

        # Read one group back from the online store to prove the round-trip.
        demo = fs.get_feature_group("credit_demographic", version=version)
        back = demo.read(online=True)
        status["read_back_rows"] = int(len(back))
        status["note"] = "Feature store write + read-back OK (online store)."
    except Exception as exc:  # noqa: BLE001 — deliberately broad: never fail the pipeline
        # Strip ANSI colour codes + non-ASCII so neither the JSON report nor the
        # Windows console chokes on the (Rust-coloured) Hopsworks error message.
        import re

        raw = f"Hopsworks step failed ({type(exc).__name__}: {exc})"
        clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)             # remove ANSI colours
        clean = " ".join(clean.split())                         # collapse whitespace/newlines
        status["note"] = (
            clean.encode("ascii", "replace").decode()
            + " — pipeline continues with the local feature_table."
        )

    _safe_print(status["note"])
    return status
