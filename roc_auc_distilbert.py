import os
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_curve,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

# ============================================================
# 1. Paths
# ============================================================

DATA_PATH = "data/tweets/tweets.csv"
MODEL_PATH = "models/misinformation_filter"

# ============================================================
# 2. Load dataset
# ============================================================

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)
print("Columns:", df.columns.tolist())

# Kaggle Disaster Tweets normally uses:
# text  -> tweet text
# target -> 0 or 1 label

df = df[["text", "target"]].dropna()

X = df["text"].astype(str)
y = df["target"].astype(int)

print("\nClass distribution:")
print(y.value_counts())

# ============================================================
# 3. Create TEST set
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# ============================================================
# 4. Load DistilBERT tokenizer and model
# ============================================================

print("\nLoading DistilBERT...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH
)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model.to(device)
model.eval()

print("Device:", device)

# ============================================================
# 5. Generate predictions
# ============================================================

texts = X_test.tolist()

all_probabilities = []
all_predictions = []

batch_size = 16

print("\nRunning inference...")

with torch.no_grad():

    for start in range(0, len(texts), batch_size):

        batch_texts = texts[start:start + batch_size]

        encoded = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        )

        encoded = {
            key: value.to(device)
            for key, value in encoded.items()
        }

        outputs = model(**encoded)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )

        predictions = torch.argmax(
            probabilities,
            dim=1
        )

        all_probabilities.extend(
            probabilities[:, 1].cpu().numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )

# Convert to numpy

y_true = np.array(y_test)
y_probability = np.array(all_probabilities)
y_pred = np.array(all_predictions)

# ============================================================
# 6. ROC-AUC
# ============================================================

fpr, tpr, thresholds = roc_curve(
    y_true,
    y_probability
)

roc_auc = roc_auc_score(
    y_true,
    y_probability
)

print("\n" + "=" * 50)
print("DISTILBERT ROC-AUC RESULT")
print("=" * 50)

print(f"ROC-AUC Score: {roc_auc:.4f}")

# ============================================================
# 7. Additional classification results
# ============================================================

print("\nClassification Report:")
print(
    classification_report(
        y_true,
        y_pred,
        digits=4
    )
)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_true,
        y_pred
    )
)

# ============================================================
# 8. Plot ROC Curve
# ============================================================

plt.figure(figsize=(8, 6))

plt.plot(
    fpr,
    tpr,
    linewidth=2,
    label=f"DistilBERT (AUC = {roc_auc:.4f})"
)

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    linewidth=1.5,
    label="Random Classifier"
)

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")

plt.title(
    "ROC Curve - DistilBERT Disaster Text Classification"
)

plt.legend(
    loc="lower right"
)

plt.grid(alpha=0.3)

plt.tight_layout()

# ============================================================
# 9. Save figure
# ============================================================

OUTPUT_PATH = "distilbert_roc_auc.png"

plt.savefig(
    OUTPUT_PATH,
    dpi=300,
    bbox_inches="tight"
)

print("\nROC curve saved to:")
print(os.path.abspath(OUTPUT_PATH))

plt.show()