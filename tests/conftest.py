"""Shared pytest fixtures.

Fixtures defined here are auto-discovered by pytest and available to
every test in ``tests/``. Add small, deterministic synthetic DataFrames
here once the dataset schema is known.

TODO(dataset): once the dataset is chosen, add a ``sample_raw_df``
fixture returning a tiny in-memory DataFrame that matches the real
schema. Tests should never touch ``data/01_raw/`` on disk.
"""

import pandas as pd
import pytest


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    """A tiny, valid UCI Credit Card Default frame (real 25-column schema).

    Four clean rows matching the columns produced by reading the raw .xls with
    ``header=1``. Tests use this instead of touching ``data/01_raw/`` on disk.
    """
    cols: dict = {
        "ID": [1, 2, 3, 4],
        "LIMIT_BAL": [20000, 120000, 50000, 90000],
        "SEX": [2, 1, 2, 1],
        "EDUCATION": [2, 2, 1, 3],
        "MARRIAGE": [1, 2, 1, 2],
        "AGE": [24, 47, 33, 52],
    }
    # The six repayment-status columns (note the PAY_0 / PAY_2.. quirk).
    for c in ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]:
        cols[c] = [0, 0, -1, 0]
    # Bill-statement and previous-payment amounts.
    for c in ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]:
        cols[c] = [3913, 1000, 500, 0]
    for c in ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]:
        cols[c] = [0, 1000, 200, 0]
    cols["default payment next month"] = [1, 0, 0, 1]
    return pd.DataFrame(cols)
