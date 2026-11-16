"""
ml/misinformation.py
─────────────────────
DistilBERT misinformation / disaster tweet classification.

Model context (from train_misinfo.py):
  Fine-tuned on the Kaggle "Natural Language Processing with Disaster Tweets" dataset.
  Label schema:
    label = 1  → "real disaster tweet" (GENUINE)
    label = 0  → "not a real disaster tweet" (NOT INFORMATIVE / MISLEADING)

IMPORTANT LIMITATIONS:
  - The model detects whether text *resembles* a real disaster tweet, not whether
    the described event is actually occurring.
  - High confidence (e.g. P=0.94) means the text pattern matches real disaster tweet
    training examples. It does NOT verify the factual claim.
  - Verification status labels are model outputs only.

Accuracy on validation set: 84.12% (see models/nlp_model_comparison.csv)
F1 Score (Critical): 83.50%
"""
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from typing import Optional


def load_misinfo_model(
    model_dir: str = "models/misinformation_filter",
):
    """
    Load fine-tuned DistilBERT tokenizer and classifier from disk.
    Returns (tokenizer, model) or (None, None) if files are missing.
    """
    try:
        tokenizer = DistilBertTokenizer.from_pretrained(model_dir)
        model = DistilBertForSequenceClassification.from_pretrained(model_dir)
        model.eval()
        return tokenizer, model
    except Exception:
        return None, None


def run_distilbert(
    text: str,
    tokenizer,
    model,
    max_length: int = 128,
) -> dict:
    """
    Run DistilBERT classification on text.

    Args:
        text        : Cleaned report text (use services.social.clean_text first)
        tokenizer   : Loaded DistilBertTokenizer
        model       : Loaded DistilBertForSequenceClassification (eval mode)
        max_length  : Max token length (128 matches training)

    Returns dict:
        text                : str — analyzed text
        prob_genuine        : float — P(label=1, real disaster tweet)
        prob_misleading     : float — P(label=0, not real)
        is_genuine          : bool — prob_genuine >= 0.5
        confidence          : float — max(prob_genuine, prob_misleading)
        credibility_score   : int — prob_genuine * 100 (display value)
        classification      : str — "VERIFIED GENUINE" | "LIKELY MISLEADING"
        verification_status : str — "LIKELY GENUINE" | "UNCERTAIN" | "LIKELY MISLEADING"
        recommended_action  : str — operational guidance
    """
    if not text or not text.strip():
        raise ValueError("Text input cannot be empty.")

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=max_length,
    )
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        prob_genuine = float(probs[0][1].item())   # label=1 → real disaster
        prob_misleading = float(probs[0][0].item()) # label=0 → not real

    is_genuine = prob_genuine >= 0.5
    confidence = max(prob_genuine, prob_misleading)

    # Verification status
    if prob_genuine >= 0.65:
        verification_status = "LIKELY GENUINE"
    elif prob_genuine >= 0.35:
        verification_status = "UNCERTAIN"
    else:
        verification_status = "LIKELY MISLEADING"

    if is_genuine:
        recommended_action = "DISPATCH VERIFICATION TEAM — PRIORITY HIGH"
    elif prob_genuine >= 0.35:
        recommended_action = "MONITOR — UNCERTAIN CLASSIFICATION"
    else:
        recommended_action = "FLAG REPORT — DO NOT DISPATCH BASED ON THIS ALONE"

    return {
        "text": text,
        "prob_genuine": prob_genuine,
        "prob_misleading": prob_misleading,
        "is_genuine": is_genuine,
        "confidence": confidence,
        "credibility_score": int(round(prob_genuine * 100)),
        "classification": "VERIFIED GENUINE" if is_genuine else "LIKELY MISLEADING",
        "verification_status": verification_status,
        "recommended_action": recommended_action,
        "verified": is_genuine,  # for report store compat
    }


def batch_classify(
    texts: list,
    tokenizer,
    model,
    batch_size: int = 8,
) -> list:
    """
    Classify a list of texts in batches.
    Returns list of result dicts (same schema as run_distilbert).
    """
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for text in batch:
            try:
                results.append(run_distilbert(text, tokenizer, model))
            except Exception as e:
                results.append({
                    "text": text,
                    "prob_genuine": 0.0,
                    "prob_misleading": 1.0,
                    "is_genuine": False,
                    "confidence": 1.0,
                    "credibility_score": 0,
                    "classification": "CLASSIFICATION ERROR",
                    "verification_status": "UNVERIFIED",
                    "recommended_action": f"Error: {e}",
                    "verified": False,
                })
    return results
