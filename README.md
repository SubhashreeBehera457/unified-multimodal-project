# UNIFIED MULTIMODAL DISASTER MANAGEMENT SYSTEM
## Real-Time Emergency Operations & Intelligence Command Center

An AI-powered, multimodal, explainable intelligence platform designed for emergency operations centers (EOC) and first responders. Bridges proactive hazard prediction, real-time social & news verification, visual damage assessment, and rescue routing.

---

## 🏛️ System Architecture

```text
               EXTERNAL DATA SOURCES & APIs
 [Open-Meteo Weather]   [GDACS Alert RSS]   [GDELT News Feed]   [OSRM Routing]
          │                    │                   │                  │
          ▼                    ▼                   ▼                  ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                             SERVICES TIER                                  │
│   services/weather.py   services/gdacs.py   services/social.py  routing.py │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        MACHINE LEARNING ENGINE                             │
│   ml/risk.py          ml/misinformation.py    ml/vision.py    ml/fusion.py │
│   (XGBoost + SHAP)    (DistilBERT NLP)        (ResNet-50)     (Decision)   │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND                                 │
│   backend/main.py             backend/state.py         backend/model_loader│
│   ├── /api/health             ├── /api/dashboard       ├── /api/incidents │
│   ├── /api/weather            ├── /api/gdacs           ├── /api/risk      │
│   ├── /api/misinformation     ├── /api/vision          ├── /api/fusion    │
│   ├── /api/routing            ├── /api/social          └── /ws/live (WS)  │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       ▼  REST / WebSocket (JSON)
┌────────────────────────────────────────────────────────────────────────────┐
│                       REACT OPERATIONAL FRONTEND                           │
│   React 18 + TypeScript + Vite + Tailwind CSS + Leaflet + Lucide Icons     │
│   ├── Command Center (Tactical Map, Live Incident Stream, KPI Telemetry)   │
│   ├── Pre-Disaster Risk (XGBoost Simulator, SHAP Feature Attributions)     │
│   ├── Misinformation (DistilBERT Analyzer, GDELT Live Feed, Truth Discl.) │
│   ├── Multimodal Analysis (Damage Photos Upload, ResNet-50, Fusion Engine)│
│   └── Rescue Routing (OSRM Road Navigation, ETA, Team Dispatch)            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Run Commands

### Prerequisites
- Python 3.10+ (with virtual environment)
- Node.js v18+ and npm

### 1. Backend Setup (FastAPI)
```bash
# Activate virtual environment
# Windows:
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
pip install fastapi uvicorn[standard] pydantic python-dotenv

# Start FastAPI Intelligence API on port 8000
uvicorn backend.main:app --reload --port 8000
```
API Documentation will be accessible at: `http://localhost:8000/docs`

### 2. Frontend Setup (React + Vite)
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server on port 5173
npm run dev
```
Open Command Center in browser at: `http://localhost:5173/`

### 3. Streamlit Fallback (Legacy Presentation Layer)
The existing Streamlit application remains functional and untouched as a fallback:
```bash
streamlit run app.py
```

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description | Data Status |
|--------|----------|-------------|-------------|
| `GET` | `/` | API status and root metadata | SYSTEM |
| `GET` | `/api/health` | Comprehensive service & model reachability check | LIVE / SYSTEM |
| `GET` | `/api/dashboard` | Aggregated telemetry, KPIs, weather, incidents | LIVE / AGGREGATED |
| `GET` | `/api/incidents` | List active emergency incidents with filters | LIVE / SIMULATION |
| `POST`| `/api/incidents` | Register a new incident report | USER / SIMULATION |
| `POST`| `/api/incidents/dispatch` | Dispatch rescue team to incident | OPERATION |
| `GET` | `/api/weather` | Open-Meteo observations for Bhubaneswar/Odisha | `[ LIVE ] Open-Meteo` |
| `GET` | `/api/gdacs` | Global Disaster Alert & Coordination System RSS | `[ LIVE ] GDACS` |
| `GET` | `/api/risk/latest` | Latest cached/baseline hazard risk evaluation | `[ MODEL GENERATED ]` |
| `POST`| `/api/risk/predict` | XGBoost risk inference + SHAP feature attributions | `[ MODEL GENERATED ]` |
| `POST`| `/api/misinformation/analyze`| DistilBERT tweet/report credibility evaluation | `[ MODEL GENERATED ]` |
| `POST`| `/api/vision/analyze` | ResNet-50 visual damage assessment (Single/Multi) | `[ MODEL GENERATED ]` |
| `POST`| `/api/fusion/combine` | Transparent decision-level multimodal fusion | `[ MODEL GENERATED ]` |
| `POST`| `/api/routing/calculate` | OSRM shortest road driving path & duration | `[ LIVE ] OSRM` |
| `GET` | `/api/social/gdelt` | GDELT DOC 2.0 live disaster news articles | `[ LIVE ] GDELT` |
| `GET` | `/api/social/x` | Live X (Twitter) disaster tweets ingestion | Config-dependent |
| `GET` | `/api/social/reddit` | Reddit disaster subreddit posts | Config-dependent |
| `WS`  | `/ws/live` | WebSocket telemetry pulse (every 4s) | REAL-TIME STREAM |

