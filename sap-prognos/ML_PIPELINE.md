# ML Pipeline - SAP Prognos

The SAP Prognos ML pipeline is built on XGBoost, optimized for fast inference and high explainability.

## 1. Feature Engineering
The model requires specific time-series lag features.
- `store`: Int
- `item`: Int
- `day_of_week`: Derived from Date (0-6)
- `month`: Derived from Date (1-12)
- `year`: Derived from Date
- `is_weekend`: Binary (1 if day_of_week >= 5 else 0)
- `sales_lag_1`: Previous day's sales
- `sales_lag_7`: Sales exactly one week ago
- `sales_roll_mean_7`: 7-day rolling average

## 2. Model Training
The model is an `XGBRegressor` trained on historical Store-Item data. 
- **Objective Function**: `reg:squarederror`
- **Evaluation Metric**: MAPE & RMSE
- **Format**: Exported as `xgboost_model.json`.

## 3. Real-Time Explainability
Instead of using complex SHAP values which add latency, the API queries the XGBoost Booster for real-time feature importance (Gain). 
- **Trend Impact**: Calculated using `sales_roll_mean_7`.
- **Momentum Impact**: Calculated using `sales_lag_1`.
- **Seasonality Impact**: Calculated using `day_of_week`.

These gains are normalized to 100% and returned to the UI as "AI Drivers", providing immediate business context for the forecast.
