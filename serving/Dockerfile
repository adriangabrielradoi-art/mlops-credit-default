# Serve the credit-default champion behind FastAPI + uvicorn.
# Build from the PROJECT ROOT so the context can see serving/ and data/06_models/:
#   docker build -f serving/Dockerfile -t credit-default-api:$(git rev-parse --short HEAD) .
# (tag by git SHA, never :latest, per the week-4 lecture).
FROM python:3.13-slim

WORKDIR /srv

# Dependencies first (least-frequently-changed layer -> better build cache).
COPY serving/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code, then the champion model. The demo bakes the model in via CHAMPION_PATH;
# in production the container would load it from the MLflow registry at startup
# (see app/loader.py) so one image serves many model versions.
COPY serving/app ./app
COPY data/06_models/champion_model.pkl ./model/champion_model.pkl
ENV CHAMPION_PATH=/srv/model/champion_model.pkl

# Run as a non-root user (good practice).
RUN useradd -m appuser && chown -R appuser /srv
USER appuser

EXPOSE 8000
# One process per container; scale horizontally with more containers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
