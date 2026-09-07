import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
from prophet import Prophet
import xgboost as xgb
import os
import json

def mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_idx = y_true != 0
    return np.mean(np.abs((y_true[non_zero_idx] - y_pred[non_zero_idx]) / y_true[non_zero_idx])) * 100

def evaluate_predictions(y_true, y_pred, model_name):
    metrics = {
        'RMSE': float(np.sqrt(mean_squared_error(y_true, y_pred))),
        'MAE': float(mean_absolute_error(y_true, y_pred)),
        'MAPE': float(mape(y_true, y_pred))
    }
    print(f"--- {model_name} ---")
    print(f"RMSE: {metrics['RMSE']:.2f}")
    print(f"MAE: {metrics['MAE']:.2f}")
    print(f"MAPE: {metrics['MAPE']:.2f}%\n")
    return metrics

def run_model_comparison(data_dir, out_dir):
    print("Loading data...")
    train = pd.read_csv(os.path.join(data_dir, 'split_train.csv'))
    val = pd.read_csv(os.path.join(data_dir, 'split_val.csv'))
    test = pd.read_csv(os.path.join(data_dir, 'split_test.csv'))
    
    train_full = pd.concat([train, val])
    
    results = {}

    print("Evaluating Baseline (7-Day Moving Average)...")
    baseline_preds = test['sales_roll_mean_7'].fillna(test['sales'].mean())
    results['Baseline (7-Day MA)'] = evaluate_predictions(test['sales'], baseline_preds, 'Baseline (7-Day MA)')

    print("Training XGBoost Global Model (Full Dataset ~820k rows)...")
    features = ['store', 'item', 'day_of_week', 'month', 'year', 'is_weekend', 'sales_lag_1', 'sales_lag_7', 'sales_roll_mean_7']
    target = 'sales'
    
    X_train, y_train = train_full[features], train_full[target]
    X_test, y_test = test[features], test[target]
    
    # Use tree_method='hist' for much faster training on large datasets
    xgb_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, tree_method='hist', random_state=42)
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    
    results['XGBoost (Full Global)'] = evaluate_predictions(y_test, xgb_preds, 'XGBoost (Full Global)')

    print("Training Prophet Models (Subset of 5 Store-Item pairs due to scale)...")
    # Training 500 Prophet models takes too long for the prototype script.
    # We'll evaluate Prophet on a small subset to get a representative MAPE.
    prophet_preds = []
    prophet_actuals = []
    xgb_subset_preds = []
    
    groups = test.groupby(['store', 'item'])
    count = 0
    for (store, item), test_group in groups:
        if count >= 5:
            break
        
        train_group = train_full[(train_full['store'] == store) & (train_full['item'] == item)]
        
        df_prophet = train_group[['date', 'sales']].rename(columns={'date': 'ds', 'sales': 'y'})
        
        m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        m.fit(df_prophet)
        
        future = test_group[['date']].rename(columns={'date': 'ds'})
        forecast = m.predict(future)
        
        prophet_preds.extend(forecast['yhat'].values)
        prophet_actuals.extend(test_group['sales'].values)
        
        # Also collect XGBoost predictions for this subset
        xgb_subset_preds.extend(xgb_model.predict(test_group[features]))
        count += 1

    results['Prophet (Sampled)'] = evaluate_predictions(prophet_actuals, prophet_preds, 'Prophet (Sampled)')
    results['XGBoost (Sampled 5 Series)'] = evaluate_predictions(prophet_actuals, xgb_subset_preds, 'XGBoost (Sampled 5 Series)')
    
    print("Saving XGBoost model...")
    xgb_model.save_model(os.path.join(out_dir, 'xgboost_model.json'))
    
    with open(os.path.join(out_dir, 'model_comparison.json'), 'w') as f:
        json.dump({'metrics': results}, f, indent=4)
        
    print("Model comparison complete!")

if __name__ == "__main__":
    base_dir = "/Users/anand/Desktop/final project /sap-prognos"
    data_dir = os.path.join(base_dir, "data-prep")
    out_dir = os.path.join(base_dir, "models")
    run_model_comparison(data_dir, out_dir)
