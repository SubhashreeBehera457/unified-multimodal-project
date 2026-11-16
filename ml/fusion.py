"""
ml/fusion.py
─────────────
Decision-level multimodal fusion engine.

Architecture:
  Vision (ResNet-50) result + Text (DistilBERT) result
          ↓                          ↓
    damage_score              prob_genuine
    (0.0–1.0)                  (0.0–1.0)
          ↓                          ↓
          └──────── fusion ──────────┘
                        ↓
                 fusion_score (0.0–1.0)
                        ↓
                 incident assessment
                        ↓
                 recommended action

IMPORTANT:
  This is DECISION-LEVEL FUSION, not CROSS-MODAL ATTENTION FUSION.

  There is NO trained neural fusion model (models/fusion_model/ is empty).
  train_fusion.py uses SyntheticFusionDataset and its weights were never committed.

  The fusion implemented here is:
    - Transparent (fully deterministic, documented)
    - Explainable (each component's contribution is shown)
    - Honest (no fake "attention weights")

  When both modalities are available:
    fusion_score = vision_damage_score × 0.6 + text_genuine_prob × 0.4

  When only one modality is available:
    fusion_score = that modality's score (single-modal result)

  The 60/40 weighting reflects that visual damage evidence
  typically carries stronger incident confirmation than a text classification.
  This weighting is a configurable design choice, not a learned parameter.

Decision thresholds:
  fusion_score ≥ 0.7  → HIGH INCIDENT CONFIDENCE
  0.4 ≤ score < 0.7   → MODERATE INCIDENT CONFIDENCE
  score < 0.4         → LOW INCIDENT CONFIDENCE / MONITOR
"""


VISION_WEIGHT = 0.6   # weight for visual damage score in dual-modality fusion
TEXT_WEIGHT = 0.4     # weight for text genuine probability in dual-modality fusion


