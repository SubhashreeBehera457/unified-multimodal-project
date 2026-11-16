from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SingleImageVisionResult(BaseModel):
    filename: Optional[str] = None
    damage_class: str  # "NO DAMAGE" | "MILD DAMAGE" | "SEVERE DAMAGE" | "INVALID IMAGE"
    class_idx: int
    confidence: float
    all_probs: List[float]
    damage_score: float
    is_valid: bool = True
    risk_level: str = "LOWER RISK"  # "LOWER RISK" | "MODERATE RISK" | "HIGH RISK" | "INVALID"
    limitation: str

class VisionResponse(BaseModel):
    image_count: int
    aggregate_score: float
    aggregate_class: str
    aggregate_class_idx: int
    is_valid: bool = True
    risk_level: str = "LOWER RISK"
    severity_summary: Dict[str, int]
    individual_results: List[SingleImageVisionResult]
    model_name: str = "ResNet-50 CrisisMMD Calibrated Damage Classifier"
    limitation: str = "Trained on CrisisMMD multimodal disaster imagery and verified control benchmarks"
    data_label: str = "MODEL GENERATED"
    timestamp: str
