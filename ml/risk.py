"""
ml/risk.py
──────────
XGBoost risk model inference + SHAP explanation.

Model context (from train_risk_xai.py):
  - Trained on Odisha daily rainfall + IBTrACS cyclone data
  - Target: Risk_Score = normalized hazard index
  - Training normalization denominator includes extreme historical cyclone events (>200 kt wind)
  - Consequence: output range for slider-range inputs ≈ 0–39 (not 0–100)
  - This is the model's actual learned behavior, not a bug

Feature schema (exact features the model was trained on):
  Manual Daily Rainfall (mm)   ← direct slider input
  WMO_WIND                     ← direct slider input
  Rain_Lag1                    ← synthetic proxy: rainfall × 0.8
  Rain_Lag3                    ← synthetic proxy: rainfall × 0.7
  Wind_Lag1                    ← synthetic proxy: wind × 0.9

Risk classification thresholds (calibrated to real output range):
  < 10    → LOW
  10–20   → MODERATE
  20–30   → HIGH
  ≥ 30    → CRITICAL

SHAP notes:
  - Values are in risk-score-point units, NOT percentages
  - WMO_WIND dominates because lag features are linear proxies with near-zero marginal info
  - This is expected collinearity behavior from synthetic lag construction
"""
import pickle
import numpy as np
import pandas as pd
from typing import Optional


def build_feature_dataframe(rainfall_mm: float, wind_kmh: float) -> pd.DataFrame:
    """
    Build the exact feature DataFrame that XGBoost expects.

    Lag features are synthetic proxies computed from current-day values.
    Label: 'SIMULATION' — real lag features require time-series data from past days.

    Args:
        rainfall_mm : Manual Daily Rainfall (mm) — from slider or live weather
        wind_kmh    : Cyclone Sustained Wind (km/h) — from slider or live weather

    Returns:
        pd.DataFrame with columns matching the model's training schema
    """
    return pd.DataFrame({
        "Manual Daily Rainfall (mm)": [float(rainfall_mm)],
        "WMO_WIND": [float(wind_kmh)],
        "Rain_Lag1": [float(rainfall_mm) * 0.8],   # synthetic 1-day lag proxy
        "Rain_Lag3": [float(rainfall_mm) * 0.7],   # synthetic 3-day lag proxy
        "Wind_Lag1": [float(wind_kmh) * 0.9],      # synthetic 1-day wind lag proxy
    })


def run_risk_inference(
    rainfall_mm: float,
    wind_kmh: float,
    risk_model,
    explainer,
) -> dict:
    """
    Run the XGBoost risk model on current telemetry values.

    Args:
        rainfall_mm  : Daily rainfall in mm
        wind_kmh     : Cyclone wind speed in km/h
        risk_model   : Loaded XGBoost model (sklearn-compatible)
        explainer    : Loaded SHAP TreeExplainer

    Returns dict:
        input_data   : pd.DataFrame used for inference
        raw_score    : float — raw XGBoost output
        risk_score   : float — clipped to [0, 100]
        risk_level   : str — LOW | MODERATE | HIGH | CRITICAL
        risk_color   : str — hex color for the level
        shap_vals    : np.ndarray | None — per-feature SHAP contributions
        base_value   : float | None — SHAP expected model output
        shap_feature_names : list[str] — display names for each SHAP feature
        data_label   : str — "SIMULATION" (sliders) or "LIVE" (from API)
    """
    input_data = build_feature_dataframe(rainfall_mm, wind_kmh)
    raw_score = float(risk_model.predict(input_data)[0])
    risk_score = max(0.0, min(100.0, raw_score))
    risk_level, risk_color = classify_risk(risk_score)

    shap_vals = None
    base_value = None

    if explainer is not None:
        try:
            sv = explainer.shap_values(input_data)
            # Handle both 2D (n_samples, n_features) and 1D arrays
            if hasattr(sv, "shape") and len(sv.shape) == 2:
                shap_vals = np.array([float(v) for v in sv[0]])
            elif isinstance(sv, (list, np.ndarray)):
                arr = np.array(sv)
                if arr.ndim == 2:
                    shap_vals = arr[0].astype(float)
                elif arr.ndim == 1:
                    shap_vals = arr.astype(float)
            base_value = float(explainer.expected_value)
        except Exception:
            shap_vals = None

    return {
        "input_data": input_data,
        "raw_score": raw_score,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "shap_vals": shap_vals,
        "base_value": base_value,
        "shap_feature_names": [
            "Daily Rainfall (mm)",
            "Cyclone Wind (km/h)",
            "Rainfall Lag 1-Day",
            "Rainfall Lag 3-Day",
            "Wind Lag 1-Day",
        ],
        "data_label": "SIMULATION",
    }


def classify_risk(risk_score: float) -> tuple:
    """
    Classify risk into levels calibrated to the model's actual output range (0–39 for typical inputs).

    Returns:
        (level_str, hex_color)
    """
    if risk_score < 10:
        return ("LOW", "#2EA043")
    elif risk_score < 20:
        return ("MODERATE", "#58A6FF")
    elif risk_score < 30:
        return ("HIGH", "#D29922")
    else:
        return ("CRITICAL", "#F85149")


def load_risk_model(
    model_path: str = "models/risk_model/best_risk_model.pkl",
    explainer_path: str = "models/risk_model/explainer.pkl",
):
    """
    Load the XGBoost model and SHAP TreeExplainer from disk.
    Returns (model, explainer) or (None, None) if files are missing.
    """
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(explainer_path, "rb") as f:
            explainer = pickle.load(f)
        return model, explainer
    except Exception:
        return None, None
