"""
Phase 10: Transformer Fine-Tuning Script for Kaggle GPU (Tesla T4).
Fine-tunes DistilBERT / BERT on NYC 311 Resolution Texts & RSAT Aspect Grievances.
Evaluates chronologically: Train (2023), Validation (2024), Out-of-Time Test (2025).

Outputs generated in ./output_bundle:
1. bert_absa/ (HuggingFace saved weights and tokenizer)
2. transformer_metrics.json (Empirical out-of-time metrics & per-class F1)
3. training_loss_curve.png (Convergence loss & F1 curves)
4. kaggle_absa_bundle.zip (Single-click downloadable package)
"""

import os
import glob
import json
import time
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
from sklearn.metrics import classification_report, f1_score, accuracy_score

# ----------------- CONFIGURATION -----------------
MODEL_NAME = "distilbert-base-uncased"  # Fast, highly accurate, lightweight (~260MB)
BATCH_SIZE = 32
MAX_LEN = 128
EPOCHS = 3
LR = 2e-5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUTPUT_DIR = "output_bundle"
MODEL_SAVE_DIR = os.path.join(OUTPUT_DIR, "bert_absa")

print(f"[*] Training on device: {DEVICE}")
if torch.cuda.is_available():
    print(f"[*] GPU Model: {torch.cuda.get_device_name(0)}")

# ----------------- LOCATE DATASET -----------------
def find_dataset():
    candidates = [
        "/kaggle/input/**/kaggle_absa_sample.csv",
        "./kaggle_absa_sample.csv",
        "data/processed/kaggle_absa_sample.csv",
        "kaggle_absa_sample.csv"
    ]
    for pattern in candidates:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            print(f"[+] Found dataset at: {matches[0]}")
            return matches[0]
    raise FileNotFoundError("Could not locate kaggle_absa_sample.csv! Please upload it as input.")

DATA_PATH = find_dataset()
df = pd.read_csv(DATA_PATH)
print(f"[+] Loaded dataset shape: {df.shape}")

# ----------------- LABELS & SPLIT -----------------
ASPECTS = sorted(df["canonical_aspect"].unique().tolist())
label2id = {asp: i for i, asp in enumerate(ASPECTS)}
id2label = {i: asp for i, asp in enumerate(ASPECTS)}
df["label"] = df["canonical_aspect"].map(label2id)

train_df = df[df["year"] == 2023].reset_index(drop=True)
val_df = df[df["year"] == 2024].reset_index(drop=True)
test_df = df[df["year"] == 2025].reset_index(drop=True)

print(f"[+] Chronological Partitions:")
print(f"    Train (2023): {len(train_df):,} samples")
print(f"    Val   (2024): {len(val_df):,} samples")
print(f"    Test  (2025): {len(test_df):,} samples (Out-of-Time)")

# ----------------- DATASET CLASS -----------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class CivicDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long)
        }

train_ds = CivicDataset(train_df["resolution_description"].tolist(), train_df["label"].tolist(), tokenizer, MAX_LEN)
val_ds = CivicDataset(val_df["resolution_description"].tolist(), val_df["label"].tolist(), tokenizer, MAX_LEN)
test_ds = CivicDataset(test_df["resolution_description"].tolist(), test_df["label"].tolist(), tokenizer, MAX_LEN)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

# ----------------- MODEL SETUP -----------------
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(ASPECTS),
    id2label=id2label,
    label2id=label2id
)
model.to(DEVICE)

optimizer = AdamW(model.parameters(), lr=LR, weight_decay=0.01)
total_steps = len(train_loader) * EPOCHS
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)

# ----------------- TRAINING LOOP -----------------
history = {"train_loss": [], "val_loss": [], "val_acc": [], "val_macro_f1": []}
best_val_f1 = -1.0
os.makedirs(MODEL_SAVE_DIR, exist_ok=True)

scaler = torch.cuda.amp.GradScaler() if torch.cuda.is_available() else None

print("\n[*] Starting Fine-Tuning across 3 Epochs...")
start_time = time.time()

for epoch in range(1, EPOCHS + 1):
    model.train()
    total_train_loss = 0.0

    for step, batch in enumerate(train_loader):
        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["label"].to(DEVICE)

        optimizer.zero_grad()

        if scaler:
            with torch.cuda.amp.autocast():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

        scheduler.step()
        total_train_loss += loss.item()

        if (step + 1) % 100 == 0 or (step + 1) == len(train_loader):
            print(f"  Epoch {epoch}/{EPOCHS} | Step {step+1}/{len(train_loader)} | Loss: {loss.item():.4f}")

    avg_train_loss = total_train_loss / len(train_loader)

    # Validation
    model.eval()
    total_val_loss = 0.0
    val_preds, val_targets = [], []

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["label"].to(DEVICE)

            if scaler:
                with torch.cuda.amp.autocast():
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            else:
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

            total_val_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
            val_preds.extend(preds)
            val_targets.extend(labels.cpu().numpy())

    avg_val_loss = total_val_loss / len(val_loader)
    val_acc = accuracy_score(val_targets, val_preds)
    val_macro_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0)

    history["train_loss"].append(round(avg_train_loss, 4))
    history["val_loss"].append(round(avg_val_loss, 4))
    history["val_acc"].append(round(val_acc, 4))
    history["val_macro_f1"].append(round(val_macro_f1, 4))

    print(f"[+] Epoch {epoch} Complete: Train Loss={avg_train_loss:.4f} | Val Loss={avg_val_loss:.4f} | Val Acc={val_acc:.4f} | Val Macro-F1={val_macro_f1:.4f}")

    # Save Best Model Checkpoint
    if val_macro_f1 > best_val_f1:
        best_val_f1 = val_macro_f1
        model.save_pretrained(MODEL_SAVE_DIR)
        tokenizer.save_pretrained(MODEL_SAVE_DIR)
        print(f"    --> Saved best model checkpoint (Val Macro-F1: {val_macro_f1:.4f})")

