# Unified Disaster Management System: Project Report

## 1. Problem Statement
In the event of natural disasters such as cyclones and flash floods, emergency response agencies face critical delays caused by fragmented information. Decision-makers often lack real-time integration between meteorological telemetry (e.g., rainfall, wind speed) and on-the-ground visual assessments. Furthermore, the rapid spread of misinformation on social media severely hampers rescue operations by directing resources to false incidents. There is a pressing need for a unified, intelligent system that can dynamically fuse multimodal data to verify incidents, predict risks, and optimize rescue routing in real time.

## 2. Objective
The primary objective of this project is to develop a **Unified Disaster Response Intelligence Platform** capable of:
1. Predicting flood and cyclone risks using historical and real-time meteorological data.
2. Filtering and verifying social media reports to separate genuine distress signals from misinformation.
3. Fusing Natural Language Processing (NLP) intelligence with Computer Vision assessments of crisis imagery.
4. Dynamically routing rescue teams around blocked or hazardous roads using graph-based routing algorithms.

## 3. Proposed Solution & Architecture
The system acts as a centralized "Command Center" (built using Python and Streamlit) that continuously ingests and processes multimodal data streams. 

### 3.1 AI Modalities Used
- **Risk Prediction Engine (XGBoost):** A time-series enabled regression model that ingests daily rainfall (Odisha datasets) and cyclone wind speeds (IBTrACS) to generate a normalized `Risk_Score`. It uses Explainable AI (SHAP) to interpret feature importance in real-time.
- **Misinformation Intelligence (DistilBERT):** A fine-tuned transformer model for Sequence Classification. It analyzes social media text embeddings to classify reports as "Verified Genuine" or "False/Misleading" with high confidence.
- **Visual Assessment (ResNet50):** A deep Convolutional Neural Network (CNN) adapted for image classification to analyze drone or satellite imagery and categorize structural damage (No Damage, Mild Damage, Severe Damage).

## 4. Workflow Integration
1. **Phase 1: Pre-Disaster Telemetry:** Environmental sensors feed data into the XGBoost model to continuously output a baseline risk score.
2. **Phase 2: Social Intelligence:** Crowdsourced text is ingested and routed through the DistilBERT NLP filter to verify authenticity.
3. **Phase 3: Cross-Modal Fusion:** If an incident is flagged, live images are requested and passed through the ResNet50 model. The system fuses the verified NLP intent with the CNN damage classification to assign a final incident severity.
4. **Phase 4: Tactical Routing:** The incident coordinates are passed to an OSRM routing API, calculating the safest path for emergency response teams using Dijkstra’s algorithm, intentionally bypassing active hazard zones.

## 5. Results & Performance Comparison

### 5.1 Pre-Disaster Risk (Time-Series XGBoost)
- The model successfully learned non-linear interactions between rainfall lag features and wind speeds. 
- Using SHAP values, we demonstrated that continuous rainfall over a 3-day window (`Rain_Lag3`) paired with high sustained winds heavily drives the critical risk threshold.

### 5.2 Misinformation NLP Model
A comparison of the deployed DistilBERT model against traditional Machine Learning baselines on the validation dataset:

| Model Architecture | Accuracy | F1-Score (Critical) | Latency |
|--------------------|----------|---------------------|---------|
| TF-IDF + Naive Bayes | 88.43% | 54.26% | Low |
| TF-IDF + Logistic Reg. | 88.39% | 54.17% | Low |
| **DistilBERT (Deployed)** | **84.12%** | **83.50%** | Medium |

*Observation:* While baseline models had high overall accuracy, their F1-score for correctly classifying rare, critical genuine reports was poor (~54%). DistilBERT achieved a highly balanced F1-score of **83.50%**, making it significantly more reliable for critical deployment where false negatives cost lives.

### 5.3 UI / UX
- The Command Center dashboard was completely refactored to use responsive CSS Grids, ensuring scalability and operability across mobile devices in the field, tablets, and desktop displays.

## 6. Conclusion
The Unified Disaster Management System successfully demonstrates how disjointed data modalities—structured meteorological metrics, unstructured text, and visual imagery—can be synchronized into a single operational dashboard. By integrating Explainable AI (SHAP), the system builds trust with human operators. The deployment of advanced models like DistilBERT and ResNet50 significantly reduces the noise of misinformation and accelerates emergency response times through dynamic, hazard-aware routing. 

## 7. Folder Structure Guide
If you are reviewing this project, the code has been structured as follows for clarity:
- `app.py`: The main responsive Streamlit dashboard. Run `streamlit run app.py` to start.
- `docs/`: Contains project architecture diagrams, slide decks, and detailed breakdown documentation.
- `data/`: Contains the raw datasets (`ibtracs.NI.list.v04r01.csv` & `rainfall...csv`).
- `notebooks/`: Contains `Disaster_Model_EDA_Training.ipynb`, a fully executed Jupyter notebook detailing the data exploration, feature engineering, and model training.
- `scripts/`: Python scripts for model training (`train_risk_xai.py`, `train_misinfo.py`, etc.).
- `models/`: Saved model weights (`.pkl`, `.pth`) loaded dynamically by the dashboard.
