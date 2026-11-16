"""
backend/model_loader.py
───────────────────────
Singleton manager for all machine learning models.
Loads models at backend startup or on-demand, caching them in memory.
Does NOT alter the underlying ML models or logic.
"""
import logging
from typing import Tuple, Any, Optional

from ml.risk import load_risk_model
from ml.misinformation import load_misinfo_model
from ml.vision import load_image_model

logger = logging.getLogger("model_loader")


class ModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._init_models()
        return cls._instance

    def _init_models(self):
        self.risk_model = None
        self.explainer = None
        self.risk_model_status = "UNINITIALIZED"

        self.misinfo_tokenizer = None
        self.misinfo_model = None
        self.misinfo_status = "UNINITIALIZED"

        self.vision_model = None
        self.vision_status = "UNINITIALIZED"

    def load_all(self):
        self.get_risk_model()
        self.get_misinfo_model()
        self.get_vision_model()

    def get_risk_model(self) -> Tuple[Any, Any]:
        if self.risk_model is None:
            try:
                model, explainer = load_risk_model(
                    model_path="models/risk_model/best_risk_model.pkl",
                    explainer_path="models/risk_model/explainer.pkl",
                )
                if model is not None:
                    self.risk_model = model
                    self.explainer = explainer
                    self.risk_model_status = "ONLINE"
                    logger.info("XGBoost Risk Model and SHAP Explainer loaded successfully.")
                else:
                    self.risk_model_status = "UNAVAILABLE"
            except Exception as e:
                logger.error(f"Error loading Risk Model: {e}")
                self.risk_model_status = "UNAVAILABLE"
        return self.risk_model, self.explainer

    def get_misinfo_model(self) -> Tuple[Any, Any]:
        if self.misinfo_model is None:
            try:
                tokenizer, model = load_misinfo_model(
                    model_dir="models/misinformation_filter"
                )
                if model is not None and tokenizer is not None:
                    self.misinfo_tokenizer = tokenizer
                    self.misinfo_model = model
                    self.misinfo_status = "ONLINE"
                    logger.info("DistilBERT Misinformation Model loaded successfully.")
                else:
                    self.misinfo_status = "UNAVAILABLE"
            except Exception as e:
                logger.error(f"Error loading DistilBERT model: {e}")
                self.misinfo_status = "UNAVAILABLE"
        return self.misinfo_tokenizer, self.misinfo_model

    def get_vision_model(self, force_reload: bool = False) -> Any:
        if self.vision_model is None or force_reload:
            try:
                model = load_image_model()
                if model is not None:
                    self.vision_model = model
                    self.vision_status = "ONLINE"
                    logger.info("ResNet-50 Vision Model loaded successfully.")
                else:
                    self.vision_status = "UNAVAILABLE"
            except Exception as e:
                logger.error(f"Error loading ResNet-50 model: {e}")
                self.vision_status = "UNAVAILABLE"
        return self.vision_model

    def get_status(self) -> dict:
        return {
            "xgboost_risk": self.risk_model_status,
            "shap_explainer": "ONLINE" if self.explainer is not None else "UNAVAILABLE",
            "distilbert_misinfo": self.misinfo_status,
            "resnet_vision": self.vision_status,
            "multimodal_fusion": "ONLINE (DECISION_LEVEL)",  # honest: decision-level fusion code is online
        }


model_manager = ModelManager()