def run_fusion(
    vision_result: dict = None,
    text_result: dict = None,
) -> dict:
    """
    Compute decision-level fusion from vision and/or text results.

    Args:
        vision_result : Output dict from ml.vision.classify_multiple_images()
                        or ml.vision.classify_single_image()
                        (needs keys: aggregate_score or damage_score, aggregate_class or damage_class)
        text_result   : Output dict from ml.misinformation.run_distilbert()
                        (needs keys: prob_genuine, classification, confidence)

    Returns dict:
        fusion_score       : float (0–1)
        fusion_title       : str — "HIGH/MODERATE/LOW INCIDENT CONFIDENCE"
        fusion_color       : str — hex color
        fusion_method      : str — description of how fusion was computed
        vision_contribution: float — vision component value used
        text_contribution  : float — text component value used
        vision_label       : str — display string for vision input
        text_label         : str — display string for text input
        recommended_action : str — operational guidance
        fusion_type        : str — always "DECISION_LEVEL" (not attention)
        limitation_notice  : str — honest limitation description
    """
    vision_score = None
    vision_label = "NOT RUN"
    text_score = None
    text_label = "NOT RUN"

    # ── Parse vision result ──────────────────────────────────────────────────
    vision_is_valid = True
    if vision_result is not None:
        agg_class = vision_result.get("aggregate_class") or vision_result.get("damage_class", "UNKNOWN")
        vision_is_valid = vision_result.get("is_valid", agg_class != "INVALID IMAGE")
        
        if not vision_is_valid or "INVALID" in agg_class.upper():
            vision_score = 0.0
            vision_label = "INVALID IMAGE (OUT-OF-DOMAIN)"
            vision_is_valid = False
        else:
            agg_score = vision_result.get("aggregate_score")
            dmg_score = vision_result.get("damage_score")
            vision_score = agg_score if agg_score is not None else (dmg_score if dmg_score is not None else 0.0)
            n_imgs = vision_result.get("image_count", 1)
            img_str = f" ({n_imgs} image{'s' if n_imgs != 1 else ''})" if n_imgs > 1 else ""
            vision_label = f"{agg_class}{img_str}"

    # ── Parse text result ────────────────────────────────────────────────────
    if text_result is not None:
        text_score = float(text_result.get("prob_genuine", 0.0))
        classif = text_result.get("classification", "UNKNOWN")
        text_conf = text_result.get("confidence", 0.0)
        text_label = f"{classif} ({text_conf:.0%})"

    # ── Fusion computation ───────────────────────────────────────────────────
    if vision_score is not None and text_score is not None:
        if not vision_is_valid:
            # Image was invalid, do not allow it to affect score or inflate confidence
            fusion_score = text_score * 0.5
            fusion_method = "Text only (discounted) — vision input rejected as out-of-domain"
            vision_contribution = 0.0
            text_contribution = round(fusion_score, 4)
        else:
            fusion_score = vision_score * VISION_WEIGHT + text_score * TEXT_WEIGHT
            fusion_method = (
                f"Vision × {VISION_WEIGHT:.0%} + Text × {TEXT_WEIGHT:.0%} "
                f"(dual-modality decision fusion)"
            )
            vision_contribution = round(vision_score * VISION_WEIGHT, 4)
            text_contribution = round(text_score * TEXT_WEIGHT, 4)
    elif vision_score is not None:
        if not vision_is_valid:
            fusion_score = 0.0
            fusion_method = "Vision invalid — out-of-domain image uploaded"
            vision_contribution = 0.0
            text_contribution = 0.0
        else:
            fusion_score = vision_score
            fusion_method = "Vision only — text analysis not run (single-modality)"
            vision_contribution = vision_score
            text_contribution = 0.0
    elif text_score is not None:
        fusion_score = text_score
        fusion_method = "Text only — no image uploaded (single-modality)"
        vision_contribution = 0.0
        text_contribution = text_score
    else:
        # No modalities at all
        return {
            "fusion_score": 0.0,
            "fusion_title": "NO INPUT",
            "fusion_color": "#8B949E",
            "fusion_method": "No modalities provided",
            "vision_contribution": 0.0,
            "text_contribution": 0.0,
            "vision_label": "NOT RUN",
            "text_label": "NOT RUN",
            "recommended_action": "Upload image and/or enter text to activate fusion.",
            "fusion_type": "DECISION_LEVEL",
            "limitation_notice": (
                "No trained neural fusion model exists. "
                "This is deterministic decision-level combination."
            ),
        }

    fusion_score = round(min(1.0, max(0.0, fusion_score)), 4)

    # ── Decision thresholds ──────────────────────────────────────────────────
    if fusion_score >= 0.7:
        fusion_title = "HIGH INCIDENT CONFIDENCE"
        fusion_color = "#F85149"
        recommended_action = "DISPATCH HEAVY RESCUE — PRIORITY 1"
    elif fusion_score >= 0.4:
        fusion_title = "MODERATE INCIDENT CONFIDENCE"
        fusion_color = "#D29922"
        recommended_action = "DEPLOY RAPID ASSESSMENT CREW — PRIORITY 2"
    else:
        fusion_title = "LOW INCIDENT CONFIDENCE"
        fusion_color = "#2EA043"
        recommended_action = "MONITOR — DO NOT OVER-DEPLOY RESOURCES"

    return {
        "fusion_score": fusion_score,
        "fusion_title": fusion_title,
        "fusion_color": fusion_color,
        "fusion_method": fusion_method,
        "vision_contribution": vision_contribution,
        "text_contribution": text_contribution,
        "vision_label": vision_label,
        "text_label": text_label,
        "recommended_action": recommended_action,
        "fusion_type": "DECISION_LEVEL",
        "limitation_notice": (
            "ResNet-50 fine-tuned on CrisisMMD multimodal disaster imagery and verified control baselines. "
            "Decision-level fusion provides transparent, explainable joint damage and credibility escalation."
        ),
    }
