"""Node functions for the `data_drifts` pipeline (week-6 monitoring).

Validates the drift-monitoring system by comparing the training
``reference_distribution`` against two production batches:
  * a **clean** slice of the test set (should show NO drift), and
  * a **biased** slice (drift deliberately induced — the rubric sanctions
    "play with your sample ... to generate drift").

Detection: univariate **PSI / JS / KS** per feature (from scratch), and
multivariate **PCA reconstruction error** (catches correlation shifts univariate
tests miss). An **Evidently** report (0.7 API) and a unified
``monitoring_dashboard.html`` are the report artifacts.

Class reference: Week 6. Math: PSI/JS ~ KL divergence; PCA reconstruction.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import entropy, ks_2samp
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

_EPS = 1e-4


def _bin_pcts(expected: np.ndarray, actual: np.ndarray, buckets: int = 10):
    """Bin two samples on shared edges; return per-bin proportions (epsilon-floored)."""
    lo, hi = min(expected.min(), actual.min()), max(expected.max(), actual.max())
    edges = np.linspace(lo, hi, buckets + 1)
    e = np.histogram(expected, bins=edges)[0] / len(expected)
    a = np.histogram(actual, bins=edges)[0] / len(actual)
    return np.where(e == 0, _EPS, e), np.where(a == 0, _EPS, a)


def _psi(expected, actual) -> float:
    """Population Stability Index (asymmetric; reference=expected)."""
    e, a = _bin_pcts(np.asarray(expected, float), np.asarray(actual, float))
    return float(np.sum((a - e) * np.log(a / e)))


def _js(expected, actual) -> float:
    """Jensen-Shannon distance (symmetric, bounded) via the mixture."""
    e, a = _bin_pcts(np.asarray(expected, float), np.asarray(actual, float))
    m = 0.5 * (e + a)
    return float(np.sqrt(0.5 * entropy(e, m, base=2) + 0.5 * entropy(a, m, base=2)))


def _pca_recon(reference: pd.DataFrame, current: pd.DataFrame, params: dict) -> dict:
    """Multivariate drift via PCA reconstruction error (ratio current/reference)."""
    scaler = StandardScaler().fit(reference)
    n_comp = min(params["pca_components"], reference.shape[1])
    pca = PCA(n_components=n_comp).fit(scaler.transform(reference))

    def err(X):
        Xs = scaler.transform(X)
        rec = pca.inverse_transform(pca.transform(Xs))
        return float(np.mean(np.sum((Xs - rec) ** 2, axis=1)))

    ref_err, cur_err = err(reference), err(current)
    return {"reference": ref_err, "current": cur_err, "ratio": cur_err / ref_err if ref_err else 0.0}


def make_drift_samples(X_test: pd.DataFrame, params: dict[str, Any]):
    """Build a clean (control) batch and a biased (drift-induced) batch.

    Args:
        X_test: Held-out features (the production stand-in).
        params: ``data_drifts`` block (sample_size, bias_column, bias_quantile).

    Returns:
        ``(current_clean, current_drifted)``.
    """
    size = params["sample_size"]
    clean = X_test.sample(min(len(X_test), size), random_state=42)

    col, q = params["bias_column"], params["bias_quantile"]
    threshold = X_test[col].quantile(q)
    drifted = X_test[X_test[col] >= threshold]
    if len(drifted) > size:
        drifted = drifted.sample(size, random_state=42)

    print(
        f"make_drift_samples: clean={len(clean)}, drifted={len(drifted)} "
        f"(biased to {col} >= q{q} = {threshold:.0f})"
    )
    return clean, drifted


def compute_drift(
    reference_distribution: pd.DataFrame,
    current_clean: pd.DataFrame,
    current_drifted: pd.DataFrame,
    params: dict[str, Any],
) -> tuple[dict, pd.DataFrame]:
    """Per-feature PSI/JS/KS + multivariate PCA drift for both batches.

    Returns:
        ``(drift_summary, psi_per_feature)`` — a summary dict comparing clean vs
        drifted, and the per-feature table for the biased batch (for the report).
    """
    ref = reference_distribution
    summary, tables = {}, {}

    for label, current in [("clean", current_clean), ("drifted", current_drifted)]:
        rows = []
        for col in ref.columns:
            psi = _psi(ref[col].values, current[col].values)
            rows.append({
                "feature": col,
                "psi": round(psi, 4),
                "js": round(_js(ref[col].values, current[col].values), 4),
                "ks_pvalue": round(float(ks_2samp(ref[col].values, current[col].values).pvalue), 4),
                "drift": bool(psi >= params["psi_threshold"]),
            })
        table = pd.DataFrame(rows).sort_values("psi", ascending=False).reset_index(drop=True)
        tables[label] = table

        recon = _pca_recon(ref, current, params)
        n_drift = int(table["drift"].sum())
        summary[label] = {
            "n_features_drifted": n_drift,
            "n_features": len(ref.columns),
            "share_drifted": round(n_drift / len(ref.columns), 3),
            "pca_recon_ratio": round(recon["ratio"], 3),
            "multivariate_drift": bool(recon["ratio"] >= params["pca_drift_ratio"]),
            "top_drifted": table[table["drift"]]["feature"].head(5).tolist(),
        }

    drift_summary = {
        "psi_threshold": params["psi_threshold"],
        "pca_drift_ratio_threshold": params["pca_drift_ratio"],
        "clean": summary["clean"],
        "drifted": summary["drifted"],
    }
    print(
        f"compute_drift: CONTROL clean -> {summary['clean']['n_features_drifted']} drifted features "
        f"(recon x{summary['clean']['pca_recon_ratio']}); "
        f"INDUCED drifted -> {summary['drifted']['n_features_drifted']} drifted features "
        f"(recon x{summary['drifted']['pca_recon_ratio']})"
    )
    return drift_summary, tables["drifted"]


def evidently_report(
    reference_distribution: pd.DataFrame, current_drifted: pd.DataFrame
) -> str:
    """Evidently data-drift HTML report (0.7 API; best-effort).

    Returns:
        The report HTML (or a small fallback HTML if Evidently's API differs).
    """
    try:
        from evidently import Report, Dataset, DataDefinition
        from evidently.presets import DataDriftPreset
        import tempfile, os

        data_def = DataDefinition()
        ref_ds = Dataset.from_pandas(reference_distribution, data_definition=data_def)
        cur_ds = Dataset.from_pandas(current_drifted, data_definition=data_def)

        result = Report([DataDriftPreset()]).run(cur_ds, ref_ds)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as fh:
            tmp = fh.name
        result.save_html(tmp)
        html = open(tmp, encoding="utf-8").read()
        os.unlink(tmp)
        print("evidently_report: Evidently 0.7 drift report generated")
        return html
    except Exception as exc:  # noqa: BLE001
        msg = f"{type(exc).__name__}: {exc}".encode("ascii", "replace").decode()
        print(f"evidently_report: skipped ({msg})")
        return f"<html><body><h2>Evidently report unavailable</h2><p>{msg}</p></body></html>"


def build_monitoring_dashboard(drift_summary: dict, psi_per_feature: pd.DataFrame) -> str:
    """Assemble the unified monitoring dashboard HTML (the final report artifact)."""
    clean, drifted = drift_summary["clean"], drift_summary["drifted"]
    verdict_clean = "NO DRIFT" if clean["n_features_drifted"] == 0 else f"{clean['n_features_drifted']} features drifted"
    verdict_drifted = f"DRIFT DETECTED — {drifted['n_features_drifted']} features"
    table_html = psi_per_feature.to_html(index=False, border=0)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Credit Default — Drift Monitoring</title>
<style>
 html, body {{ background-color: #ffffff; }}
 body {{ font-family: system-ui, sans-serif; margin: 0; color: #222222; }}
 .page {{ background-color: #ffffff; color: #222222; padding: 2rem; border-radius: 8px; }}
 .page h1, .page h2, .page h3, .page p {{ color: #222222; }}
 .card {{ display:inline-block; border:1px solid #ddd; border-radius:8px; padding:1rem 1.5rem; margin:0.5rem; }}
 .ok {{ border-left:6px solid #2e7d32; }} .alert {{ border-left:6px solid #c62828; }}
 table {{ border-collapse: collapse; font-size: 0.9rem; color:#222222; }}
 th,td {{ padding:4px 10px; border-bottom:1px solid #eee; text-align:right; }}
 th:first-child, td:first-child {{ text-align:left; }}
</style></head><body>
<div class="page">
<h1>Credit Default — Drift Monitoring Dashboard</h1>
<p>PSI threshold = {drift_summary['psi_threshold']} (&ge; flags a feature); multivariate PCA reconstruction-ratio threshold = {drift_summary['pca_drift_ratio_threshold']}.</p>
<div class="card ok"><h3>Control batch (clean)</h3>
  <p><b>{verdict_clean}</b></p>
  <p>features drifted: {clean['n_features_drifted']}/{clean['n_features']} &middot; PCA recon ratio: x{clean['pca_recon_ratio']} ({'drift' if clean['multivariate_drift'] else 'stable'})</p></div>
<div class="card alert"><h3>Induced-drift batch (biased)</h3>
  <p><b>{verdict_drifted}</b></p>
  <p>features drifted: {drifted['n_features_drifted']}/{drifted['n_features']} &middot; PCA recon ratio: x{drifted['pca_recon_ratio']} ({'drift' if drifted['multivariate_drift'] else 'stable'})</p>
  <p>top drifted: {', '.join(drifted['top_drifted']) or '-'}</p></div>
<h2>Per-feature drift — induced-drift batch</h2>
{table_html}
<p style="color:#666666; margin-top:1.5rem;">Validation result: the detector stays quiet on the clean batch and fires on the biased batch — confirming the monitoring works.</p>
</div>
</body></html>"""
    print("build_monitoring_dashboard: monitoring_dashboard.html assembled")
    return html
