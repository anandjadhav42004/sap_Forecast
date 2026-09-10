# Testing & Verification - SAP Prognos

## Backend Testing
The backend is tested using `pytest` and `httpx`.

**Run Tests:**
```bash
cd forecast-api
python -m pytest tests/test_api.py -v
```

**Coverage:**
- `test_health_check`: Verifies the model and database are loaded.
- `test_forecast`: Verifies the XGBoost model runs, returns bounds, and provides gain-based explainability.
- `test_simulate`: Verifies what-if scenarios (promotions, seasonality, adjustment pct) correctly modify the base forecast.
- `test_anomalies`: Verifies the Z-Score outlier detection logic correctly flags spikes and drops.
- `test_reorder_alerts`: Verifies the `/reorder-alerts` endpoint correctly returns a dict with `count` and `alerts`.

## Project Verification Script
A master verification script `verify_project.py` exists to validate the entire project structure, checking for the existence of models, databases, and critical backend/frontend files.

**Run Audit:**
```bash
python verify_project.py
```
