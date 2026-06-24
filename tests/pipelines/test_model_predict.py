"""Tests for `model_predict` — the batch node and the FastAPI serving app."""
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from fastapi.testclient import TestClient

from my_mlops_project.pipelines.model_predict.nodes import batch_predict

PARAMS = {"prediction_threshold": 0.5, "shap_sample": 50}


def _fitted_model_and_data():
    X, y = make_classification(
        n_samples=200, n_features=6, weights=[0.78, 0.22], random_state=0
    )
    X = pd.DataFrame(X, columns=[f"f{i}" for i in range(6)])
    model = RandomForestClassifier(n_estimators=20, random_state=0).fit(X, y)
    return model, X.iloc[:50]


def test_batch_predict_outputs():
    """Predictions have proba + decision; the log summarises the batch."""
    model, X_test = _fitted_model_and_data()
    predictions, log = batch_predict(X_test, model, PARAMS)

    assert {"default_proba", "prediction"} <= set(predictions.columns)
    assert len(predictions) == len(X_test)
    assert predictions["prediction"].isin([0, 1]).all()
    assert log["n_scored"] == len(X_test)
    assert 0.0 <= log["predicted_default_rate"] <= 1.0


def test_fastapi_serving(monkeypatch):
    """The API loads a model at startup and answers /health, /ready, /predict."""
    model, _ = _fitted_model_and_data()

    import app.main as main
    # Inject a tiny model instead of loading the real champion at startup.
    monkeypatch.setattr(main, "load_champion", lambda: model)

    with TestClient(main.app) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/ready").json()["ready"] is True

        resp = client.post("/predict", json={"features": {"f0": 0.5, "f1": -0.5}})
        assert resp.status_code == 200
        body = resp.json()
        assert 0.0 <= body["default_probability"] <= 1.0
        assert body["prediction"] in (0, 1)
