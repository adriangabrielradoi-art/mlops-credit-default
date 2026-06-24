"""Tests for the `data_cleaning` pipeline node.

Verifies the cleaning decisions: ID dropped, target renamed, undocumented
EDUCATION/MARRIAGE codes merged into "other", PAY_* left untouched.
"""
import pandas as pd

from my_mlops_project.pipelines.data_cleaning.nodes import clean_credit_data

# Mirrors the conf/base/parameters.yml `data_cleaning` block.
CLEAN_PARAMS = {
    "id_column": "ID",
    "target_column_raw": "default payment next month",
    "target_column": "default",
    "category_merges": {
        "EDUCATION": {"from": [0, 5, 6], "to": 4},
        "MARRIAGE": {"from": [0], "to": 3},
    },
}


def test_clean_structure_and_merges(sample_raw_df):
    """ID dropped, target renamed, undocumented codes merged, PAY untouched."""
    df = sample_raw_df.copy()
    # Inject undocumented category codes the cleaner must consolidate.
    df.loc[0, "EDUCATION"] = 5
    df.loc[1, "EDUCATION"] = 6
    df.loc[2, "EDUCATION"] = 0
    df.loc[0, "MARRIAGE"] = 0
    # A PAY value that is "undocumented" but must be preserved.
    df.loc[0, "PAY_0"] = -2

    out = clean_credit_data(df, CLEAN_PARAMS)

    # Structure.
    assert "ID" not in out.columns
    assert "default" in out.columns
    assert "default payment next month" not in out.columns

    # Undocumented categories consolidated into the documented set.
    assert set(out["EDUCATION"].unique()).issubset({1, 2, 3, 4})
    assert set(out["MARRIAGE"].unique()).issubset({1, 2, 3})

    # PAY_* left exactly as-is (the -2 must survive).
    assert "PAY_0" in out.columns
    assert -2 in out["PAY_0"].values


def test_clean_drops_duplicate_rows(sample_raw_df):
    """Exact duplicate rows are removed."""
    # Duplicate the frame so every row appears twice (post-ID-drop dedup).
    doubled = pd.concat([sample_raw_df, sample_raw_df], ignore_index=True)
    out = clean_credit_data(doubled, CLEAN_PARAMS)
    # Without ID, the 8 rows collapse back to the 4 unique customers.
    assert len(out) == len(sample_raw_df)
