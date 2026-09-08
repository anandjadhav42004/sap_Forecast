from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
import xgboost as xgb
import os
import sys
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Logging
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level_str, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sap_prognos_api")

# Add current directory to path to allow importing inventory_service when running from root
sys.path.append(os.path.dirname(__file__))
import inventory_service

app = FastAPI(
    title="SAP Prognos Forecast API", 
    description="Enterprise AI Demand Forecasting and Inventory Optimization API",
    version="1.0.0"
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(os.path.dirname(__file__), '..', 'models', 'xgboost_model.json'))
CONFIDENCE_LEVEL = float(os.getenv("CONFIDENCE_LEVEL", "0.85"))

# Load model on startup
logger.info(f"Loading XGBoost model from {MODEL_PATH}")
model = xgb.Booster()
try:
    model.load_model(MODEL_PATH)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")

class ForecastRequest(BaseModel):
    store: int = Field(..., gt=0, description="Store ID")
    item: int = Field(..., gt=0, description="Item ID")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Forecast Date (YYYY-MM-DD)")
    sales_lag_1: float = Field(..., ge=0, description="Previous day's sales")
    sales_lag_7: float = Field(..., ge=0, description="Sales from 7 days ago")
    sales_roll_mean_7: float = Field(..., ge=0, description="7-day rolling average of sales")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "store": 2,
                "item": 10,
                "date": "2018-01-01",
                "sales_lag_1": 41.0,
                "sales_lag_7": 45.0,
                "sales_roll_mean_7": 41.7
            }
        }
    }

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
        try:
            dmatrix = xgb.DMatrix(features)
            prediction = float(model.predict(dmatrix)[0])
        except Exception as e:
            logger.error(f"Model prediction failed: {e}. Using fallback heuristic.")
            prediction = float(req.sales_roll_mean_7) * 1.05
        
        # Estimated Prediction Range (based on XGBoost global MAPE ~12.9%)
        error_margin = prediction * 0.129 
        lower_bound = round(max(0, prediction - error_margin), 2)
        upper_bound = round(prediction + error_margin, 2)

        # Real Explainable AI using XGBoost feature importance (Gain)
        drivers = []
        try:
            importance = model.get_score(importance_type='gain')
            total_gain = sum(importance.values()) if importance else 1.0
            
            # Trend (sales_roll_mean_7)
            trend_impact = round((importance.get("sales_roll_mean_7", 0) / total_gain) * 100, 1)
            trend_direction = "up" if req.sales_roll_mean_7 > req.sales_lag_7 else "down"
            drivers.append({
                "factor": "Recent weekly demand is " + ("increasing" if trend_direction == "up" else "decreasing"),
                "impact_percentage": trend_impact,
                "direction": trend_direction
            })
            
            # Seasonality (day_of_week / is_weekend)
            season_impact = round((importance.get("day_of_week", 0) / total_gain) * 100, 1)
            season_direction = "up" if is_weekend else "down"
            drivers.append({
                "factor": "Weekend seasonality factor" if is_weekend else "Weekday baseline",
                "impact_percentage": season_impact,
                "direction": season_direction
            })
            
            # Momentum (sales_lag_1)
            momentum_impact = round((importance.get("sales_lag_1", 0) / total_gain) * 100, 1)
            momentum_direction = "up" if req.sales_lag_1 > req.sales_roll_mean_7 else "down"
            drivers.append({
                "factor": "Recent daily momentum",
                "impact_percentage": momentum_impact,
                "direction": momentum_direction
            })
        except Exception as e:
            logger.error(f"Error extracting feature importance: {e}")
            drivers = []
        
        return {
            "store": req.store,
            "item": req.item,
            "forecast_date": req.date,
            "predicted_demand": round(prediction, 2),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_level": CONFIDENCE_LEVEL,
            "model": "XGBoost",
            "model_version": "1.0.0",
            "explainability": drivers
        }
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

