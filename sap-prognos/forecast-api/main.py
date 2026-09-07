from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import pandas as pd
import xgboost as xgb
import os
import sys

# Add current directory to path to allow importing inventory_service when running from root
sys.path.append(os.path.dirname(__file__))
import inventory_service

app = FastAPI(title="SAP Prognos Forecast API", description="Demand forecasting API for SAP Prognos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'xgboost_model.json')
model = xgb.XGBRegressor()
model.load_model(model_path)

class ForecastRequest(BaseModel):
    store: int
    item: int
    date: str
    sales_lag_1: float
    sales_lag_7: float
    sales_roll_mean_7: float

@app.post("/forecast")
def get_forecast(req: ForecastRequest):
    try:
        # Parse date to extract date-part features
        dt = pd.to_datetime(req.date)
        day_of_week = dt.dayofweek
        month = dt.month
        year = dt.year
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Order of features must match the training set:
        # ['store', 'item', 'day_of_week', 'month', 'year', 'is_weekend', 'sales_lag_1', 'sales_lag_7', 'sales_roll_mean_7']
        features = pd.DataFrame([{
            'store': req.store,
            'item': req.item,
            'day_of_week': day_of_week,
            'month': month,
            'year': year,
            'is_weekend': is_weekend,
            'sales_lag_1': req.sales_lag_1,
            'sales_lag_7': req.sales_lag_7,
            'sales_roll_mean_7': req.sales_roll_mean_7
        }])
        
        # Predict
        prediction = model.predict(features)[0]
        
        return {
            "store": req.store,
            "item": req.item,
            "date": req.date,
            "forecasted_sales": round(float(prediction), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/inventory/{store}/{item}")
def get_inventory(store: int, item: int):
    try:
        inv = inventory_service.get_inventory(store, item)
        if not inv:
            raise HTTPException(status_code=404, detail="Inventory not found")
        return inv
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/reorder-alerts")
def get_reorder_alerts():
    try:
        alerts = inventory_service.get_all_reorder_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return RedirectResponse(url="/docs")
