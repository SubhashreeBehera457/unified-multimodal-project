"""
backend/api/vision.py
─────────────────────
ResNet-50 visual damage assessment endpoint.
Supports single or multi-image uploads, validity gating, and aggregations.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from PIL import Image
import io
from datetime import datetime

from backend.model_loader import model_manager
from backend.schemas.vision import VisionResponse, SingleImageVisionResult
from ml.vision import classify_multiple_images

router = APIRouter(prefix="/vision", tags=["Vision Analysis"])


@router.post("/analyze", response_model=VisionResponse)
async def analyze_images(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No image files provided.")

    model = model_manager.get_vision_model(force_reload=True)
    if model is None:
        raise HTTPException(status_code=503, detail="ResNet-50 vision model is not available or failed to load.")

    pil_images = []
    filenames = []
    for file in files:
        try:
            content = await file.read()
            img = Image.open(io.BytesIO(content))
            pil_images.append(img)
            filenames.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read image '{file.filename}': {str(e)}")

    try:
        agg = classify_multiple_images(pil_images=pil_images, model=model)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        individual_results = []
        for fn, res in zip(filenames, agg["individual_results"]):
            individual_results.append(SingleImageVisionResult(
                filename=fn,
                damage_class=res["damage_class"],
                class_idx=res["class_idx"],
                confidence=round(res["confidence"], 4),
                all_probs=[round(p, 4) for p in res["all_probs"]],
                damage_score=res["damage_score"],
                is_valid=res.get("is_valid", True),
                risk_level=res.get("risk_level", "LOWER RISK"),
                limitation=res["limitation"],
            ))

        return VisionResponse(
            image_count=agg["image_count"],
            aggregate_score=agg["aggregate_score"],
            aggregate_class=agg["aggregate_class"],
            aggregate_class_idx=agg["aggregate_class_idx"],
            is_valid=agg.get("is_valid", True),
            risk_level=agg.get("risk_level", "LOWER RISK"),
            severity_summary=agg["severity_summary"],
            individual_results=individual_results,
            model_name="ResNet-50 CrisisMMD Fine-Tuned Damage Classifier",
            limitation=agg.get("limitation", "Trained on CrisisMMD multimodal disaster imagery and verified control benchmarks"),
            data_label="MODEL GENERATED",
            timestamp=now_str,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision inference error: {str(e)}")
