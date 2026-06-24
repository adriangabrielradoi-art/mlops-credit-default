"""Node functions for the `data_cleaning` pipeline.

First value manipulation of the UCI Credit Card Default data. Turns the
validated raw frame (real-name columns, untouched values) into a clean
`03_primary` table ready for feature engineering.

The cleaning decisions — especially how undocumented category codes are handled
— are explained with the supporting evidence in
`notebooks/02_data_cleaning.ipynb`. Summary:

* drop the ``ID`` row identifier (not a feature);
* rename the spaced target ``default payment next month`` -> ``default``;
* merge undocumented EDUCATION codes {0,5,6} -> 4 (other) and MARRIAGE {0} -> 3
  (other) — rare (~1.2% / 0.2%) and unexplained, so "other" is the honest bucket;
* LEAVE the PAY_* columns untouched — their undocumented ``-2`` is common
  (~22% of rows) and meaningful (no credit used), part of an ordinal scale;
* drop exact duplicate rows; ensure integer dtypes.

Class reference: Week 1 (data prep). Primary tooling: pandas.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def clean_credit_data(validated_data: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Clean the validated credit frame into the primary modelling table.

    All steps are parameter-driven (see the ``data_cleaning`` block in
    parameters.yml) so the cleaning *policy* is config, not hard-code.

    Args:
        validated_data: The quality-passed frame from the data_quality pipeline
            (real-name columns, values unchanged, includes ``ID`` and the spaced
            target name).
        params: The ``data_cleaning`` params block (id_column, target_column_raw,
            target_column, category_merges).

    Returns:
        The cleaned DataFrame: no ``ID``, target renamed to ``default``,
        undocumented EDUCATION/MARRIAGE codes consolidated, deduplicated, int.
    """
    # Work on a copy so the upstream catalog object is never mutated in place.
    df = validated_data.copy()

    # 1. Drop the row identifier — it is an arbitrary key with no predictive
    #    value (same reasoning as dropping SK_ID in the Featuretools lab).
    df = df.drop(columns=[params["id_column"]])

    # 2. Rename the spaced target to a clean, code-friendly name.
    df = df.rename(columns={params["target_column_raw"]: params["target_column"]})

    # 3. Consolidate undocumented category codes into the "other" bucket.
    #    Each entry maps a list of source codes -> one destination code.
    for column, merge in params["category_merges"].items():
        replacement = {code: merge["to"] for code in merge["from"]}
        df[column] = df[column].replace(replacement)

    # NOTE: PAY_0/PAY_2..PAY_6 are deliberately NOT modified here. Their
    # undocumented -2 is ~22% of rows and represents a real state (no credit
    # used), so they stay as the ordinal repayment scale. See the notebook.

    # 4. Remove exact duplicate rows (after dropping the unique ID, genuine
    #    duplicates can surface). Report how many were removed.
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    n_removed = n_before - len(df)

    # 5. Every remaining column is integer-coded in this dataset — coerce to int
    #    so parquet/types are consistent downstream.
    df = df.astype(int)

    print(
        f"data_cleaning: dropped '{params['id_column']}', renamed target -> "
        f"'{params['target_column']}', merged {list(params['category_merges'])} "
        f"undocumented codes, removed {n_removed} duplicate rows -> {df.shape}"
    )
    return df
