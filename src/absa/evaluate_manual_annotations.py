"""Evaluate human ABSA annotations and the domain-transfer classifier."""

import argparse
import json
import os
import sys

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, cohen_kappa_score, f1_score

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.absa.create_annotation_batch import ASPECTS
from src.absa.absa_pipeline import ASPECT_TAXONOMY_MAP


def require_complete(df: pd.DataFrame, columns):
    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Missing annotation column: {col}")
        if df[col].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"Column {col} contains blank labels; complete annotation before evaluation")
        invalid = set(df[col].dropna().astype(str)) - set(ASPECTS)
        if invalid:
            raise ValueError(f"Invalid labels in {col}: {sorted(invalid)}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate two annotators and ABSA on manual 311 labels.")
    parser.add_argument("--annotations", default="data/annotation/absa_annotation_batch.csv")
    parser.add_argument("--rsat", default="data/raw/rsat_raw.parquet")
    parser.add_argument("--output", default="reports/metrics/absa_manual_annotation_metrics.json")
    args = parser.parse_args()

    ann = pd.read_csv(args.annotations)
    require_complete(ann, ["annotator_1_label", "annotator_2_label", "adjudicated_label"])
    a1 = ann["annotator_1_label"].astype(str)
    a2 = ann["annotator_2_label"].astype(str)
    adjudicated = ann["adjudicated_label"].astype(str)

    rsat = pd.read_parquet(args.rsat)
    rsat["label"] = rsat["dissatisfaction_reason"].map(ASPECT_TAXONOMY_MAP)
    train = rsat[rsat["label"].notna() & rsat["resolution_description"].notna()].copy()
    train["text"] = train["resolution_description"].astype(str)
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    x_train = vectorizer.fit_transform(train["text"])
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    clf.fit(x_train, train["label"])
    predictions = clf.predict(vectorizer.transform(ann["text"].astype(str)))
    report = classification_report(adjudicated, predictions, labels=ASPECTS, output_dict=True, zero_division=0)

    output = {
        "task": "Human-annotated NYC 311 ABSA domain-transfer evaluation",
        "sample_count": int(len(ann)),
        "label_set": ASPECTS,
        "annotator_agreement": {
            "raw_agreement": float((a1 == a2).mean()),
            "cohen_kappa": float(cohen_kappa_score(a1, a2, labels=ASPECTS)),
        },
        "classifier_against_adjudicated_labels": {
            "accuracy": float(accuracy_score(adjudicated, predictions)),
            "macro_f1": float(f1_score(adjudicated, predictions, labels=ASPECTS, average="macro", zero_division=0)),
            "per_class": {label: report[label] for label in ASPECTS},
        },
        "interpretation": "Evaluation measures transfer from RSAT-linked resolution text to manually annotated 311 resolution narratives; it is not evaluation on unrestricted citizen comments.",
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote manual annotation metrics to {args.output}")


if __name__ == "__main__":
    main()
