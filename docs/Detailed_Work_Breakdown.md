# Detailed Day-by-Day Work Breakdown — Member Wise
### ~10-12 Working Days · 3 Members · Flood + Cyclone AI System

**How to use this document:** Each day has a problem statement, a concept to understand first, detailed steps in order, and a clear deliverable. This is the corrected, real version of your project — Phase 1 (predict risk) connected to Phase 2 (live evidence aggregation), not satellite-image damage assessment.

**Core idea, in one line:** Predict flood/cyclone risk before it happens, and once risk crosses a threshold, automatically pull together every scattered report coming in — tweets, news, photos — into one clear, continuously-updated picture.

**The gap you're filling:** Most published systems either predict disasters OR classify disaster reports. Very few connect the two into one continuous pipeline. That connection — not any single model — is your contribution. State it that way in the paper, every time.

---

# MEMBER 1 — Subhashree — Phase 1: Flood + Cyclone Risk Prediction

## Day 1 — Setup and getting cyclone data
**Problem this solves:** We don't have any cyclone data yet, and don't know its structure.

**Detailed steps:**
1. Go to https://www.ncei.noaa.gov/products/international-best-track-archive — download the IBTrACS North Indian Ocean basin subset as CSV
2. Open it, note down the columns (storm ID, timestamp, latitude, longitude, wind speed, pressure)
3. Read the CrisisMMD paper abstract (arxiv.org/abs/1805.00713) so you understand what Phase 2 will eventually receive from you — a risk score, not raw numbers

**Deliverable:** IBTrACS CSV downloaded, columns documented.

---

## Day 2 — Reading cyclone data programmatically
**Concept to learn first:** Time-series rows are sequentially dependent — order matters, unlike normal tabular data.

