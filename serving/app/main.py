"""FastAPI service for the credit-default champion model.

Patterns (week 4/5 serving lecture + lab):
- ``lifespan`` loads the champion ONCE at startup (not per request, not baked
  into the image — see ``loader.py``).
- ``/predict`` validates the request with Pydantic and returns the default
  probability + decision.
- ``/health`` (liveness) and ``/ready`` (readiness) probes for the orchestrator.

Run locally:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.loader import load_champion

# Classification cutoff (overridable via env for blue/green threshold tweaks).
THRESHOLD = float(os.getenv("PREDICTION_THRESHOLD", "0.5"))


class PredictRequest(BaseModel):
    """One applicant as a {feature_name: value} mapping.

    Accepting a dict keeps the API robust to the 30+ engineered features without
    a brittle hand-listed schema; the model's own feature order is applied.
    """

    features: dict[str, float] = Field(..., description="feature name -> value")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the champion once at startup; clear it on shutdown."""
    app.state.model = load_champion()
    yield
    app.state.model = None


app = FastAPI(title="Credit Default Champion API", version="1.0.0", lifespan=lifespan)


@app.post("/predict")
def predict(req: PredictRequest) -> dict:
    """Return the default probability + decision for one applicant.

    Raises:
        HTTPException: 503 if the model is not loaded yet.
    """
    model = getattr(app.state, "model", None)
    if model is None:
        raise HTTPException(status_code=503, detail="model not loaded")

    # Order the incoming features to match what the model was trained on.
    cols = list(getattr(model, "feature_names_in_", []))
    row = pd.DataFrame([req.features])
    if cols:
        # Fill any missing expected columns with 0, drop unexpected ones.
        for c in cols:
            if c not in row.columns:
                row[c] = 0.0
        row = row[cols]

    proba = float(model.predict_proba(row)[:, 1][0])
    return {
        "default_probability": round(proba, 4),
        "prediction": int(proba >= THRESHOLD),
        "threshold": THRESHOLD,
    }


@app.get("/health")
def health() -> dict:
    """Liveness probe: the process is up."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    """Readiness probe: the model has finished loading."""
    return {"ready": getattr(app.state, "model", None) is not None}
