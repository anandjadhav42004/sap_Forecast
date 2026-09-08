# API Contract - SAP Prognos

This document specifies the actual API endpoints implemented in the FastAPI backend.

## Base URL
- **Local Development**: `http://localhost:8000`
- **Production**: `https://sap-forecast.onrender.com`

## 1. Forecast Demand
Generate an AI-powered demand forecast using XGBoost.

- **Method**: `POST`
- **Path**: `/forecast`
- **Request Body**:
  ```json
  {
    "store": 2,
    "item": 10,
    "date": "2018-01-01",
    "sales_lag_1": 41.0,
    "sales_lag_7": 45.0,
    "sales_roll_mean_7": 41.7
  }
  ```
- **Response**:
  ```json
  {
    "store": 2,
    "item": 10,
    "forecast_date": "2018-01-01",
    "predicted_demand": 42.5,
    "lower_bound": 37.0,
    "upper_bound": 48.0,
    "confidence_level": 0.85,
    "model": "XGBoost",
    "model_version": "1.0.0",
    "explainability": [
      {
        "factor": "Recent weekly demand is increasing",
        "impact_percentage": 45.2,
        "direction": "up"
      }
    ]
  }
  ```

## 2. Inventory Simulation
Simulate inventory impact with what-if scenarios.

- **Method**: `POST`
- **Path**: `/simulate`
- **Request Body**:
  ```json
  {
    "store": 2,
    "item": 10,
    "date": "2018-01-01",
    "sales_lag_1": 41.0,
    "sales_lag_7": 45.0,
    "sales_roll_mean_7": 41.7,
    "demand_adjustment_pct": 20.0,
    "is_promotion": true,
    "high_seasonality": false
  }
  ```
- **Response**: Returns `base_forecast`, `adjusted_forecast`, `current_stock`, `shortage`, `recommended_order`, and `risk`.

## 3. Anomaly Detection
Detect statistical outliers in historical data using Z-Scores.

- **Method**: `POST`
- **Path**: `/anomalies`
- **Request Body**: Array of `historical_sales` objects.
- **Response**: Array of detected anomalies where Z-Score absolute value > 2.0.

## 4. Reorder Alerts
Fetch global active reorder alerts for the dashboard.

- **Method**: `GET`
- **Path**: `/reorder-alerts`
- **Response**: Returns `count` and an array of `alerts` where current stock is near or below the reorder point.
