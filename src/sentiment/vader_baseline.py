"""
Phase 4: VADER Sentiment Baseline Module.
Applies NLTK VADER to NYC 311 agency resolution descriptions,
aggregates polarity features to the municipal service cell level,
and evaluates classification agreement against RSAT citizen ground truth.
Satisfies VIT Review-2 criteria C3 and C4.
"""

import os
import sys
import json
import argparse
import logging
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def map_vader_label(compound_score: float, pos_thresh: float = 0.05, neg_thresh: float = -0.05) -> str:
    if compound_score >= pos_thresh:
        return "Positive"
    elif compound_score <= neg_thresh:
        return "Negative"
    return "Neutral"


def plot_confusion_matrix(y_true, y_pred, labels, out_path: str):
    """Generates and saves publication confusion matrix."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=(7, 6), dpi=150)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.title("VADER Baseline Confusion Matrix (Cell-Level Ground Truth)", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Predicted Sentiment Label (Agency Narrative)", fontsize=10)
    plt.ylabel("Ground-Truth Sentiment Label (RSAT Survey)", fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    logger.info(f"Saved confusion matrix figure to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Run VADER baseline for Smart Cities project.")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    raw_dir = config["data"]["raw_dir"]
    proc_dir = config["data"]["processed_dir"]
    metrics_dir = "reports/metrics"
    fig_dir = "reports/figures"

    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    pos_thresh = config["nlp"]["models"]["vader"].get("pos_threshold", 0.05)
    neg_thresh = config["nlp"]["models"]["vader"].get("neg_threshold", -0.05)
    min_cell_samples = config["data"].get("min_cell_samples", 10)

    # 1. Load Datasets
    rsat_path = os.path.join(raw_dir, "rsat_raw.parquet")
    nyc311_path = os.path.join(raw_dir, "nyc311_raw.parquet")
    logger.info(f"Loading raw datasets: {rsat_path} and {nyc311_path}")
    df_rsat = pd.read_parquet(rsat_path)
    df_311 = pd.read_parquet(nyc311_path)

    # 2. Score NYC 311 Resolution Descriptions with VADER
    logger.info("Initializing NLTK VADER SentimentIntensityAnalyzer...")
    sia = SentimentIntensityAnalyzer()

    # Pre-extract unique text strings and compute VADER instantaneously
    logger.info("Computing VADER polarity scores across unique resolution narratives...")
    unique_texts = df_311["resolution_description"].fillna("").astype(str).unique()
    text_to_score = {t: (sia.polarity_scores(t)["compound"] if t.strip() else 0.0) for t in unique_texts}
    text_to_label = {t: map_vader_label(sc, pos_thresh, neg_thresh) for t, sc in text_to_score.items()}
    
    clean_series = df_311["resolution_description"].fillna("").astype(str)
    df_311["vader_compound"] = clean_series.map(text_to_score)
    df_311["vader_label"] = clean_series.map(text_to_label)

    # Save processed NYC 311 with VADER features
    out_311_vader = os.path.join(proc_dir, "nyc311_with_vader.parquet")
    df_311.to_parquet(out_311_vader, index=False)
    logger.info(f"Saved NYC 311 with VADER features to {out_311_vader} ({len(df_311):,} records)")

    # 3. Aggregate VADER features to Cell Level
    logger.info("Aggregating VADER features to (complaint_type, borough, year, month) cells...")
    df_311["complaint_type_upper"] = df_311["complaint_type"].str.upper()
    df_311["created_dt"] = pd.to_datetime(df_311["created_date"], errors="coerce")
    df_311["year"] = df_311["created_dt"].dt.year
    df_311["month"] = df_311["created_dt"].dt.month

    # Cell aggregations
    df_311["is_vader_pos"] = (df_311["vader_label"] == "Positive").astype(int)
    df_311["is_vader_neg"] = (df_311["vader_label"] == "Negative").astype(int)
    df_311["is_vader_neu"] = (df_311["vader_label"] == "Neutral").astype(int)

    cell_vader = df_311.groupby(["complaint_type_upper", "borough", "year", "month"]).agg(
        mean_vader_score=("vader_compound", "mean"),
        std_vader_score=("vader_compound", "std"),
        vader_pos_rate=("is_vader_pos", "mean"),
        vader_neg_rate=("is_vader_neg", "mean"),
        vader_neu_rate=("is_vader_neu", "mean"),
        n_311_requests=("unique_key", "count"),
    ).reset_index()

    cell_vader["std_vader_score"] = cell_vader["std_vader_score"].fillna(0.0)

    # Determine cell majority VADER label
    def get_cell_pred_label(row):
        if row["mean_vader_score"] >= pos_thresh:
            return "Positive"
        elif row["mean_vader_score"] <= neg_thresh:
            return "Negative"
        return "Neutral"

    cell_vader["vader_cell_pred"] = cell_vader.apply(get_cell_pred_label, axis=1)

    out_cell_vader = os.path.join(proc_dir, "cell_vader_features.parquet")
    cell_vader.to_parquet(out_cell_vader, index=False)
    logger.info(f"Saved cell-level VADER features to {out_cell_vader} ({len(cell_vader):,} cells)")

    # 4. Evaluation against RSAT Ground Truth
    logger.info("Computing cell-level classification evaluation against RSAT ground truth...")
    df_rsat["complaint_type_upper"] = df_rsat["complaint_type"].str.upper()
    df_rsat["sentiment_label"] = df_rsat["overall_satisfaction"].map({
        "Strongly Agree": "Positive",
        "Agree": "Positive",
        "Neutral": "Neutral",
        "Disagree": "Negative",
        "Strongly Disagree": "Negative",
    })

    # RSAT cell majority and sentiment rates
    df_rsat["is_rsat_neg"] = (df_rsat["sentiment_label"] == "Negative").astype(int)
    df_rsat["is_rsat_pos"] = (df_rsat["sentiment_label"] == "Positive").astype(int)
    df_rsat["is_rsat_neu"] = (df_rsat["sentiment_label"] == "Neutral").astype(int)

    cell_rsat = df_rsat.groupby(["complaint_type_upper", "borough", "year", "month"]).agg(
        n_rsat_responses=("unique_key", "count"),
        rsat_neg_rate=("is_rsat_neg", "mean"),
        rsat_pos_rate=("is_rsat_pos", "mean"),
        rsat_neu_rate=("is_rsat_neu", "mean"),
    ).reset_index()

    # Filter cells with sufficient sample size
    cell_rsat_filtered = cell_rsat[cell_rsat["n_rsat_responses"] >= min_cell_samples].copy()

    def get_rsat_majority(row):
        rates = {"Negative": row["rsat_neg_rate"], "Positive": row["rsat_pos_rate"], "Neutral": row["rsat_neu_rate"]}
        return max(rates, key=rates.get)

    cell_rsat_filtered["rsat_ground_truth"] = cell_rsat_filtered.apply(get_rsat_majority, axis=1)

    # Merge on cell keys
    merged = pd.merge(
        cell_vader,
        cell_rsat_filtered[["complaint_type_upper", "borough", "year", "month", "n_rsat_responses", "rsat_ground_truth", "rsat_neg_rate"]],
        on=["complaint_type_upper", "borough", "year", "month"],
        how="inner",
    )
    logger.info(f"Matched {len(merged):,} robust cells between VADER and RSAT")

    labels = ["Negative", "Neutral", "Positive"]
    y_true = merged["rsat_ground_truth"]
    y_pred = merged["vader_cell_pred"]

    report_dict = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)

    metrics_output = {
        "model": "VADER Lexicon Baseline",
        "evaluation_grain": "Cell-level (Service × Borough × Year × Month)",
        "number_of_matched_cells": int(len(merged)),
        "min_cell_samples_threshold": min_cell_samples,
        "overall_accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "per_class": {
            "Negative": {
                "precision": round(float(report_dict["Negative"]["precision"]), 4),
                "recall": round(float(report_dict["Negative"]["recall"]), 4),
                "f1_score": round(float(report_dict["Negative"]["f1-score"]), 4),
                "support": int(report_dict["Negative"]["support"]),
            },
            "Neutral": {
                "precision": round(float(report_dict["Neutral"]["precision"]), 4),
                "recall": round(float(report_dict["Neutral"]["recall"]), 4),
                "f1_score": round(float(report_dict["Neutral"]["f1-score"]), 4),
                "support": int(report_dict["Neutral"]["support"]),
            },
            "Positive": {
                "precision": round(float(report_dict["Positive"]["precision"]), 4),
                "recall": round(float(report_dict["Positive"]["recall"]), 4),
                "f1_score": round(float(report_dict["Positive"]["f1-score"]), 4),
                "support": int(report_dict["Positive"]["support"]),
            },
        },
        "methodological_limitation": (
            "VADER operates on agency closure narratives (NYC 311 resolution_description). "
            "Evaluated against citizen RSAT overall_satisfaction survey ground truth. "
            "Serves as an operational feature extractor and baseline benchmark."
        ),
    }

    metrics_path = os.path.join(metrics_dir, "vader_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2)
    logger.info(f"Saved VADER evaluation metrics to {metrics_path}")

    # Plot Confusion Matrix
    cm_path = os.path.join(fig_dir, "vader_confusion_matrix.png")
    plot_confusion_matrix(y_true, y_pred, labels, cm_path)

    logger.info("Phase 4 VADER Baseline completed successfully!")


if __name__ == "__main__":
    main()
