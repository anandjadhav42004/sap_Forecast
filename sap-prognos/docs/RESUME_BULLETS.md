# SAP Prognos - Resume Bullets

*Use these bullets to highlight the technical depth and business impact of your final-year project.*

### Software Engineering & Architecture
- **Engineered a decoupled Enterprise AI platform** using a FastAPI (Python) microservices backend and a SAPUI5 Single Page Application (SPA) frontend, deployed via Render and Vercel.
- **Implemented SAP Fiori/Horizon design principles** to create a production-grade executive dashboard, including SAPUI5 Hash Routing, dynamic Component loading, and Role-Based Access Control (RBAC) for User/Admin flows.
- **Architected a robust REST API contract** using Pydantic for strict input validation, supporting end-to-end flows for ML forecasting, inventory simulation, and statistical anomaly detection.

### Machine Learning & Data Science
- **Developed a high-performance demand forecasting engine** utilizing XGBoost (`XGBRegressor`) trained on historical Store-Item data, achieving highly competitive MAPE metrics over traditional moving-average baselines.
- **Designed an Explainable AI (XAI) feature** that extracts real-time feature importance (Gain) from the XGBoost booster to dynamically explain demand drivers (Trend, Momentum, Seasonality) to business users.
- **Implemented a mathematical anomaly detection pipeline** using Pandas to calculate Z-Scores across time-series data, automatically identifying and surfacing historical sales outliers (>2 Std Dev).

### Supply Chain & Inventory Optimization
- **Built an automated inventory decision engine** that calculates Expected Lead-Time Demand, Safety Stock, and Days of Cover, automatically triggering real-time reorder recommendations to prevent stockouts.
- **Created a What-If Scenario Simulator** allowing supply chain planners to inject custom demand adjustments, promotional multipliers, and seasonal factors to instantly visualize projected inventory impact and shortage risks.
