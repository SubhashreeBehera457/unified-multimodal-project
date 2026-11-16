import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import shap
import pickle

def train_and_compare_risk_models():
    print("Generating Synthetic Phase 1 Dataset for Pre-Disaster Risk Prediction...")
    np.random.seed(42)
    data = {
        'rainfall_24h_mm': np.random.uniform(0, 500, 5000),
        'river_level_m': np.random.uniform(1.0, 10.0, 5000),
        'wind_speed_kmh': np.random.uniform(10, 200, 5000),
        'soil_moisture_index': np.random.uniform(0, 100, 5000)
    }
    df = pd.DataFrame(data)
    
    df['flood_risk'] = (df['rainfall_24h_mm'] * 0.1) + (df['river_level_m'] * 3) + (df['soil_moisture_index'] * 0.2)
    df['flood_risk'] += np.random.normal(0, 5, 5000)
    df['flood_risk'] = np.clip(df['flood_risk'], 0, 100)

    X = df[['rainfall_24h_mm', 'river_level_m', 'wind_speed_kmh', 'soil_moisture_index']]
    y = df['flood_risk']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=42),
        "Support Vector Regressor (SVR)": SVR(kernel='rbf'),
        "Random Forest (Proposed)": RandomForestRegressor(n_estimators=100, random_state=42)
    }

    results = []
    best_model = None
    best_r2 = -float('inf')

    print("\n--- MODEL COMPARISON EVALUATION ---")
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mse = mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        results.append({"Model": name, "MSE": round(mse, 2), "R2_Score": round(r2, 4)})
        print(f"{name} -> MSE: {mse:.2f}, R2: {r2:.4f}")
        
        if r2 > best_r2:
            best_r2 = r2
            best_model = model

    results_df = pd.DataFrame(results)
    results_df.to_csv("models/risk_model_comparison.csv", index=False)
    
    print("\nModel Comparison Results Saved to: models/risk_model_comparison.csv")
    print(f"\nBest Model selected for XAI: {results_df.loc[results_df['R2_Score'].idxmax()]['Model']}")

    print("Setting up Explainable AI (XAI) with SHAP for the best model...")
    # TreeExplainer is best for RF/Trees
    if isinstance(best_model, (RandomForestRegressor, DecisionTreeRegressor)):
        explainer = shap.TreeExplainer(best_model)
    else:
        # Fallback for linear models or SVR
        explainer = shap.KernelExplainer(best_model.predict, shap.sample(X_train, 100))
    
    os.makedirs('models/risk_model', exist_ok=True)
    with open('models/risk_model/best_risk_model.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    with open('models/risk_model/explainer.pkl', 'wb') as f:
        pickle.dump(explainer, f)
        
    print("Phase 1 Best Model and XAI Explainer saved successfully!")

if __name__ == "__main__":
    train_and_compare_risk_models()
