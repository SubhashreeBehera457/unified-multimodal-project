"""
backend/api/risk.py
───────────────────
Pre-disaster risk analysis endpoint using trained XGBoost and SHAP Explainer.
Preserves existing model inference without modification.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.model_loader import model_manager
from backend.state import state_manager
from backend.schemas.risk import RiskPredictRequest, RiskPredictResponse, ShapContribution
from ml.risk import run_risk_inference

router = APIRouter(prefix="/risk", tags=["Risk Analysis"])


@router.get("/latest", response_model=RiskPredictResponse)
def get_latest_risk():
    if state_manager.latest_risk_result:
        return state_manager.latest_risk_result

    # Run default baseline prediction
    default_req = RiskPredictRequest(rainfall_mm=45.0, wind_kmh=65.0, source="SIMULATION")
    return predict_risk(default_req)


@router.post("/predict", response_model=RiskPredictResponse)
def predict_risk(req: RiskPredictRequest):
    risk_model, explainer = model_manager.get_risk_model()
    if risk_model is None:
        raise HTTPException(status_code=503, detail="XGBoost risk model is not available or failed to load.")

    try:
        inf = run_risk_inference(
            rainfall_mm=req.rainfall_mm,
            wind_kmh=req.wind_kmh,
            risk_model=risk_model,
            explainer=explainer,
        )

        # Build structured SHAP contributions
        shap_contributions = []
        shap_vals = inf.get("shap_vals")
        feat_names = inf.get("shap_feature_names", [])
        input_data = inf.get("input_data")

        if shap_vals is not None and len(shap_vals) == len(feat_names):
            raw_vals = [
                req.rainfall_mm,
                req.wind_kmh,
                req.rainfall_mm * 0.8,
                req.rainfall_mm * 0.7,
                req.wind_kmh * 0.9,
            ]
            for name, val, sv in zip(feat_names, raw_vals, shap_vals):
                shap_contributions.append(ShapContribution(
                    feature=name,
                    value=round(val, 2),
                    contribution=round(float(sv), 4),
                ))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        risk_score = round(inf["risk_score"], 2)

        response = RiskPredictResponse(
            raw_score=round(inf["raw_score"], 2),
            risk_score=risk_score,
            risk_level=inf["risk_level"],
            risk_color=inf["risk_color"],
            operational_threshold_crossed=risk_score >= 70.0,
            shap_contributions=shap_contributions,
            base_value=round(inf["base_value"], 4) if inf.get("base_value") is not None else None,
            input_features={
                "Manual Daily Rainfall (mm)": req.rainfall_mm,
                "WMO_WIND": req.wind_kmh,
                "Rain_Lag1 (synthetic proxy)": round(req.rainfall_mm * 0.8, 2),
                "Rain_Lag3 (synthetic proxy)": round(req.rainfall_mm * 0.7, 2),
                "Wind_Lag1 (synthetic proxy)": round(req.wind_kmh * 0.9, 2),
            },
            model_name="XGBoost Regressor (Odisha Rainfall + IBTrACS Cyclone)",
            data_label="MODEL GENERATED",
            calibrated_note=(
                "Risk Score represents a normalized hazard index (calibrated 0–100 against historical extreme events). "
                "It is a comparative hazard score, NOT a calibrated percentage probability of disaster occurrence."
            ),
            timestamp=now_str,
        )

        state_manager.latest_risk_result = response.dict()
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
