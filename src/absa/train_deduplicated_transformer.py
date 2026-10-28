"""Train and evaluate DistilBERT on the same deduplicated ABSA split as baselines."""

import argparse
import json
import os
import random
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class TextDataset(Dataset):
    def __init__(self, frame, tokenizer, label2id, max_length):
        self.texts = frame["resolution_description"].astype(str).tolist()
        self.labels = frame["canonical_aspect"].map(label2id).astype(int).tolist()
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):
        encoded = self.tokenizer(
            self.texts[index],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "label": torch.tensor(self.labels[index], dtype=torch.long),
        }


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model, loader, device, labels):
    model.eval()
    predictions, targets = [], []
    losses = []
    with torch.no_grad():
        for batch in loader:
            output = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                labels=batch["label"].to(device),
            )
            losses.append(float(output.loss.item()))
            predictions.extend(output.logits.argmax(dim=1).cpu().numpy())
            targets.extend(batch["label"].numpy())
    return {
        "loss": float(np.mean(losses)),
        "accuracy": float(accuracy_score(targets, predictions)),
        "macro_f1": float(f1_score(targets, predictions, labels=labels, average="macro", zero_division=0)),
        "report": classification_report(targets, predictions, labels=labels, output_dict=True, zero_division=0),
    }


def main():
    parser = argparse.ArgumentParser(description="Train leakage-controlled DistilBERT ABSA model.")
    parser.add_argument("--input", default="data/processed/absa_deduplicated_split.parquet")
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--model-output", default="artifacts/models/bert_absa_dedup")
    parser.add_argument("--metrics-output", default="reports/metrics/transformer_metrics.json")
    parser.add_argument("--figure-output", default="reports/figures/training_loss_curve.png")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)
    frame = pd.read_parquet(args.input)
    aspects = sorted(frame["canonical_aspect"].unique().tolist())
    label2id = {label: index for index, label in enumerate(aspects)}
    id2label = {index: label for label, index in label2id.items()}
    train = frame[frame["split_year"] == 2023].reset_index(drop=True)
    val = frame[frame["split_year"] == 2024].reset_index(drop=True)
    test = frame[frame["split_year"] == 2025].reset_index(drop=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(aspects),
        id2label=id2label,
        label2id=label2id,
        local_files_only=True,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train_loader = DataLoader(TextDataset(train, tokenizer, label2id, args.max_length), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(TextDataset(val, tokenizer, label2id, args.max_length), batch_size=args.batch_size)
    test_loader = DataLoader(TextDataset(test, tokenizer, label2id, args.max_length), batch_size=args.batch_size)
    labels = list(range(len(aspects)))
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)
    label_counts = train["canonical_aspect"].map(label2id).value_counts().reindex(labels, fill_value=1)
    class_weights = len(train) / (len(labels) * label_counts.to_numpy(dtype=float))
    loss_function = torch.nn.CrossEntropyLoss(
        weight=torch.tensor(class_weights, dtype=torch.float32, device=device)
    )

    os.makedirs(args.model_output, exist_ok=True)
    history = {"train_loss": [], "val_loss": [], "val_accuracy": [], "val_macro_f1": []}
    best_val = -np.inf
    start = time.time()
    for epoch in range(args.epochs):
        model.train()
        losses = []
        for batch in train_loader:
            optimizer.zero_grad()
            output = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
            )
            loss = loss_function(output.logits, batch["label"].to(device))
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
        val_result = evaluate(model, val_loader, device, labels)
        history["train_loss"].append(float(np.mean(losses)))
        history["val_loss"].append(val_result["loss"])
        history["val_accuracy"].append(val_result["accuracy"])
        history["val_macro_f1"].append(val_result["macro_f1"])
        print(
            f"epoch={epoch + 1} train_loss={history['train_loss'][-1]:.4f} "
            f"val_loss={val_result['loss']:.4f} val_macro_f1={val_result['macro_f1']:.4f}"
        )
        if val_result["macro_f1"] > best_val:
            best_val = val_result["macro_f1"]
            model.save_pretrained(args.model_output)
            tokenizer.save_pretrained(args.model_output)

    best_model = AutoModelForSequenceClassification.from_pretrained(args.model_output, local_files_only=True).to(device)
    test_result = evaluate(best_model, test_loader, device, labels)
    per_class = {
        aspect: {
            "f1": float(test_result["report"].get(str(label2id[aspect]), {}).get("f1-score", 0.0)),
            "support": int(test_result["report"].get(str(label2id[aspect]), {}).get("support", 0)),
        }
        for aspect in aspects
    }
    # classification_report uses integer keys when labels are integers in
    # some sklearn versions and strings in others.
    for aspect, index in label2id.items():
        entry = test_result["report"].get(index, test_result["report"].get(str(index), {}))
        per_class[aspect] = {
            "f1": float(entry.get("f1-score", 0.0)),
            "support": int(entry.get("support", 0)),
        }

    metrics = {
        "status": "completed_local_common_deduplicated_split",
        "model_architecture": f"Transformer ({args.model_name})",
        "training_environment": str(device),
        "split_policy": "Same group-deduplicated 2023/2024/2025 split used by rule and TF-IDF baselines",
        "split_counts": {"train": len(train), "validation": len(val), "test": len(test)},
        "cross_split_normalized_text_overlap": 0,
        "hyperparameters": {
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "max_seq_length": args.max_length,
            "epochs": args.epochs,
            "seed": args.seed,
            "class_weighting": "inverse-frequency weights estimated from the 2023 training split",
            "training_time_minutes": round((time.time() - start) / 60, 2),
        },
        "evaluation_metrics_out_of_time": {
            "test_accuracy": round(test_result["accuracy"], 4),
            "test_macro_f1": round(test_result["macro_f1"], 4),
            "test_loss": round(test_result["loss"], 4),
        },
        "per_class": per_class,
        "training_history": history,
    }
    os.makedirs(os.path.dirname(args.metrics_output), exist_ok=True)
    with open(args.metrics_output, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    epochs = np.arange(1, len(history["train_loss"]) + 1)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(epochs, history["train_loss"], marker="o", label="Training loss")
    ax.plot(epochs, history["val_loss"], marker="s", label="Validation loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Cross-entropy loss")
    ax.set_title("DistilBERT training on duplicate-controlled ABSA split")
    ax.legend()
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.figure_output), exist_ok=True)
    fig.savefig(args.figure_output)
    plt.close(fig)
    print(f"Wrote transformer metrics to {args.metrics_output}")


if __name__ == "__main__":
    main()
