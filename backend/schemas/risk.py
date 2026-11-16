from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RiskPredictRequest(BaseModel):
    rainfall_mm: float = Field(..., ge=0.0, le=1000.0, description="Manual daily rainfall in mm")
    wind_kmh: float = Field(..., ge=0.0, le=400.0, description="Cyclone wind speed in km/h")
    source: str = "SIMULATION"  # "SIMULATION" | "LIVE"

class ShapContribution(BaseModel):
    feature: str
    value: float
    contribution: float  # SHAP value in risk-score units

class RiskPredictResponse(BaseModel):
    raw_score: float
    risk_score: float  # clipped to [0, 100]
    risk_level: str    # "LOW" | "MODERATE" | "HIGH" | "CRITICAL"
    risk_color: str
    operational_threshold_crossed: bool  # True if risk_score >= 70.0
    shap_contributions: List[ShapContribution]
    base_value: Optional[float] = None
    input_features: Dict[str, float]
    model_name: str = "XGBoost Regressor"
    data_label: str  # "MODEL GENERATED"
    calibrated_note: str
    timestamp: str
