# SAP Prognos: AI-Powered Demand Forecasting & Inventory Optimization System
**Final Year Project Report**

## 1. Abstract
Supply chain inefficiencies, stockouts, and overstocking cost enterprises millions annually. SAP Prognos is a prototype Enterprise AI system designed to bridge the gap between predictive machine learning and actionable inventory management. Built with an XGBoost forecasting engine, a FastAPI backend, and an SAPUI5 frontend, the system provides highly accurate demand predictions, real-time inventory risk analysis, and actionable reorder recommendations.

## 2. Introduction
Traditional inventory systems rely heavily on static reorder points and moving averages, which fail to adapt to dynamic market conditions like weekends, promotions, and sudden trends. SAP Prognos introduces an intelligent layer that forecasts future demand using machine learning and translates that demand into tangible supply chain decisions (Days of Cover, Expected Shortage, Recommended Order).

## 3. System Architecture
The system follows a decoupled, modern architecture:
- **Frontend**: SAPUI5 (Fiori Design Guidelines). Hosted statically on Vercel. Features Role-Based Access Control, Hash Routing, and dynamic data binding.
- **Backend**: FastAPI (Python). Hosted on Render. Provides RESTful endpoints for forecasting, simulation, anomalies, and inventory lookups.
- **Database**: SQLite (Prototype for SAP HANA). Stores real-time inventory state, target stocks, and lead times.
- **ML Engine**: XGBoost. Pickled/JSON model loaded into memory on backend startup.

## 4. Machine Learning Methodology
- **Model**: `XGBRegressor` chosen for its speed, ability to handle non-linear tabular data, and explainability features.
- **Features Engineered**: `sales_lag_1`, `sales_lag_7`, `sales_roll_mean_7`, `day_of_week`, `is_weekend`, `month`.
- **Explainable AI (XAI)**: Instead of black-box predictions, the API queries the booster's `Gain` metrics in real-time to quantify whether momentum, seasonality, or long-term trends are driving the current forecast up or down.

## 5. Inventory Optimization Logic
SAP Prognos does not stop at forecasting. It applies standard supply chain mathematics:
- **Expected Lead-Time Demand** = `Forecasted Daily Demand * Lead Time (Days)`
- **Shortage Risk** = If `Expected Lead-Time Demand > (Current Stock + Incoming Stock)`, the item is flagged as *High Risk*.
- **Recommended Order** = `Target Stock - (Current Stock + Incoming Stock)`

## 6. What-If Simulation
The platform features a Simulator page where planners can adjust the baseline ML forecast by:
- Percentage Adjustments (e.g., +20% expected foot traffic)
- Promotional Multipliers (+15%)
- High Seasonality Multipliers (+10%)
The system instantly recalculates the inventory impact and updates the recommended order quantity based on the simulated scenario.

## 7. Anomaly Detection
To prevent bad historical data from corrupting future forecasts, the system includes a Z-Score based statistical anomaly detector. It calculates the mean and standard deviation of historical sales arrays, flagging any data points with a `|Z-Score| > 2.0` as unexpected spikes or drops.

## 8. Conclusion & Future Scope
SAP Prognos successfully demonstrates how machine learning can be integrated into an enterprise UI to solve real-world inventory problems. 
**Future Scope**:
- Integration with live SAP S/4HANA instances via OData services.
- Replacement of SQLite with SAP HANA Cloud.
- Implementation of deep learning (LSTMs) for multi-horizon forecasting.
- Enterprise SSO (OAuth2/SAML) for authentication.

*(Note: To generate the required .pdf or .docx version of this report, open this markdown file in VS Code or Typora and select "Export to PDF/Word", or use an online Markdown to PDF converter).*