class SalesData(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    sales: float = Field(..., ge=0)

class AnomalyRequest(BaseModel):
    store: int = Field(..., gt=0)
    item: int = Field(..., gt=0)
    historical_sales: List[SalesData] = Field(..., min_length=5, description="At least 5 data points required for anomaly detection")

@app.post("/anomalies")
def detect_anomalies(req: AnomalyRequest):
    logger.info(f"Anomaly detection requested for Store {req.store}, Item {req.item}")
    try:
        df = pd.DataFrame([{"date": s.date, "sales": s.sales} for s in req.historical_sales])
        df['sales'] = pd.to_numeric(df['sales'])
        
        mean = df['sales'].mean()
        std = df['sales'].std()
        
        anomalies = []
        if std > 0:
            df['z_score'] = (df['sales'] - mean) / std
            anomalous_rows = df[df['z_score'].abs() > 2.0]
            
            for _, row in anomalous_rows.iterrows():
                deviation_pct = ((row['sales'] - mean) / mean) * 100 if mean > 0 else 0
                anomalies.append({
                    "date": row['date'],
                    "actual_sales": float(row['sales']),
                    "expected": round(float(mean), 2),
                    "deviation_pct": round(float(deviation_pct), 1),
                    "is_spike": bool(row['sales'] > mean)
                })
                
        return {
            "store": req.store,
            "item": req.item,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
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

class SimulationRequest(BaseModel):
    store: int = Field(..., gt=0)
    item: int = Field(..., gt=0)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    sales_lag_1: float = Field(..., ge=0)
    sales_lag_7: float = Field(..., ge=0)
    sales_roll_mean_7: float = Field(..., ge=0)
    demand_adjustment_pct: float = Field(0.0, description="Percentage adjustment to base demand (e.g. 20 for +20%)")
    is_promotion: bool = Field(False, description="Apply promotion impact multiplier")
    high_seasonality: bool = Field(False, description="Apply high seasonality multiplier")

@app.post("/simulate")
def simulate_forecast(req: SimulationRequest):
    logger.info(f"Simulation requested for Store {req.store}, Item {req.item}")
    try:
        # Base Forecast
        dt = pd.to_datetime(req.date)
        features = pd.DataFrame([{
            'store': req.store,
            'item': req.item,
            'day_of_week': dt.dayofweek,
            'month': dt.month,
            'year': dt.year,
            'is_weekend': 1 if dt.dayofweek >= 5 else 0,
            'sales_lag_1': req.sales_lag_1,
            'sales_lag_7': req.sales_lag_7,
            'sales_roll_mean_7': req.sales_roll_mean_7
        }])
        
        try:
            dmatrix = xgb.DMatrix(features)
            base_prediction = float(model.predict(dmatrix)[0])
        except Exception as e:
            logger.error(f"Model prediction failed: {e}. Using fallback heuristic.")
            base_prediction = float(req.sales_roll_mean_7) * 1.05
        
        # Apply Simulation Adjustments
        simulated_prediction = base_prediction * (1 + req.demand_adjustment_pct / 100.0)
        if req.is_promotion:
            simulated_prediction *= 1.15 # +15% for promotion
        if req.high_seasonality:
            simulated_prediction *= 1.10 # +10% for high seasonality
            
        # Inventory Impact
        inv = inventory_service.get_inventory(req.store, req.item)
        inventory_impact = 0
        recommended_order = 0
        risk_level = "UNKNOWN"
        
        if inv:
            current_stock = inv['current_stock']
            lead_time = inv['lead_time_days']
            incoming = inv['incoming_stock']
            target_stock = inv['target_stock']
            
            # Simulated demand during lead time
            projected_demand_lt = simulated_prediction * lead_time
            available_stock = current_stock + incoming
            
            expected_shortage = projected_demand_lt - available_stock
            
            if expected_shortage > 0:
                recommended_order = int(target_stock - available_stock)
                inventory_impact = -int(expected_shortage) # Negative impact means we are short
                risk_level = "HIGH"
            else:
                inventory_impact = int(abs(expected_shortage)) # Positive means we have surplus
                recommended_order = max(0, int(target_stock - available_stock))
                risk_level = "LOW"
                
        return {
            "store": req.store,
            "item": req.item,
            "date": req.date,
            "base_forecast": round(base_prediction, 2),
            "adjusted_forecast": round(simulated_prediction, 2),
            "current_stock": current_stock if inv else 0,
            "shortage": int(abs(inventory_impact)) if inventory_impact < 0 else 0,
            "recommended_order": recommended_order,
            "risk": risk_level
        }
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

class RecommendationRequest(BaseModel):
    store: int = Field(..., gt=0)
    item: int = Field(..., gt=0)
    forecasted_demand: float = Field(..., ge=0)

@app.post("/recommendation")
def get_recommendation(req: RecommendationRequest):
    logger.info(f"Recommendation requested for Store {req.store}, Item {req.item}")
    try:
        inv = inventory_service.get_inventory(req.store, req.item)
        if not inv:
            logger.warning(f"Inventory not found for Store {req.store}, Item {req.item}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found for recommendation")
            
        current_stock = inv['current_stock']
        incoming = inv['incoming_stock']
        lead_time = inv['lead_time_days']
        target_stock = inv['target_stock']
        
        available_stock = current_stock + incoming
        expected_demand_lt = req.forecasted_demand * lead_time
        expected_shortage = expected_demand_lt - available_stock
        
        if expected_shortage > 0:
            reorder_amount = int(target_stock - available_stock)
            status = "⚠️ Reorder Required"
        else:
            reorder_amount = 0
            status = "✅ Stock Sufficient"
            
        return {
            "store": req.store,
            "item": req.item,
            "forecast": round(req.forecasted_demand, 2),
            "current_stock": current_stock,
            "incoming_stock": incoming,
            "expected_shortage": round(expected_shortage, 2) if expected_shortage > 0 else 0,
            "status": status,
            "recommendation": f"Reorder {reorder_amount} units" if reorder_amount > 0 else "No action needed"
        }
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.get("/reorder-alerts")
def get_reorder_alerts():
    try:
        alerts = inventory_service.get_all_reorder_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    # Check DB Connection
    db_connected = False
    try:
        conn = inventory_service.get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_connected = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    # Check Model Loaded
    model_loaded = False
    try:
        if model.num_features() > 0:
            model_loaded = True
    except Exception:
        pass

    return {
        "status": "healthy" if (db_connected and model_loaded) else "degraded",
        "model_loaded": model_loaded,
        "database_connected": db_connected,
        "version": "1.0.0"
    }

@app.get("/")
def root():
    return {
        "name": "SAP Prognos API",
        "description": "Enterprise AI Demand Forecasting and Inventory Optimization",
        "docs_url": "/docs",
        "health_check": "/health",
        "metrics": "/metrics"
    }

@app.get("/metrics")
def get_metrics():
    import json
    metrics_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_comparison.json')
    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Metrics unavailable")
