from fastapi import FastAPI, HTTPException, Request, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import xgboost as xgb
import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import inventory_service
import inventory_db

# Ensure self-healing database initialization
try:
    inventory_db.ensure_db_initialized()
    logger.info("Database verified and initialized.")
except Exception as e:
    logger.error(f"Database initialization warning: {e}")

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
_DEFAULT_MODEL_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "xgboost_model.json"))
env_model_path = os.getenv("MODEL_PATH")
if env_model_path and os.path.isabs(env_model_path):
    MODEL_PATH = env_model_path
elif env_model_path:
    MODEL_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), env_model_path))
else:
    MODEL_PATH = _DEFAULT_MODEL_PATH
CONFIDENCE_LEVEL = float(os.getenv("CONFIDENCE_LEVEL", "0.85"))

# Load model on startup
logger.info(f"Loading XGBoost model from {MODEL_PATH}")
model = xgb.Booster()
try:
    model.load_model(MODEL_PATH)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")


# ==============================================================================
# Security & RBAC (Role-Based Access Control)
# Demonstration-level token authentication
# ==============================================================================
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/auth/login")
def login(req: LoginRequest):
    """Demo authentication endpoint providing role-based Bearer tokens."""
    if req.username == "admin" and req.password == "admin":
        return {
            "token": "demo-admin-bearer-token",
            "role": "admin",
            "fullName": "Anand Jadhav",
            "email": "anand.jadhav@sap-prognos.internal",
            "roleName": "Administrator",
            "avatarText": "AJ"
        }
    elif req.username == "user" and req.password == "user":
        return {
            "token": "demo-user-bearer-token",
            "role": "user",
            "fullName": "Demo User",
            "email": "demo.viewer@sap-prognos.internal",
            "roleName": "Viewer (Read-Only)",
            "avatarText": "DU"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Use admin/admin or user/user for demo access."
        )

def get_current_user_role(
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
) -> str:
    """Extracts role from X-User-Role header or Authorization Bearer token."""
    if x_user_role:
        return x_user_role.lower().strip()
    if authorization:
        auth_lower = authorization.lower()
        if "admin" in auth_lower:
            return "admin"
        if "user" in auth_lower:
            return "user"
    return "viewer"

def require_admin(role: str = Depends(get_current_user_role)):
    """Enforces administrator authorization on sensitive operational endpoints."""
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required for this operational action."
        )
    return role


# ==============================================================================
# Forecasting & Explainable AI
# ==============================================================================
class ForecastRequest(BaseModel):
    store: int = Field(..., gt=0, le=10, description="Store ID (1 to 10)")
    item: int = Field(..., gt=0, le=50, description="Item ID (1 to 50)")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Forecast Start Date (YYYY-MM-DD)")
    sales_lag_1: float = Field(..., ge=0, description="Previous day's sales (t-1)")
    sales_lag_7: float = Field(..., ge=0, description="Sales from 7 days ago (t-7)")
    sales_roll_mean_7: float = Field(..., ge=0, description="7-day rolling average (t-7 to t-1)")
    horizon_days: int = Field(1, ge=1, le=30, description="Forecast horizon in days (1 to 30)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "store": 2,
                "item": 10,
                "date": "2018-01-01",
                "sales_lag_1": 41.0,
                "sales_lag_7": 45.0,
                "sales_roll_mean_7": 41.7,
                "horizon_days": 7
            }
        }
    }

def _predict_single_step(store: int, item: int, dt: datetime, lag_1: float, lag_7: float, roll_mean_7: float) -> float:
    """Predicts a single step using the trained XGBoost booster."""
    day_of_week = dt.weekday()
    month = dt.month
    year = dt.year
    is_weekend = 1 if day_of_week >= 5 else 0
    
    features = pd.DataFrame([{
        'store': store,
        'item': item,
        'day_of_week': day_of_week,
        'month': month,
        'year': year,
        'is_weekend': is_weekend,
        'sales_lag_1': lag_1,
        'sales_lag_7': lag_7,
        'sales_roll_mean_7': roll_mean_7
    }])
    
    try:
        dmatrix = xgb.DMatrix(features)
        pred = float(model.predict(dmatrix)[0])
        return max(0.0, pred)
    except Exception as e:
        logger.error(f"XGBoost predict failed: {e}. Using rolling mean fallback.")
        return float(roll_mean_7) * 1.05