elapsed = time.time() - start_time
print(f"\n[*] Fine-Tuning Completed in {elapsed/60:.2f} minutes.")

# ----------------- OUT-OF-TIME TEST EVALUATION -----------------
print("\n[*] Evaluating Best Checkpoint on 2025 Out-of-Time Test Set...")
best_model = AutoModelForSequenceClassification.from_pretrained(MODEL_SAVE_DIR)
best_model.to(DEVICE)
best_model.eval()

test_preds, test_targets = [], []
total_test_loss = 0.0

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["label"].to(DEVICE)

        if scaler:
            with torch.cuda.amp.autocast():
                outputs = best_model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        else:
            outputs = best_model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

        total_test_loss += outputs.loss.item()
        preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
        test_preds.extend(preds)
        test_targets.extend(labels.cpu().numpy())

avg_test_loss = total_test_loss / len(test_loader)
test_acc = accuracy_score(test_targets, test_preds)
test_macro_f1 = f1_score(test_targets, test_preds, average="macro", zero_division=0)
report = classification_report(test_targets, test_preds, target_names=ASPECTS, output_dict=True, zero_division=0)

per_class_f1 = {asp: round(float(report[asp]["f1-score"]), 4) for asp in ASPECTS}
tfidf_baseline_f1 = 0.1723  # Phase 6 baseline
delta_f1 = round(float(test_macro_f1 - tfidf_baseline_f1), 4)

print("\n" + "="*50)
print(f"OUT-OF-TIME (2025) TEST RESULTS:")
print(f"  Test Accuracy: {test_acc:.4f}")
print(f"  Test Macro-F1: {test_macro_f1:.4f}  (Gain over TF-IDF: +{delta_f1:.4f})")
print(f"  Per-Aspect F1 Breakdown:")
for k, v in per_class_f1.items():
    print(f"    - {k}: {v:.4f}")
print("="*50)

# ----------------- SAVE METRICS JSON -----------------
metrics_data = {
    "status": "completed_kaggle_gpu_empirical_run",
    "model_architecture": f"Transformer ({MODEL_NAME})",
    "fine_tuning_corpus": "NYC 311 Resolution Narratives & RSAT Grievances (2023-2025)",
    "training_environment": f"Kaggle GPU ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})",
    "hyperparameters": {
        "learning_rate": LR,
        "batch_size": BATCH_SIZE,
        "max_seq_length": MAX_LEN,
        "optimizer": "AdamW",
        "weight_decay": 0.01,
        "epochs": EPOCHS,
        "training_time_minutes": round(elapsed / 60, 2)
    },
    "evaluation_metrics_out_of_time": {
        "test_accuracy": round(float(test_acc), 4),
        "test_macro_f1": round(float(test_macro_f1), 4),
        "test_loss": round(float(avg_test_loss), 4)
    },
    "per_class_f1": per_class_f1,
    "delta_f1_vs_tfidf_baseline": delta_f1,
    "training_history": history
}

metrics_path = os.path.join(OUTPUT_DIR, "transformer_metrics.json")
with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics_data, f, indent=2)
print(f"[+] Saved metrics JSON to: {metrics_path}")

# ----------------- PLOT TRAINING LOSS CURVE -----------------
epochs_range = range(1, EPOCHS + 1)
fig, ax1 = plt.subplots(figsize=(8, 5), dpi=150)
color = "#e74c3c"
ax1.set_xlabel("Epoch", fontsize=11, labelpad=8)
ax1.set_ylabel("Cross-Entropy Loss", color=color, fontsize=11, labelpad=8)
ax1.plot(epochs_range, history["train_loss"], "o-", color=color, linewidth=2, label="Train Loss")
ax1.plot(epochs_range, history["val_loss"], "s--", color="#c0392b", linewidth=2, label="Val Loss")
ax1.tick_params(axis="y", labelcolor=color)

ax2 = ax1.twinx()
color = "#2980b9"
ax2.set_ylabel("Validation Macro-F1", color=color, fontsize=11, labelpad=8)
ax2.plot(epochs_range, history["val_macro_f1"], "^-", color=color, linewidth=2, label="Val Macro-F1")
ax2.tick_params(axis="y", labelcolor=color)

plt.title(f"{MODEL_NAME} Civic Fine-Tuning Convergence (Kaggle GPU)", fontsize=12, fontweight="bold", pad=12)
fig.tight_layout()
curve_path = os.path.join(OUTPUT_DIR, "training_loss_curve.png")
plt.savefig(curve_path, dpi=150)
plt.close()
print(f"[+] Saved convergence curves to: {curve_path}")

# ----------------- CREATE DOWNLOADABLE ZIP BUNDLE -----------------
zip_path = "kaggle_absa_bundle"
shutil.make_archive(zip_path, "zip", OUTPUT_DIR)
print(f"\n[SUCCESS] Downloadable package created at: {zip_path}.zip")
print(f"[*] Package size: {os.path.getsize(zip_path + '.zip') / (1024*1024):.2f} MB")
print("[*] Ready for single-click download from Kaggle output!")
