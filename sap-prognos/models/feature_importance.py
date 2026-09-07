import xgboost as xgb
import json
import os

base_dir = "/Users/anand/Desktop/final project /sap-prognos"
model_path = os.path.join(base_dir, 'models', 'xgboost_model.json')

model = xgb.XGBRegressor()
model.load_model(model_path)
booster = model.get_booster()

# Feature importance based on 'gain' (contribution of the feature to the model)
importance = booster.get_score(importance_type='gain')
sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)

print("XGBoost Feature Importances (Gain):")
for feature, score in sorted_importance:
    print(f"{feature}: {score:.4f}")
