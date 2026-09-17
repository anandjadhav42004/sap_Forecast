# ==============================================================================
# SAP Prognos — Enterprise Production Container
# Compatible with Docker, Kubernetes, and SAP AI Core (OCI Compliant)
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY forecast-api/requirements.txt /app/forecast-api/requirements.txt
RUN pip install --no-cache-dir -r /app/forecast-api/requirements.txt

# Copy application code and trained models
COPY models/ /app/models/
COPY forecast-api/ /app/forecast-api/
COPY frontend-ui5/ /app/frontend-ui5/

# Seed SQLite database if not present
RUN python /app/forecast-api/inventory_db.py

EXPOSE 8000 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/models/xgboost_model.json
ENV PORT=8000

WORKDIR /app/forecast-api

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
