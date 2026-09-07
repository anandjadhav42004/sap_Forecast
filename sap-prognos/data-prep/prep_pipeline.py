import pandas as pd
import numpy as np
import os

def prep_data(raw_filepath, out_dir):
    print("Starting data prep pipeline on REAL data...")
    print(f"Loading data from {raw_filepath}")
    df = pd.read_csv(raw_filepath)
    df['date'] = pd.to_datetime(df['date'])
    
    print("Initial Data Range:")
    print(f"Min Date: {df['date'].min().date()}, Max Date: {df['date'].max().date()}")
    
    # Sort data
    df = df.sort_values(by=['store', 'item', 'date'])

    print("Handling missing values...")
    # Group by store and item to interpolate missing values
    df['sales'] = df.groupby(['store', 'item'])['sales'].transform(lambda x: x.interpolate(method='linear').ffill().bfill())
    
    print("Capping outliers...")
    def cap_outliers(series):
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series.clip(lower=lower_bound, upper=upper_bound)
        
    df['sales'] = df.groupby(['store', 'item'])['sales'].transform(cap_outliers)
    
    print("Engineering features (lags, rolling averages, date parts)...")
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    df['sales_lag_1'] = df.groupby(['store', 'item'])['sales'].shift(1)
    df['sales_lag_7'] = df.groupby(['store', 'item'])['sales'].shift(7)
    df['sales_roll_mean_7'] = df.groupby(['store', 'item'])['sales'].transform(lambda x: x.shift(1).rolling(window=7).mean())
    
    # Drop rows with NaN from lags
    df = df.dropna().reset_index(drop=True)
    
    print("Performing time-based split...")
    # Real dataset is 2013-01-01 to 2017-12-31 (5 years)
    train_end = pd.to_datetime('2016-12-31')
    val_end = pd.to_datetime('2017-06-30')
    
    train = df[df['date'] <= train_end]
    val = df[(df['date'] > train_end) & (df['date'] <= val_end)]
    test = df[df['date'] > val_end]
    
    print(f"Train set size: {len(train)}")
    print(f"Validation set size: {len(val)}")
    print(f"Test set size: {len(test)}")
    
    # Save splits with "split_" prefix to avoid overwriting the raw kaggle file
    train.to_csv(os.path.join(out_dir, 'split_train.csv'), index=False)
    val.to_csv(os.path.join(out_dir, 'split_val.csv'), index=False)
    test.to_csv(os.path.join(out_dir, 'split_test.csv'), index=False)
    
    print(f"Data prep complete. Files saved to {out_dir}")
    
    print("\n--- Dataset Summary ---")
    print(f"Total Rows: {len(df)}")
    print(f"Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Stores: {df['store'].nunique()}, Items: {df['item'].nunique()}")

if __name__ == "__main__":
    out_dir = "/Users/anand/Desktop/final project /sap-prognos/data-prep"
    raw_file = os.path.join(out_dir, "train.csv") # The Kaggle file
    prep_data(raw_file, out_dir)
