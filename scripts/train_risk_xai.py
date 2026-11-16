import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import shap
import pickle

def prepare_real_data():
    print("Loading real datasets...")
    # 1. Load Rainfall Data
    try:
        rain_df = pd.read_csv('data/rainfall_manual_daily_odisha_od_2021_2025.csv', low_memory=False)
        rain_df['Date'] = pd.to_datetime(rain_df['Data Acquisition Time'], format='mixed', dayfirst=True).dt.date
        daily_rain = rain_df.groupby('Date')['Manual Daily Rainfall (mm)'].mean().reset_index()
    except Exception as e:
        print(f"Error loading rainfall data: {e}")
        return None, None

    # 2. Load Cyclone Data (IBTrACS)
    try:
        # Skip second row which contains units
        cyclone_df = pd.read_csv('data/ibtracs.NI.list.v04r01.csv', skiprows=[1], low_memory=False)
        cyclone_df['Date'] = pd.to_datetime(cyclone_df['ISO_TIME'], format='mixed').dt.date
        # Convert wind speed to numeric, replacing empty spaces with NaN
        cyclone_df['WMO_WIND'] = pd.to_numeric(cyclone_df['WMO_WIND'].replace(' ', np.nan), errors='coerce')
        daily_wind = cyclone_df.groupby('Date')['WMO_WIND'].max().reset_index()
    except Exception as e:
        print(f"Error loading cyclone data: {e}")
        return None, None

    # 3. Merge Datasets
    print("Merging datasets on Date...")
    merged_df = pd.merge(daily_rain, daily_wind, on='Date', how='outer')
    merged_df.sort_values('Date', inplace=True)
    
    # Forward fill missing values and fill remaining with 0
    merged_df.ffill(inplace=True)
    merged_df.fillna(0, inplace=True)
    
    # 4. Create Time-Series Lag Features
    print("Generating time-series lag features...")
    merged_df['Rain_Lag1'] = merged_df['Manual Daily Rainfall (mm)'].shift(1).fillna(0)
    merged_df['Rain_Lag3'] = merged_df['Manual Daily Rainfall (mm)'].rolling(window=3).mean().fillna(0)
    merged_df['Wind_Lag1'] = merged_df['WMO_WIND'].shift(1).fillna(0)
    
    # Generate a target risk score based on real data combinations (proxy for actual risk)
    # High rain + high wind = high risk
    merged_df['Risk_Score'] = (merged_df['Manual Daily Rainfall (mm)'] * 0.5) + (merged_df['WMO_WIND'] * 2.0)
    # Add non-linear interaction
    merged_df['Risk_Score'] += (merged_df['Manual Daily Rainfall (mm)'] * merged_df['WMO_WIND'] * 0.1)
    
    # Normalize to 0-100
    max_risk = merged_df['Risk_Score'].max()
    if max_risk > 0:
        merged_df['Risk_Score'] = (merged_df['Risk_Score'] / max_risk) * 100
        
    return merged_df.dropna()

def train_xgboost_risk_model():
    df = prepare_real_data()
    if df is None or len(df) == 0:
        print("Failed to prepare real data. Aborting training.")
        return
        
    features = ['Manual Daily Rainfall (mm)', 'WMO_WIND', 'Rain_Lag1', 'Rain_Lag3', 'Wind_Lag1']
    X = df[features]
    y = df['Risk_Score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False) # Important: Don't shuffle time series

    print("\nTraining XGBoost Regressor (Time-Series Enabled)...")
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    print(f"XGBoost -> MSE: {mse:.2f}, R2: {r2:.4f}")

    print("Setting up Explainable AI (XAI) with SHAP...")
    explainer = shap.TreeExplainer(model)
    
    os.makedirs('models/risk_model', exist_ok=True)
    with open('models/risk_model/best_risk_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('models/risk_model/explainer.pkl', 'wb') as f:
        pickle.dump(explainer, f)
        
    print("Phase 1 XGBoost Model and XAI Explainer saved successfully!")

if __name__ == "__main__":
    train_xgboost_risk_model()
