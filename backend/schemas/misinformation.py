from pydantic import BaseModel, Field
from typing import Optional

class MisinfoAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Incident report text to analyze")
    source: Optional[str] = "MANUAL_INPUT"

class MisinfoAnalyzeResponse(BaseModel):
    text: str
    cleaned_text: str
    prob_genuine: float
    prob_misleading: float
    is_genuine: bool
    confidence: float
    credibility_score: int  # 0-100
    classification: str     # "VERIFIED GENUINE" | "LIKELY MISLEADING"
    verification_status: str # "LIKELY GENUINE" | "UNCERTAIN" | "LIKELY MISLEADING"
    recommended_action: str
    model_name: str = "DistilBERT (Fine-tuned)"
    disclaimer: str = "AI classification reflects linguistic pattern resemblance to disaster reports, not independent factual ground truth."
    data_label: str = "MODEL GENERATED"
    timestamp: str
