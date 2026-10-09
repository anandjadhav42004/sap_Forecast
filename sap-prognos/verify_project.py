import os
import sys

# Add forecast-api to path so inventory_service and inventory_db can be resolved
# by both the Python runtime and static analysis tools.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_API_DIR = os.path.join(_BASE_DIR, "forecast-api")
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

def verify_system():
    print("SAP PROGNOS SYSTEM CHECK")
    
    # 1. Project Structure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(base_dir, "forecast-api")
    models_dir = os.path.join(base_dir, "models")
    ui_dir = os.path.join(base_dir, "frontend-ui5", "webapp")
    
    dirs = [api_dir, models_dir, ui_dir]
    if all(os.path.exists(d) for d in dirs):
        print("[PASS] Project structure")
    else:
        print("[FAIL] Project structure")
        return
        
    # 2. Model File
    model_path = os.path.join(models_dir, "xgboost_model.json")
    if os.path.exists(model_path):
        print("[PASS] Model file")
    else:
        print("[FAIL] Model file")
        return
        
    # 3. Database
    db_path = os.path.join(api_dir, "inventory.db")
    if os.path.exists(db_path):
        print("[PASS] Database")
    else:
        print("[FAIL] Database")
        return
        
    # 4. Model Loading
    try:
        import xgboost as xgb
        model = xgb.XGBRegressor()
        model.load_model(model_path)
        print("[PASS] Model loading")
    except Exception as e:
        print(f"[FAIL] Model loading: {e}")
        return
        
    # 5. API Imports
    try:
        import main
        import inventory_service
        import inventory_db
        print("[PASS] API imports")
    except Exception as e:
        print(f"[FAIL] API imports: {e}")
        return
        
    # 6. Configuration
    env_path = os.path.join(api_dir, ".env")
    if os.path.exists(env_path):
        print("[PASS] Configuration")
    else:
        print("[FAIL] Configuration (.env missing)")
        
    print("SYSTEM READY")

if __name__ == "__main__":
    verify_system()
