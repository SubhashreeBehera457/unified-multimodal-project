from pydantic import BaseModel
from typing import Optional, Dict, Any

class FusionRequest(BaseModel):
    vision_score: Optional[float] = None
    vision_label: Optional[str] = None
    text_prob_genuine: Optional[float] = None
    text_label: Optional[str] = None

class FusionResponse(BaseModel):
    fusion_score: float
    fusion_title: str
    fusion_color: str
    fusion_method: str
    vision_contribution: float
    text_contribution: float
    vision_label: str
    text_label: str
    recommended_action: str
    fusion_type: str = "DECISION_LEVEL"
    limitation_notice: str
    data_label: str = "MODEL GENERATED"
    timestamp: str
