# Serving — FastAPI champion API

Online inference for the credit-default champion model (rubric component 4:
*model serving + containers*). The batch counterpart is the Kedro
`model_predict` pipeline.

## Layout
```
serving/
├── app/
│   ├── main.py      FastAPI app: lifespan model-load, /predict, /health, /ready
│   └── loader.py    load champion: env pickle -> MLflow registry -> local pickle
├── requirements.txt minimal serving deps
└── Dockerfile       container image
```

## Run locally (no Docker)
From the project root, with the `.venv-mlops` env:
```powershell
$env:PYTHONPATH = "serving"
.\.venv-mlops\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Then:
```powershell
curl http://localhost:8000/health
curl http://localhost:8000/ready
# POST a feature dict to /predict (any missing engineered features default to 0):
```

## Run in Docker
Build from the **project root** (the context needs `serving/` and the model),
tagging by git SHA (never `:latest`, per the week-4 lecture):
```powershell
docker build -f serving/Dockerfile -t credit-default-api:dev .
docker run -p 8000:8000 credit-default-api:dev
```

## Endpoints
| Route | Method | Purpose |
|---|---|---|
| `/predict` | POST | `{"features": {...}}` -> `{default_probability, prediction, threshold}` |
| `/health` | GET | liveness (process up) |
| `/ready`  | GET | readiness (model loaded) |

## How the champion is loaded
`app/loader.py` resolves the model in this order: `CHAMPION_PATH` env (used by the
Docker image), then the **MLflow registry** alias `credit_default_champion@Champion`
(production-correct — loaded at startup, not baked in), then the local pickle.

## Production notes (report)
- One process per container; scale horizontally with more replicas behind a load
  balancer / Kubernetes (see report §production).
- Threshold is env-configurable (`PREDICTION_THRESHOLD`) for blue/green tweaks.
- In production the image stays model-agnostic and loads the champion from the
  registry at boot, so promoting a new champion needs no rebuild.