**Detailed steps:**
1. Load the CSV in pandas, check date range, storm count, missing values
2. Filter to storms with landfall near Odisha (latitude/longitude bounds)
3. Count how many relevant storms remain — if under ~15-20, flag this now (it caps how strong your results can be, and you'll need to say so honestly in the paper)
4. Print basic stats: wind speed range, pressure range for your filtered storms

**Deliverable:** Filtered cyclone dataset, documented sample size.

---

## Day 3 — Getting and reading flood data
**Detailed steps:**
1. Go to https://indiawris.gov.in (or IMD) and download rainfall/river-level data for coastal Odisha districts
2. Load it in pandas, check date range and missing values
3. Compare time periods — do your flood data dates roughly overlap with your cyclone events? (Note any gaps, since cyclones often cause the floods you're tracking)

**Deliverable:** Flood/rainfall dataset loaded and explored.

---

## Day 4 — Feature engineering for both hazards
**Concept to learn first:** A model can't take "all of history" — it needs fixed windows (e.g., last 7 days of rainfall → risk level).

**Detailed steps:**
1. For cyclone: build features — wind speed, central pressure, distance from coast, forward speed
2. For flood: build features — recent cumulative rainfall, river level trend
3. Handle missing values (simple interpolation is fine)
4. Split both datasets by time — train on older events, test on more recent ones, not a random split

**Deliverable:** Two feature-engineered, train/test-split datasets ready for modeling.

---

## Day 5 — Training the cyclone risk model
**Detailed steps:**
1. Train a Random Forest (or Gradient Boosting) classifier predicting cyclone severity category from your features
2. Evaluate with accuracy + F1-score (not just accuracy, given class imbalance is likely)
3. Record the real numbers — even if not perfect, this is normal for a first pass

**Deliverable:** Trained cyclone model with documented F1/accuracy.

---

## Day 6 — Training the flood risk model
**Detailed steps:**
1. Train the same type of model for flood risk level from your flood features
2. Evaluate the same way
3. If results are weak, try: more features, class weighting, or a slightly larger time window

**Deliverable:** Trained flood model with documented F1/accuracy.

---

## Day 7 — Packaging outputs for the bridge
**Problem this solves:** Sabyasachi and Chandrakant need your risk scores in one clean, consistent format to trigger Phase 2.

**Detailed steps:**
1. Convert both models' predictions into a standard format: risk score 0-1, per region, per date, per hazard
2. Generate a clean CSV output file
3. Write the threshold rule: `if flood_risk > X or cyclone_risk > X: activate Phase 2`
4. Share the output format with your team — confirm it's exactly what they expect before moving to integration

**Deliverable:** Clean risk-score output file + documented trigger threshold, ready to hand off.

---

# MEMBER 2 — Sabyasachi — Phase 2: Text Understanding

## Day 1 — Setup and understanding the data
**Problem this solves:** We need labeled disaster text data before building anything.

**Detailed steps:**
1. Download CrisisMMD (crisisnlp.qcri.org) and/or HumAID for more volume
2. Read the CrisisMMD paper (arxiv.org/abs/1805.00713) — note the informative/humanitarian-category/severity label structure
3. Confirm your dataset includes flood and hurricane/cyclone events specifically (CrisisMMD: Sri Lanka floods, Hurricanes Irma/Harvey/Maria — matches your two hazards)

**Deliverable:** Dataset downloaded, label structure documented.

---

## Day 2 — Reading the data programmatically
**Detailed steps:**
1. Load the dataset, inspect columns and label distribution
2. Check class balance — how many informative vs. non-informative posts, per hazard type
3. Filter to just flood- and cyclone-related posts if the dataset covers other hazards too

**Deliverable:** Working data-loading code, documented class distribution.

---

## Day 3 — Detection model (Step 1 of the pipeline)
**Concept to learn first:** Fine-tuning a small pretrained model (DistilBERT) on your labels is fast — a few hours on free Colab GPU, not training from zero.

**Detailed steps:**
1. Fine-tune DistilBERT on the informative/not-informative label
2. Evaluate with F1-score (not just accuracy)
3. Record the real number

**Deliverable:** Working detection model with documented F1-score.

---

## Day 4 — Extraction model (Step 2)
**Detailed steps:**
1. Run a pretrained NER pipeline (spaCy or HuggingFace) on detected posts — no training needed
2. Pull out location names and key severity terms
3. Spot-check 10-15 outputs manually — does the extraction look reasonable?

**Deliverable:** Working extraction code, manually verified on a sample.

---

## Day 5 — Same-event matching (Step 3)
**Concept to learn first:** SBERT gives you a pretrained sentence embedding — you compute cosine similarity directly, no training.

**Detailed steps:**
1. Load a pretrained SBERT model
2. Compute similarity scores between pairs of posts about the same known event
3. Pick a similarity threshold that reasonably separates "same event" from "different event" — test it on a few known pairs

**Deliverable:** Working similarity function with a documented, tested threshold.

---

## Day 6 — Event grouping (Step 4) + end-to-end test
**Detailed steps:**
1. Feed your similarity scores into HDBSCAN to cluster posts into distinct events
2. Run the full pipeline (detect → extract → match → group) on a batch of real flood/cyclone posts
3. Manually check: did it correctly separate two different real events, and correctly group duplicates of the same event?

**Deliverable:** Full text pipeline working end-to-end, tested on real flood/cyclone posts.

---

## Day 7 — Packaging outputs for fusion
**Detailed steps:**
1. Agree with Chandrakant on the exact output format he needs (event ID, location, confidence score, source count)
2. Convert your pipeline's output into that format
3. Generate a sample output file and confirm it loads correctly in his expected format

**Deliverable:** Clean, standardized event output file ready for fusion.

---

# MEMBER 3 — Chandrakant — Phase 2: Images + Fusion + Dashboard

## Day 1 — Setup and understanding image data
**Detailed steps:**
1. Download CrisisMMD (same dataset, image portion) — has informative/humanitarian-category/damage-severity labels for images
2. Read the CrisisMMD paper's image-task section
3. Set up the shared GitHub repo structure if not already done: `/phase1`, `/phase2_text`, `/phase2_image`, `/dashboard`, `/paper`

**Deliverable:** Image dataset downloaded, repo structure live.

---

## Day 2 — Reading images programmatically
**Detailed steps:**
1. Load a sample of CrisisMMD images and their labels
2. Check class distribution (damage severity is likely imbalanced — document it)
3. Visualize a few examples per class to understand what "damage" looks like in this dataset

**Deliverable:** Working image-loading code, documented class distribution.

---

## Day 3 — Image model (Step 5 of the pipeline)
**Concept to learn first:** ResNet-50 pretrained on millions of general images — you're fine-tuning its last layers, not training from scratch.

**Detailed steps:**
1. Load pretrained ResNet-50, fine-tune on CrisisMMD's damage/informative labels
2. Handle class imbalance if present (class weighting is the simplest fix)
3. Run initial training on Colab GPU

**Deliverable:** First-pass trained image classification model.

---

## Day 4 — Evaluating the image model
**Detailed steps:**
1. Evaluate with per-class F1-score, not just overall accuracy
2. Check which class the model struggles with most (usually the rarest one)
3. Document the real numbers, even if not perfect

**Deliverable:** Documented per-class F1 scores.

---

## Day 5 — Fusion + bridge logic
**Concept to learn first:** Fusion doesn't have to be a trained model — a simple weighted combination of text-confidence + image-confidence is a legitimate, honest design choice for this timeline.

**Detailed steps:**
1. Collect Sabyasachi's text-event output and your image-classification output
2. Write a simple fusion function: combine both into one confidence score per event
3. Implement the bridge: read Subhashree's risk-score file, trigger which regions' Phase 2 data gets shown
4. Test with a few sample events end-to-end

**Deliverable:** Working fusion function + bridge trigger, tested on sample data.

---

## Day 6 — Dashboard skeleton
**Concept to learn first:** Streamlit turns a Python script into a webpage — no separate frontend needed.

**Detailed steps:**
1. Build a basic Streamlit app with three sections: risk map, live event feed, severity ranking
2. Wire in Subhashree's risk-score output for the risk map section
3. Wire in your fused event output for the event feed section

**Deliverable:** Working dashboard skeleton showing both Phase 1 and Phase 2 outputs.

---

## Day 7 — Full integration and testing
**Detailed steps:**
1. Run the complete pipeline end-to-end: risk prediction → trigger → text pipeline → image pipeline → fusion → dashboard
2. Fix any format mismatches between team members' outputs
3. Take screenshots or record a short demo — you'll need this for the paper and presentation

**Deliverable:** Fully working, demoable end-to-end system.

---

# Shared — Days 8-10: Results and Paper

**Day 8:** Each person finalizes their real numbers (F1/accuracy for all three models). Write your own methodology section in past tense — what you did, not instructions.

**Day 9:** Combine into one paper: Abstract → Introduction (the flood/cyclone problem) → Related Work (cite CrisisMMD, HumAID, and be honest about what's already published) → Methodology (your three sections) → Results → Conclusion.

**Day 10:** Critical read of each other's sections — check every claim matches what was actually measured. Format references. Proofread.

---

# Later — Upgrading Toward Higher-Tier Venues

Once this core version works end-to-end with real results, you can decide as a team whether to push further: turn the fusion step (currently a simple weighted combination) into an actual trained model that learns how to weight text vs. image evidence, with a proper ablation study (text-only vs. image-only vs. fused, same test set, same metric). That upgrade is what would move this from "solid systems paper" toward the tier your senior's IRAI paper sits at — but get the core working and honest first, then decide if the extra work is worth it for your timeline.
