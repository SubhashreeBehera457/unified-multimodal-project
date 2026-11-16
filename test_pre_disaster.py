import pandas as pd
import joblib
import numpy as np

def load_model():
    # load risk model same as app
    model_path = 'models/risk_model/best_risk_model.pkl'
    explainer_path = 'models/risk_model/explainer.pkl'
    try:
        risk_model = joblib.load(model_path)
    except Exception as e:
        risk_model = None
        print('Failed to load model:', e)
    try:
        explainer = joblib.load(explainer_path)
    except Exception as e:
        explainer = None
        print('Failed to load explainer:', e)
    return risk_model, explainer

def run_case(rainfall, river_level, wind_speed):
    risk_model, explainer = load_model()
    if risk_model is None:
        print('Model not loaded')
        return
    # feature generation (same as app)
    input_data = pd.DataFrame({
        'Manual Daily Rainfall (mm)': [rainfall],
        'WMO_WIND': [wind_speed],
        'Rain_Lag1': [rainfall * 0.8],
        'Rain_Lag3': [rainfall * 0.7],
        'Wind_Lag1': [wind_speed * 0.9]
    })
    raw_score = risk_model.predict(input_data)[0]
    risk_score = int(round(raw_score))
    risk_score = max(0, min(100, risk_score))
    print('\n--- Test case ---')
    print(f'Rainfall: {rainfall} mm, River Level: {river_level} m, Wind: {wind_speed} km/h')
    print('Feature DataFrame:', input_data.to_dict(orient='list'))
    print('Raw model prediction:', raw_score)
    print('Clipped risk %:', risk_score)
    # SHAP values (optional)
    if explainer:
        shap_vals = explainer.shap_values(input_data)
        # flatten if needed
        if hasattr(shap_vals, 'shape') and shap_vals.shape[0] > 0:
            shap_vals = shap_vals[0]
        print('SHAP values:', shap_vals)

if __name__ == '__main__':
    # Minimum values
    run_case(rainfall=0, river_level=0, wind_speed=0)
    # Medium values
    run_case(rainfall=50, river_level=5, wind_speed=80)
    # Maximum values (reasonable ranges)
    run_case(rainfall=500, river_level=10, wind_speed=250)