@app.post("/forecast")
def get_forecast(req: ForecastRequest):
    try:
        start_dt = pd.to_datetime(req.date)
        
        # Step 1: Base Single-Day Prediction
        pred_day1 = _predict_single_step(
            req.store, req.item, start_dt,
            req.sales_lag_1, req.sales_lag_7, req.sales_roll_mean_7
        )
        
        # Uncertainty bounds based on empirical global MAPE (~12.93%)
        error_margin = pred_day1 * 0.1293
        lower_bound = round(max(0.0, pred_day1 - error_margin), 2)
        upper_bound = round(pred_day1 + error_margin, 2)
        
        # Step 2: Recursive Multi-Day Forecasting (if horizon_days > 1)
        horizon_forecast = []
        total_demand = 0.0
        
        cur_lag_1 = req.sales_lag_1
        cur_lag_7 = req.sales_lag_7
        cur_roll_mean = req.sales_roll_mean_7
        rolling_buffer = [req.sales_roll_mean_7] * 6 + [req.sales_lag_1]
        
        for h in range(req.horizon_days):
            step_dt = start_dt + timedelta(days=h)
            step_date_str = step_dt.strftime('%Y-%m-%d')
            
            step_pred = _predict_single_step(
                req.store, req.item, step_dt,
                cur_lag_1, cur_lag_7, cur_roll_mean
            )
            step_margin = step_pred * 0.1293
            step_lower = round(max(0.0, step_pred - step_margin), 2)
            step_upper = round(step_pred + step_margin, 2)
            
            horizon_forecast.append({
                "day_index": h + 1,
                "date": step_date_str,
                "predicted_demand": round(step_pred, 2),
                "lower_bound": step_lower,
                "upper_bound": step_upper
            })
            total_demand += step_pred
            
            # Recursive update of autoregressive lag features for step h+1
            cur_lag_1 = step_pred
            rolling_buffer = rolling_buffer[1:] + [step_pred]
            cur_roll_mean = sum(rolling_buffer) / len(rolling_buffer)
            if h >= 6:
                cur_lag_7 = horizon_forecast[h - 6]["predicted_demand"]

        # Step 3: Explainable AI (XAI) Feature Importance
        drivers = []
        try:
            importance = model.get_score(importance_type='gain')
            total_gain = sum(importance.values()) if importance else 1.0
            
            trend_impact = round((importance.get("sales_roll_mean_7", 0) / total_gain) * 100, 1)
            trend_dir = "up" if req.sales_roll_mean_7 > req.sales_lag_7 else "down"
            drivers.append({
                "factor": "Underlying 7-day rolling trend is " + ("increasing" if trend_dir == "up" else "decreasing"),
                "impact_percentage": trend_impact,
                "direction": trend_dir
            })
            
            day_of_week = start_dt.dayofweek
            is_weekend = 1 if day_of_week >= 5 else 0
            season_impact = round((importance.get("day_of_week", 0) / total_gain) * 100, 1)
            drivers.append({
                "factor": "Weekend seasonality factor" if is_weekend else "Weekday baseline cyclicality",
                "impact_percentage": season_impact,
                "direction": "up" if is_weekend else "down"
            })
            
            momentum_impact = round((importance.get("sales_lag_1", 0) / total_gain) * 100, 1)
            momentum_dir = "up" if req.sales_lag_1 > req.sales_roll_mean_7 else "down"
            drivers.append({
                "factor": "Recent daily momentum (t-1 sales velocity)",
                "impact_percentage": momentum_impact,
                "direction": momentum_dir
            })
        except Exception as e:
            logger.error(f"XAI extraction error: {e}")
            drivers = []
            
        return {
            "store": req.store,
            "item": req.item,
            "forecast_date": req.date,
            "horizon_days": req.horizon_days,
            "predicted_demand": round(pred_day1, 2),
            "forecasted_sales": round(pred_day1, 2),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_level": CONFIDENCE_LEVEL,
            "total_horizon_demand": round(total_demand, 2),
            "avg_daily_demand": round(total_demand / req.horizon_days, 2),
            "horizon_forecast": horizon_forecast,
            "model": "XGBoost",
            "model_version": "1.0.0",
            "explainability": drivers,
            "explainability_disclaimer": "Feature importance represents model split-gain contribution, not direct causal attribution."
        }
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# What-If Demand Scenario Simulator
# ==============================================================================
class SimulationRequest(BaseModel):
    store: int = Field(..., gt=0, le=10)
    item: int = Field(..., gt=0, le=50)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    sales_lag_1: float = Field(..., ge=0)
    sales_lag_7: float = Field(..., ge=0)
    sales_roll_mean_7: float = Field(..., ge=0)
    demand_adjustment_pct: float = Field(0.0, description="Percentage adjustment to base demand (e.g. 20 for +20%)")
    is_promotion: bool = Field(False, description="Apply promotional multiplier (+15%)")
    high_seasonality: bool = Field(False, description="Apply seasonal spike multiplier (+10%)")

