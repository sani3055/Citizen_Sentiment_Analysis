"""Build a transparent summary of the available automatic ABSA evaluations."""

import argparse
import json
import os

import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Summarize automatic ABSA evaluation evidence.")
    parser.add_argument("--absa", default="reports/metrics/absa_metrics.json")
    parser.add_argument("--transformer", default="reports/metrics/transformer_metrics.json")
    parser.add_argument("--output", default="reports/metrics/absa_evaluation_summary.json")
    parser.add_argument("--figure", default="reports/figures/absa_per_aspect_f1.png")
    args = parser.parse_args()

    with open(args.absa, "r", encoding="utf-8") as f:
        absa = json.load(f)
    with open(args.transformer, "r", encoding="utf-8") as f:
        transformer = json.load(f)

    transformer_macro = transformer.get("evaluation_metrics_out_of_time", {}).get("test_macro_f1")
    tfidf_macro = absa.get("models", {}).get("tfidf_logistic_regression", {}).get("macro_f1")
    summary = {
        "evaluation_type": "automatic_ground_truth_and_domain_transfer",
        "human_annotation_completed": False,
        "human_annotation_metrics_reported": False,
        "primary_automatic_evaluation": {
            "ground_truth": "RSAT dissatisfaction_reason mapped to six canonical aspects",
            "text_source": "RSAT-linked resolution_description",
            "split": absa.get("evaluation_split"),
            "sample_count": absa.get("test_sample_count"),
            "rule_based_baseline": absa.get("models", {}).get("rule_based_baseline"),
            "tfidf_classifier": absa.get("models", {}).get("tfidf_logistic_regression"),
        },
        "transformer_evaluation": {
            "model": transformer.get("model_architecture"),
            "split": "The same group-deduplicated 2025 split used by the rule and TF-IDF models",
            "metrics": transformer.get("evaluation_metrics_out_of_time"),
            "macro_f1": transformer_macro,
            "delta_macro_f1_vs_tfidf_on_same_split": round(transformer_macro - tfidf_macro, 4),
        },
        "duplicate_control": absa.get("duplicate_control"),
        "transfer_boundary": "311 resolution narratives are evaluated as a transfer target, not as unrestricted citizen commentary.",
        "manual_annotation_status": "Future work; no synthetic human labels are used.",
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    per_aspect = absa.get("per_aspect_breakdown", {})
    transformer_per_class = transformer.get("per_class", {})
    aspects = list(per_aspect)
    x = np.arange(len(aspects))
    width = 0.26
    fig, ax = plt.subplots(figsize=(11, 6), dpi=150)
    ax.bar(x - width, [per_aspect[a]["rule_f1"] for a in aspects], width, label="Rule baseline")
    ax.bar(x, [per_aspect[a]["classifier_f1"] for a in aspects], width, label="TF-IDF")
    ax.bar(x + width, [transformer_per_class.get(a, {}).get("f1", 0.0) for a in aspects], width, label="DistilBERT")
    ax.set_ylabel("F1 score")
    ax.set_title("ABSA comparison on one duplicate-controlled test split")
    ax.set_xticks(x)
    ax.set_xticklabels(aspects, rotation=18, ha="right")
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.figure), exist_ok=True)
    fig.savefig(args.figure)
    plt.close(fig)
    print(f"Wrote automatic ABSA evaluation summary to {args.output}")


if __name__ == "__main__":
    main()
