# SAP Prognos - System Architecture

SAP Prognos is an enterprise-grade AI Demand Forecasting and Inventory Optimization platform. It bridges predictive machine learning with supply chain management to enable intelligent, proactive decision making.

## Architecture Overview

The system follows a classic decoupled architecture with a modern tech stack tailored for high performance, ease of deployment, and clear separation of concerns.

### 1. Frontend: SAPUI5 (Fiori Design Guidelines)
The user interface is built using SAPUI5, adhering to SAP Fiori design principles to provide a consistent, enterprise-ready user experience.
- **Components**: MVC architecture (`App.view.xml`, `App.controller.js`).
- **Features**: Real-time KPI dashboards, interactive charts (Chart.js integration), and dynamic data binding to backend REST APIs.
- **Hosting**: Served statically or via a lightweight HTTP server (`http-server`).

### 2. Backend: FastAPI (Python)
A high-performance asynchronous REST API framework serving as the core business logic layer.
- **Role**: Serves ML predictions, calculates inventory impacts, and provides system health metrics.
- **Validation**: Pydantic models enforce strict schema validation for all incoming requests (e.g., `SimulationRequest`, `ForecastRequest`).
- **Logging**: Structured logging using standard Python `logging` for auditability and debugging.

### 3. Machine Learning: XGBoost
The predictive engine relies on XGBoost, chosen for its efficiency with tabular time-series data.
- **Pipeline**: Historical sales data is preprocessed to extract lag features (`sales_lag_1`, `sales_lag_7`) and rolling means (`sales_roll_mean_7`).
- **Explainability**: Global feature importance (Gain) is extracted dynamically to explain predictions to the user in business terms ("Recent weekly demand is increasing").

### 4. Database: SQLite (Prototyping)
A lightweight relational database handles state management for inventory.
- **Schema**: Stores `current_stock`, `target_stock`, `lead_time_days`, `incoming_stock`, etc.
- **Logic**: The `inventory_service.py` evaluates stock levels against forecasted demand during lead time to categorize risk (CRITICAL, HIGH, MEDIUM, LOW).

## Request Flow Example: Simulation (`/simulate`)
1. **User Action**: The user adjusts the demand percentage on the SAPUI5 dashboard.
2. **Frontend Request**: SAPUI5 sends an HTTP POST request to FastAPI with the base features and adjustment parameters.
3. **Backend Processing**: 
   - Pydantic validates the request.
   - The ML model generates a base prediction.
   - Business logic applies the adjustments (promotions, seasonality, percentage tweaks).
   - `inventory_service` queries SQLite for current stock levels.
   - Shortage and reorder quantities are calculated.
4. **Response**: FastAPI returns the simulated forecast and inventory impact.
5. **UI Update**: SAPUI5 dynamically updates the charts and KPIs.