---

## 🔗 Live Integrations & Status

### Active Live Integrations
1. **Open-Meteo Weather API (`services/weather.py`)**:
   - Status: **`ONLINE`**
   - No credentials required. Pulls live temperature, precipitation accumulation (24h), wind speed, and WMO codes.
2. **GDACS RSS (`services/gdacs.py`)**:
   - Status: **`ONLINE`**
   - European Union GDACS public alert feed. Parses live flood, cyclone, and earthquake events worldwide with coordinates and population at risk.
3. **GDELT News Feed (`services/social.py`)**:
   - Status: **`ONLINE`**
   - Global Knowledge Graph DOC 2.0 API. Pulls live English disaster headlines.
4. **OSRM Routing (`services/routing.py`)**:
   - Status: **`ONLINE`**
   - Open Source Routing Machine public routing server. Calculates driving polyline, distance (km), and duration (min).

### External Integrations Requiring Credentials
1. **X (Twitter) API v2**:
   - Status: **`NOT CONFIGURED`** (requires `X_BEARER_TOKEN` in `.env`).
   - Explicitly labeled in the UI as *[ UNAVAILABLE ] X/Twitter*. No fake posts are generated.
2. **Reddit API**:
   - Status: **`NOT CONFIGURED`** (requires `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env`).
   - Explicitly labeled in the UI as *[ UNAVAILABLE ] Reddit*.

---

## 🧠 Machine Learning Models & Scientific Integrity

### 1. XGBoost Hazard Risk Model (`ml/risk.py`)
- **Trained on:** Odisha daily rainfall records combined with NOAA IBTrACS cyclone track data.
- **Output:** Normalized hazard risk score (0–100 scale).
- **Features Used:**
  1. `Manual Daily Rainfall (mm)`
  2. `WMO_WIND` (cyclone wind speed km/h)
  3. `Rain_Lag1` (synthetic proxy)
  4. `Rain_Lag3` (synthetic proxy)
  5. `Wind_Lag1` (synthetic proxy)
- **Note on River Level:** River gauge level is logged purely as local environmental telemetry context and is **NOT** a trained feature of the XGBoost model.
- **Explainability:** Generates per-feature attributions using `shap.TreeExplainer` in risk points.

### 2. DistilBERT Misinformation Filter (`ml/misinformation.py`)
- **Trained on:** Kaggle "Natural Language Processing with Disaster Tweets" dataset (84.1% validation accuracy, 83.5% F1).
- **Function:** Classifies whether text pattern linguistically resembles authentic crisis communications.
- **Disclaimer:** AI classification reflects linguistic resemblance, **not** independent factual ground truth.

### 3. ResNet-50 Visual Damage Classifier (`ml/vision.py`)
- **Architecture:** ResNet-50 fine-tuned on 3 classes (`NO DAMAGE`, `MILD DAMAGE`, `SEVERE DAMAGE`).
- **Critical Model Limitation:** The prototype weights were trained on synthetic noise representations. All outputs are explicitly tagged:
  `ARCHITECTURAL PROTOTYPE (Trained on synthetic noise; not validated for live field operations)`.

### 4. Multimodal Fusion Engine (`ml/fusion.py`)
- **Fusion Type:** **Decision-Level Fusion** (60% Vision Damage Score + 40% Text Credibility Score).
- **Integrity Notice:** No neural cross-modal attention checkpoint is stored in `models/fusion_model/`. The fusion logic is transparent, deterministic, and explainable without fabricated attention maps.

### 5. OSRM Rescue Routing (`services/routing.py`)
- **Route Type:** **`STANDARD ROAD ROUTING`**.
- **Disclaimer:** Routes represent the fastest standard driving road paths. The system does not claim automatic real-time flood/hazard avoidance unless dedicated road closure barriers are provided.

---

## 🔒 Security & Data Integrity
- **Zero Frontend Secrets:** No API tokens, keys, or credentials exist in the client-side code.
- **Source Badges:** Every datum displays its provenance:
  - `[ LIVE ]` for fresh external API responses.
  - `[ MODEL GENERATED ]` for ML model inferences.
  - `[ SIMULATION ]` for operator slider inputs and demo scenarios.
  - `[ UNAVAILABLE ]` for unconfigured or unreachable integrations.
