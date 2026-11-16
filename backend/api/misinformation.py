"""
backend/api/misinformation.py
──────────────────────────────
DistilBERT NLP misinformation analysis endpoint.
Evaluates textual disaster reports for linguistic resemblance to real incident reports.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.model_loader import model_manager
from backend.state import state_manager
from backend.schemas.misinformation import MisinfoAnalyzeRequest, MisinfoAnalyzeResponse
from services.social import clean_text
from ml.misinformation import run_distilbert

router = APIRouter(prefix="/misinformation", tags=["Misinformation Analysis"])


@router.post("/analyze", response_model=MisinfoAnalyzeResponse)
def analyze_misinformation(req: MisinfoAnalyzeRequest):
    tokenizer, model = model_manager.get_misinfo_model()
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="DistilBERT NLP model is not available or failed to load.")

    cleaned = clean_text(req.text)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Text is empty after removing URLs and mentions.")

    try:
        res = run_distilbert(text=cleaned, tokenizer=tokenizer, model=model)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        response = MisinfoAnalyzeResponse(
            text=req.text,
            cleaned_text=cleaned,
            prob_genuine=round(res["prob_genuine"], 4),
            prob_misleading=round(res["prob_misleading"], 4),
            is_genuine=res["is_genuine"],
            confidence=round(res["confidence"], 4),
            credibility_score=res["credibility_score"],
            classification=res["classification"],
            verification_status=res["verification_status"],
            recommended_action=res["recommended_action"],
            model_name="DistilBERT (Kaggle Disaster Tweets Fine-Tuned)",
            disclaimer="AI classification indicates whether the message linguistically matches real disaster tweets. It is not an independent factual verification.",
            data_label="MODEL GENERATED",
            timestamp=now_str,
        )

        # Record in state reports store
        state_manager.add_report({
            "text": req.text,
            "raw_text": req.text,
            "source_platform": req.source or "MANUAL_INPUT",
            "ingested_at": now_str,
            "verification_status": res["verification_status"],
            "is_genuine": res["is_genuine"],
            "credibility_score": res["credibility_score"],
        })

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DistilBERT inference error: {str(e)}")
