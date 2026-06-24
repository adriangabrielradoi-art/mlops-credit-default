"""Tests for `data_drifts` — PSI behaviour and the control-vs-drift contrast."""
import numpy as np
import pandas as pd

from my_mlops_project.pipelines.data_drifts.nodes import (
    _psi,
    make_drift_samples,
    compute_drift,
    build_monitoring_dashboard,
)

PARAMS = {
    "sample_size": 500,
    "bias_column": "AGE",
    "bias_quantile": 0.6,
    "psi_threshold": 0.20,
    "ks_p_value_threshold": 0.05,
    "js_threshold": 0.10,
    "pca_components": 3,
    "pca_drift_ratio": 2.0,
}


def _reference():
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "AGE": rng.normal(40, 10, 3000),
        "BILL": rng.normal(50, 15, 3000),
        "PAY": rng.normal(0, 1, 3000),
    })


def test_psi_near_zero_for_identical():
    x = np.random.default_rng(1).normal(0, 1, 3000)
    assert _psi(x, x) < 0.01


def test_psi_large_for_shifted():
    rng = np.random.default_rng(2)
    assert _psi(rng.normal(0, 1, 3000), rng.normal(3, 1, 3000)) > 0.20


def test_make_drift_samples_biases_upward():
    clean, drifted = make_drift_samples(_reference(), PARAMS)
    assert drifted["AGE"].mean() > clean["AGE"].mean()


def test_compute_drift_clean_quiet_drifted_fires():
    ref = _reference()
    rng = np.random.default_rng(3)
    clean = pd.DataFrame({
        "AGE": rng.normal(40, 10, 500), "BILL": rng.normal(50, 15, 500), "PAY": rng.normal(0, 1, 500),
    })
    drifted = pd.DataFrame({  # shifted AGE + BILL
        "AGE": rng.normal(60, 10, 500), "BILL": rng.normal(90, 15, 500), "PAY": rng.normal(0, 1, 500),
    })
    summary, table = compute_drift(ref, clean, drifted, PARAMS)
    # The detector should flag more on the drifted batch than the clean one.
    assert summary["drifted"]["n_features_drifted"] > summary["clean"]["n_features_drifted"]
    assert summary["drifted"]["n_features_drifted"] >= 1
    assert {"feature", "psi", "js", "ks_pvalue", "drift"} <= set(table.columns)


def test_dashboard_is_html():
    ref = _reference()
    rng = np.random.default_rng(4)
    clean = ref.sample(500, random_state=1)
    drifted = pd.DataFrame({
        "AGE": rng.normal(60, 10, 500), "BILL": rng.normal(90, 15, 500), "PAY": rng.normal(0, 1, 500),
    })
    summary, table = compute_drift(ref, clean, drifted, PARAMS)
    html = build_monitoring_dashboard(summary, table)
    assert "<html" in html.lower()
    assert "Drift Monitoring" in html
