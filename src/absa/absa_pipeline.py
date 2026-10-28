"""
Phase 6: Aspect-Based Sentiment Analysis (ABSA) Pipeline.
Implements Rule-Based Baseline (Option A) and Supervised TF-IDF Classifier (Option B)
to predict dissatisfaction aspects from municipal closure texts.
Evaluates using chronological splits and produces cell-level aspect grievance features.
Satisfies VIT Review-2 criteria C3, C4, and C5.
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
import re

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, accuracy_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Standardized 6-class canonical aspect taxonomy mapped from the 8 raw RSAT strings
ASPECT_TAXONOMY_MAP = {
    "The Agency did not correct the issue.": "Issue Correction",
    "The Agency did not correct the issue and this Service Request should be reopened.": "Issue Correction",
    "The Agency corrected the issue, but they took too long to respond.": "Response Time",
    "Status updates were unhelpful, inaccurate, incomplete, and/or confusing.": "Status Updates",
    "The Agency did not provide enough status updates.": "Status Updates",
    "The Agency corrected the issue, but the work they did was unsatisfactory.": "Work Quality",
    "The Agency said I did not provide complete or accurate information, but I did.": "Information Intake",
    "Other": "Other",
}

RULE_KEYWORDS = {
    "Response Time": ["time", "delay", "slow", "took too long", "late", "hours", "days", "weeks", "months", "waited", "prolonged"],
    "Status Updates": ["status", "update", "confusing", "unhelpful", "inaccurate", "communication", "notified", "notification", "misleading"],
    "Work Quality": ["unsatisfactory", "poor", "bad", "quality", "workmanship", "shoddy", "incomplete", "substandard", "improper"],
    "Information Intake": ["accurate information", "complete information", "intake", "details", "wrong address", "information provided"],
    "Issue Correction": ["not fixed", "not corrected", "did not fix", "unresolved", "persists", "still broken", "again", "remains"],
}


def load_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def rule_based_absa_predict(text: str) -> str:
    """Assigns aspect category based on domain lexicon matching."""
    text_lower = str(text).lower()
    for aspect, kws in RULE_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            return aspect
    return "Issue Correction"  # dominant empirical mode fallback


def normalize_resolution_text(text: str) -> str:
    """Normalize agency boilerplate for duplicate-group leakage control."""
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def build_group_deduplicated_split(df_rsat: pd.DataFrame):
    """Build a chronological split with no resolution text shared across years.

    A normalized agency description is assigned to the first year in which it
    appears.  Within that year, one row is kept for each distinct
    (description, aspect) pair.  This retains genuine label ambiguity while
    preventing repeated boilerplate from appearing in multiple partitions.
    """
    prepared = df_rsat.copy()
    prepared["canonical_aspect"] = prepared["dissatisfaction_reason"].map(ASPECT_TAXONOMY_MAP)
    prepared = prepared[
        prepared["canonical_aspect"].notna()
        & prepared["resolution_description"].notna()
        & (prepared["resolution_description"].str.len() > 10)
    ].copy()
    prepared["normalized_description"] = prepared["resolution_description"].map(normalize_resolution_text)

    first_year = prepared.groupby("normalized_description")["year"].min()
    prepared["split_year"] = prepared["normalized_description"].map(first_year).astype(int)
    # Keep labels that were actually observed when the text group first
    # appeared.  Without this filter, a new 2025 label attached to boilerplate
    # first seen in 2023 would be moved backwards into the training set.
    first_year_rows = prepared[prepared["year"].astype(int) == prepared["split_year"]].copy()
    deduplicated = (
        first_year_rows.sort_values(["split_year", "normalized_description", "canonical_aspect", "unique_key"])
        .drop_duplicates(["normalized_description", "canonical_aspect"], keep="first")
        .reset_index(drop=True)
    )

    split_sets = {
        int(year): set(group["normalized_description"])
        for year, group in deduplicated.groupby("split_year")
    }
    overlap_counts = {}
    years = sorted(split_sets)
    for i, left in enumerate(years):
        for right in years[i + 1:]:
            overlap_counts[f"{left}_{right}"] = len(split_sets[left] & split_sets[right])

    ambiguity = prepared.groupby("normalized_description")["canonical_aspect"].nunique()
    audit = {
        "raw_labelled_rows": int(len(prepared)),
        "first_year_rows_before_pair_deduplication": int(len(first_year_rows)),
        "unique_normalized_descriptions": int(prepared["normalized_description"].nunique()),
        "unique_text_label_pairs": int(len(deduplicated)),
        "descriptions_with_multiple_aspect_labels": int((ambiguity > 1).sum()),
        "split_counts": {
            str(year): int(count)
            for year, count in deduplicated["split_year"].value_counts().sort_index().items()
        },
        "cross_split_text_overlap_counts": overlap_counts,
        "policy": "Each normalized description belongs only to its earliest observed year; only labels observed in that first year are eligible, then one row per description-aspect pair is retained.",
    }
    return deduplicated, audit


def plot_absa_comparison(per_aspect_results: dict, out_path: str):
    """Generates publication-quality comparison of per-aspect F1 scores."""
    aspects = list(per_aspect_results.keys())
    rule_f1 = [per_aspect_results[a]["rule_f1"] for a in aspects]
    clf_f1 = [per_aspect_results[a]["classifier_f1"] for a in aspects]

    x = np.arange(len(aspects))
    width = 0.35

    plt.figure(figsize=(10, 6), dpi=150)
    plt.bar(x - width/2, rule_f1, width, label="Rule-Based Baseline (Option A)", color="#95a5a6")
    plt.bar(x + width/2, clf_f1, width, label="TF-IDF + Logistic Regression (Option B)", color="#2980b9")

    plt.ylabel("F1-Score (Out-of-Time 2025 Test Set)", fontsize=11, labelpad=10)
    plt.title("Per-Aspect Performance: Rule-Based Baseline vs. Supervised Classifier", fontsize=13, fontweight="bold", pad=15)
    plt.xticks(x, aspects, rotation=15, ha="right", fontsize=10)
    plt.ylim(0, 1.05)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    logger.info(f"Saved ABSA evaluation figure to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Run ABSA pipeline for Smart Cities project.")
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

    rsat_path = os.path.join(raw_dir, "rsat_raw.parquet")
    nyc311_path = os.path.join(raw_dir, "nyc311_raw.parquet")

    logger.info("Loading RSAT and NYC 311 datasets...")
    df_rsat = pd.read_parquet(rsat_path)
    df_311 = pd.read_parquet(nyc311_path)

    # 1. Prepare a leakage-controlled supervised dataset from RSAT rows.
    labeled_data, dedup_audit = build_group_deduplicated_split(df_rsat)
    labeled_data.to_parquet(os.path.join(proc_dir, "absa_deduplicated_split.parquet"), index=False)

    logger.warning(
        "ABSA supervision uses RSAT-linked resolution_description because citizen free-text is suppressed; "
        "interpret results as domain transfer to 311 narratives, not direct citizen-comment classification."
    )

    logger.info(
        "ABSA audit: %s raw labelled rows -> %s unique text-label pairs across %s descriptions",
        f"{dedup_audit['raw_labelled_rows']:,}",
        f"{len(labeled_data):,}",
        f"{dedup_audit['unique_normalized_descriptions']:,}",
    )

    # 2. Chronological Split (Train: 2023, Val: 2024, Test: 2025)
    train_mask = labeled_data["split_year"] == 2023
    val_mask = labeled_data["split_year"] == 2024
    test_mask = labeled_data["split_year"] == 2025

    train_df = labeled_data[train_mask]
    val_df = labeled_data[val_mask]
    test_df = labeled_data[test_mask]

    logger.info(f"Chronological split sizes -> Train (2023): {len(train_df):,}, Val (2024): {len(val_df):,}, Test (2025): {len(test_df):,}")

    # 3. Option A: Rule-Based Baseline Evaluation
    logger.info("Evaluating Rule-Based Baseline (Option A) on 2025 test split...")
    y_test = test_df["canonical_aspect"]
    y_pred_rule = [rule_based_absa_predict(t) for t in test_df["resolution_description"]]

    target_names = sorted(list(set(labeled_data["canonical_aspect"].unique())))
    rule_report = classification_report(y_test, y_pred_rule, labels=target_names, output_dict=True, zero_division=0)
    rule_macro_f1 = f1_score(y_test, y_pred_rule, labels=target_names, average="macro", zero_division=0)
    rule_acc = accuracy_score(y_test, y_pred_rule)

    # 4. Option B: TF-IDF + Logistic Regression Classifier
    logger.info("Training TF-IDF + Logistic Regression Classifier (Option B)...")
    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    X_train = tfidf.fit_transform(train_df["resolution_description"])
    y_train = train_df["canonical_aspect"]

    X_test = tfidf.transform(test_df["resolution_description"])

    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    clf.fit(X_train, y_train)

    y_pred_clf = clf.predict(X_test)
    clf_report = classification_report(y_test, y_pred_clf, labels=target_names, output_dict=True, zero_division=0)
    clf_macro_f1 = f1_score(y_test, y_pred_clf, labels=target_names, average="macro", zero_division=0)
    clf_acc = accuracy_score(y_test, y_pred_clf)

    logger.info(f"Rule Baseline Test Macro-F1: {rule_macro_f1:.4f} | Classifier Test Macro-F1: {clf_macro_f1:.4f}")

    # 5. Extract Per-Aspect Metrics
    per_aspect = {}
    for asp in target_names:
        per_aspect[asp] = {
            "rule_f1": round(float(rule_report.get(asp, {}).get("f1-score", 0.0)), 4),
            "classifier_f1": round(float(clf_report.get(asp, {}).get("f1-score", 0.0)), 4),
            "support": int(clf_report.get(asp, {}).get("support", 0)),
        }

    metrics_output = {
        "task": "Aspect-Based Sentiment Analysis (ABSA) Grievance Attribution",
        "taxonomy": target_names,
        "evaluation_split": "Out-of-Time Test Set (2025)",
        "test_sample_count": int(len(test_df)),
        "duplicate_control": dedup_audit,
        "common_test_definition": "All ABSA models are evaluated on the same deduplicated 2025 text-group test split.",
        "models": {
            "rule_based_baseline": {
                "accuracy": round(float(rule_acc), 4),
                "macro_f1": round(float(rule_macro_f1), 4),
            },
            "tfidf_logistic_regression": {
                "accuracy": round(float(clf_acc), 4),
                "macro_f1": round(float(clf_macro_f1), 4),
                "delta_f1_vs_baseline": round(float(clf_macro_f1 - rule_macro_f1), 4),
            },
        },
        "per_aspect_breakdown": per_aspect,
    }

    metrics_path = os.path.join(metrics_dir, "absa_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2)
    logger.info(f"Saved ABSA metrics to {metrics_path}")

    # Plot Comparison
    fig_path = os.path.join(fig_dir, "absa_per_aspect_f1.png")
    plot_absa_comparison(per_aspect, fig_path)

    # 6. Predict Aspect Rates per Cell for Aggregate Integration
    logger.info("Computing cell-level aspect grievance proportions on NYC 311...")
    df_311["resolution_text_clean"] = df_311["resolution_description"].fillna("").astype(str)
    
    # Score each distinct agency narrative once.  The source contains large
    # volumes of repeated closure boilerplate, so transforming every row
    # separately wastes memory without changing any prediction.
    unique_311_text = pd.Series(df_311["resolution_text_clean"].unique())
    unique_predictions = clf.predict(tfidf.transform(unique_311_text))
    text_to_aspect = dict(zip(unique_311_text, unique_predictions))
    df_311["pred_aspect"] = df_311["resolution_text_clean"].map(text_to_aspect)

    df_311["complaint_type_upper"] = df_311["complaint_type"].str.upper()
    created_dt = pd.to_datetime(df_311["created_date"], errors="coerce")
    df_311["year"] = created_dt.dt.year
    df_311["month"] = created_dt.dt.month

    # Generate one-hot columns for canonical aspects
    for asp in target_names:
        df_311[f"is_aspect_{asp.lower().replace(' ', '_')}"] = (df_311["pred_aspect"] == asp).astype(int)

    agg_dict = {f"is_aspect_{asp.lower().replace(' ', '_')}": "mean" for asp in target_names}
    cell_absa = df_311.groupby(["complaint_type_upper", "borough", "year", "month"]).agg(agg_dict).reset_index()

    out_cell_absa = os.path.join(proc_dir, "cell_absa_features.parquet")
    cell_absa.to_parquet(out_cell_absa, index=False)
    logger.info(f"Saved cell-level ABSA features to {out_cell_absa} ({len(cell_absa):,} cells)")

    logger.info("Phase 6 ABSA Pipeline completed successfully!")


if __name__ == "__main__":
    main()
