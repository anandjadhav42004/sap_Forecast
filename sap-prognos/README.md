# SAP Prognos

**Enterprise AI Demand Forecasting and Inventory Optimization Platform**

SAP Prognos is an intelligent forecasting engine and supply chain dashboard built as a final year college project to demonstrate production-grade capabilities. It uses Machine Learning (XGBoost) to predict future demand and translates those predictions into actionable inventory insights.

## Features

*   **Intelligent Demand Forecasting**: Utilizes XGBoost to predict future demand based on historical sales, rolling averages, seasonality, and momentum.
*   **Inventory Optimization**: Integrates forecasts with realistic inventory parameters (lead time, target stock, safety stock) to generate automated reorder recommendations and risk alerts.
*   **Explainable AI**: Translates opaque ML predictions into transparent business drivers (e.g., "Recent weekly demand is increasing").
*   **Interactive SAPUI5 Dashboard**: A Fiori-style frontend providing real-time KPIs, simulation capabilities ("What-if" analysis for promotions), and inventory tracking.
*   **Anomaly Detection**: Identifies unexpected spikes or dips in historical data using statistical models.

## Tech Stack

*   **Frontend**: SAPUI5 (Fiori), HTML, JavaScript, Chart.js
*   **Backend API**: Python, FastAPI, Pydantic, Uvicorn
*   **Machine Learning**: XGBoost, Scikit-learn, Pandas
*   **Database**: SQLite (Prototype for Inventory State)

## Setup & Installation

### Prerequisites
*   Python 3.10+
*   Node.js & npm (for serving the frontend)

### 1. Backend Setup

1.  Navigate to the project root:
    ```bash
    cd sap-prognos
    ```
2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure Environment Variables:
    ```bash
    cp forecast-api/.env.example forecast-api/.env
    # Edit .env if necessary
    ```
5.  Seed the Database:
    ```bash
    python forecast-api/inventory_db.py
    ```
6.  Start the FastAPI Server:
    ```bash
    uvicorn forecast-api.main:app --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`. Swagger documentation is available at `http://localhost:8000/docs`.

### 2. Frontend Setup

1.  Open a new terminal window.
2.  Navigate to the UI directory:
    ```bash
    cd sap-prognos/frontend-ui5
    ```
3.  Serve the application (using `http-server` or similar):
    ```bash
    npx http-server -p 8080
    ```
4.  Access the application at `http://localhost:8080`.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed breakdown of the system components and request workflows.

## Verification & Testing

To verify the system setup and run the automated test suite:
```bash
# Verify structure and dependencies
python verify_project.py

# Run API Unit Tests
cd forecast-api
pytest tests/
```

## License
MIT