@app.post("/simulate")
def simulate_forecast(req: SimulationRequest):
    logger.info(f"Simulation requested for Store {req.store}, Item {req.item}")
    try:
        dt = pd.to_datetime(req.date)
        base_prediction = _predict_single_step(
            req.store, req.item, dt,
            req.sales_lag_1, req.sales_lag_7, req.sales_roll_mean_7
        )
        
        promo_mult = 1.15 if req.is_promotion else 1.0
        season_mult = 1.10 if req.high_seasonality else 1.0
        simulated_prediction = base_prediction * (1 + req.demand_adjustment_pct / 100.0) * promo_mult * season_mult
        
        inv = inventory_service.get_inventory(req.store, req.item)
        if not inv:
            raise HTTPException(status_code=404, detail="Store or Item inventory not found")
            
        current_stock = inv['current_stock']
        incoming = inv['incoming_stock']
        target_stock = inv['target_stock']
        lead_time = inv['lead_time_days']
        available_stock = current_stock + incoming
        
        # Base case
        base_demand_lt = base_prediction * lead_time
        base_shortage = max(0, int(base_demand_lt - available_stock))
        base_order = max(0, int(target_stock - available_stock))
        base_risk = "CRITICAL" if available_stock <= base_demand_lt else ("HIGH" if available_stock <= inv['reorder_point'] else "LOW")
        
        # Simulated case
        sim_demand_lt = simulated_prediction * lead_time
        sim_shortage = max(0, int(sim_demand_lt - available_stock))
        sim_order = max(0, int((target_stock + sim_shortage) - available_stock)) if sim_shortage > 0 else max(0, int(target_stock - available_stock))
        sim_risk = "CRITICAL" if available_stock <= sim_demand_lt else ("HIGH" if available_stock <= inv['reorder_point'] else "LOW")
        
        inventory_impact = -sim_shortage if sim_shortage > 0 else int(available_stock - sim_demand_lt)
        
        # Scenario narrative explanation
        pct_change = round(((simulated_prediction - base_prediction) / base_prediction) * 100, 1) if base_prediction > 0 else 0
        scenario_explanation = (
            f"Simulated parameters result in a {pct_change:+.1f}% shift in daily demand "
            f"({round(base_prediction, 1)} → {round(simulated_prediction, 1)} units). "
            f"Across the {lead_time}-day lead time, expected demand is {round(sim_demand_lt, 1)} units. "
            f"Available stock is {available_stock} units, resulting in a recommended replenishment order of {sim_order} units."
        )
        
        return {
            "store": req.store,
            "item": req.item,
            "date": req.date,
            "base_case": {
                "daily_demand": round(base_prediction, 2),
                "lead_time_demand": round(base_demand_lt, 2),
                "expected_shortage": base_shortage,
                "recommended_order": base_order,
                "risk": base_risk
            },
            "simulated_case": {
                "daily_demand": round(simulated_prediction, 2),
                "lead_time_demand": round(sim_demand_lt, 2),
                "expected_shortage": sim_shortage,
                "recommended_order": sim_order,
                "risk": sim_risk,
                "applied_adjustments": {
                    "demand_adjustment_pct": req.demand_adjustment_pct,
                    "promotion_multiplier": promo_mult,
                    "seasonality_multiplier": season_mult
                }
            },
            # Flat compatibility keys
            "base_forecast": round(base_prediction, 2),
            "current_forecast": round(base_prediction, 2),
            "adjusted_forecast": round(simulated_prediction, 2),
            "simulated_forecast": round(simulated_prediction, 2),
            "current_stock": current_stock,
            "available_stock": available_stock,
            "shortage": sim_shortage,
            "inventory_impact_units": inventory_impact,
            "recommended_order": sim_order,
            "risk": sim_risk,
            "scenario_explanation": scenario_explanation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Statistical Anomaly Detection
# ==============================================================================
class SalesData(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    sales: float = Field(..., ge=0)

class AnomalyRequest(BaseModel):
    store: int = Field(..., gt=0, le=10)
    item: int = Field(..., gt=0, le=50)
    historical_sales: List[SalesData] = Field(..., min_length=5, description="At least 5 data points required for statistical anomaly detection")

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
                z = float(row['z_score'])
                actual = float(row['sales'])
                dev_pct = ((actual - mean) / mean) * 100 if mean > 0 else 0
                is_spike = bool(actual > mean)
                
                # Classify severity
                severity = "Critical" if abs(z) > 3.0 else "Warning"
                anomaly_type = "Demand Spike" if is_spike else "Demand Drop"
                
                # Supply chain operational impact
                impact = (
                    "Risk of over-ordering if spike is treated as structural trend" 
                    if is_spike else 
                    "Potential stockout or unreported supply disruption causing lost sales"
                )
                
                anomalies.append({
                    "date": row['date'],
                    "actual_sales": actual,
                    "expected": round(float(mean), 2),
                    "z_score": round(z, 2),
                    "deviation_pct": round(float(dev_pct), 1),
                    "is_spike": is_spike,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "planning_impact": impact
                })
                
        return {
            "store": req.store,
            "item": req.item,
            "sample_size": len(df),
            "mean_demand": round(float(mean), 2),
            "std_demand": round(float(std), 2),
            "anomalies_detected": len(anomalies),
            "methodology": "Two-tailed Z-score outlier detection (|Z| > 2.0)",
            "explanation": "Flagging demand outliers prevents atypical promotions or stockout dips from distorting autoregressive lag features.",
            "anomalies": anomalies
        }
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Inventory & Purchase Orders (Role-Guarded)
# ==============================================================================
@app.get("/inventory")
def get_all_inventory():
    """Returns the full master catalog (500 store-item SKUs) with supply chain indicators."""
    try:
        items = inventory_service.get_full_inventory()
        return {
            "count": len(items),
            "inventory": items
        }
    except Exception as e:
        logger.error(f"Error fetching all inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory/{store}/{item}")
def get_inventory(store: int, item: int):
    try:
        inv = inventory_service.get_inventory(store, item)
        if not inv:
            raise HTTPException(status_code=404, detail="Inventory record not found")
        return inv
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/reorder-alerts")
def get_reorder_alerts():
    try:
        alerts = inventory_service.get_all_reorder_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/history/{store}/{item}")
def get_sales_history(store: int, item: int, limit: int = 14):
    try:
        history = inventory_service.get_sales_history(store, item, limit)
        return {
            "store": store,
            "item": item,
            "count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error fetching sales history: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/features/{store}/{item}")
def get_features(store: int, item: int):
    try:
        features = inventory_service.get_latest_features(store, item)
        return features
    except Exception as e:
        logger.error(f"Error fetching latest features: {e}")
        raise HTTPException(status_code=400, detail=str(e))

class PurchaseOrderRequest(BaseModel):
    store: int = Field(..., gt=0, le=10, description="Store ID")
    item: int = Field(..., gt=0, le=50, description="Item ID")
    quantity: Optional[int] = Field(None, ge=1, description="Order quantity (optional, auto-calculated if omitted)")

@app.post("/purchase-order")
def create_purchase_order(req: PurchaseOrderRequest, admin_role: str = Depends(require_admin)):
    """Role-guarded endpoint: Only administrators can trigger real purchase orders."""
    logger.info(f"Purchase order requested by admin for Store {req.store}, Item {req.item}")
    try:
        order = inventory_service.create_purchase_order(req.store, req.item, req.quantity)
        if not order:
            raise HTTPException(status_code=404, detail="Store or Item not found in inventory")
        return {
            "message": "Purchase order successfully placed",
            "order": order
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create purchase order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/bulk-purchase-orders")
def create_bulk_purchase_orders(admin_role: str = Depends(require_admin)):
    """Admin-only endpoint: Automatically triggers purchase orders for all SKUs below safety stock."""
    logger.info("Bulk replenishment purchase orders triggered by administrator.")
    try:
        alerts = inventory_service.get_all_reorder_alerts()
        placed_orders = []
        for alert in alerts:
            order_qty = alert.get("recommended_order") or 50
            order = inventory_service.create_purchase_order(alert["store"], alert["item"], order_qty)
            if order:
                placed_orders.append(order)
        return {
            "message": f"Successfully generated {len(placed_orders)} purchase orders for all critical SKUs.",
            "count": len(placed_orders),
            "orders": placed_orders
        }
    except Exception as e:
        logger.error(f"Failed to generate bulk purchase orders: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders")
def get_orders(store: Optional[int] = None, item: Optional[int] = None):
    try:
        orders = inventory_service.get_orders(store, item)
        return {
            "count": len(orders),
            "orders": orders
        }
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# Health & Telemetry
# ==============================================================================
@app.get("/health")
def health_check():
    db_connected = False
    try:
        conn = inventory_service.get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_connected = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

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
        "version": "1.0.0",
        "environment": "development/prototype",
        "timestamp": datetime.now().isoformat()
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
    metrics_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'model_comparison.json'))
    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Metrics unavailable")
