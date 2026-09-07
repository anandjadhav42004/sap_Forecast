# SAP Prognos — Demand Forecasting

![SAP Fiori UI5](https://img.shields.io/badge/UI-SAPUI5-blue) ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688) ![Machine Learning](https://img.shields.io/badge/ML-XGBoost%20|%20Prophet-ff69b4)

SAP Prognos is an AI-powered demand forecasting prototype designed to provide intelligent, store-and-item-level sales predictions. It pairs a robust machine learning backend with a beautiful, modern **SAP Fiori Horizon** themed dashboard.

## 🌟 Key Features

- **Store & Item Level Forecasting:** Predict future demand for specific items at specific locations based on historical data.
- **Model Comparison:** Compare baseline models against advanced ML algorithms like **XGBoost** and **Prophet** (evaluated by MAPE).
- **Interactive Visualizations:** Built-in interactive line charts for comparing actual historical sales vs. forecasted points.
- **Fiori Horizon Theme:** Clean, flat, and modern UI leveraging native SAPUI5 components and micro-charts.

## 🛠️ Technology Stack

- **Frontend:** SAPUI5 (XML Views, JS Controllers, Custom CSS styling)
- **Backend API:** FastAPI (Python)
- **Data Prep & Modeling:** Pandas, Scikit-learn, XGBoost, Prophet

## 🚀 How to Run

To run the application locally, you will need to start both the Python backend API and the SAPUI5 frontend server. **Please run these in two separate terminal windows.**

### 1. Start the Backend API (FastAPI)
The backend requires the Python virtual environment to be active so it can access XGBoost and FastAPI.

```bash
# 1. Go to the project root directory
cd "sap-prognos"

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Start the FastAPI server on port 8000
uvicorn forecast-api.main:app --reload --port 8000
```
*The API will be available at `http://localhost:8000`. If you get an "Address already in use" error, clear the port by running: `lsof -ti:8000 | xargs kill -9`*

### 2. Start the Frontend Dashboard (SAPUI5)
In a **new** terminal window, start a simple HTTP server to serve the frontend UI.

```bash
# 1. Navigate to the frontend webapp directory
cd "sap-prognos/frontend-ui5/webapp"

# 2. Start the HTTP server on port 8080
python3 -m http.server 8080
```
*The enterprise dashboard will now be live at `http://localhost:8080`. (Do not press `Ctrl+C` in this terminal while you are using the app, as it will stop the server).*

## 📂 Project Structure
- `sap-prognos/frontend-ui5/`: Contains the SAPUI5 frontend application.
- `sap-prognos/forecast-api/`: Contains the FastAPI application logic.
- `sap-prognos/models/`: Scripts for training and evaluating machine learning models.
- `sap-prognos/data-prep/`: Data preparation and cleaning pipelines.
# Sap-Prognos-
# sap_Forecast
