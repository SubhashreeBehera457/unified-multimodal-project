"""
backend/api/fusion.py
─────────────────────
Multimodal fusion endpoint combining visual damage assessment and text credibility.
Clearly labeled as decision-level transparent combination (no fake neural attention).
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.schemas.fusion import FusionRequest, FusionResponse
from ml.fusion import run_fusion

router = APIRouter(prefix="/fusion", tags=["Multimodal Fusion"])


@router.post("/combine", response_model=FusionResponse)
def combine_modalities(req: FusionRequest):
    vision_result = None
    if req.vision_score is not None or req.vision_label is not None:
        v_label = req.vision_label or "DAMAGE OBSERVED"
        is_val = "INVALID" not in v_label.upper()
        vision_result = {
            "aggregate_score": req.vision_score or 0.0,
            "aggregate_class": v_label,
            "is_valid": is_val,
            "confidence": req.vision_score or 0.0,
            "image_count": 1,
        }

    text_result = None
    if req.text_prob_genuine is not None:
        text_result = {
            "prob_genuine": req.text_prob_genuine,
            "classification": req.text_label or ("VERIFIED GENUINE" if req.text_prob_genuine >= 0.5 else "LIKELY MISLEADING"),
            "confidence": max(req.text_prob_genuine, 1.0 - req.text_prob_genuine),
        }

    res = run_fusion(vision_result=vision_result, text_result=text_result)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return FusionResponse(
        fusion_score=res["fusion_score"],
        fusion_title=res["fusion_title"],
        fusion_color=res["fusion_color"],
        fusion_method=res["fusion_method"],
        vision_contribution=res["vision_contribution"],
        text_contribution=res["text_contribution"],
        vision_label=res["vision_label"],
        text_label=res["text_label"],
        recommended_action=res["recommended_action"],
        fusion_type=res["fusion_type"],
        limitation_notice=res["limitation_notice"],
        data_label="MODEL GENERATED",
        timestamp=now_str,
    )
