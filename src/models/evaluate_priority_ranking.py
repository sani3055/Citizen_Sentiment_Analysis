"""Evaluate the dashboard's one-month-ahead priority ranking on held-out cells."""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import ndcg_score

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.train_predictive import prepare_features, make_lightgbm


TARGETS = ["mean_resolution_delay_hours", "repeat_request_rate_14d"]


def precision_at_k(predicted_order, relevant_indices, k):
    if k < 1 or k > len(predicted_order):
        raise ValueError("k must be between 1 and the number of ranked cells")
    selected = set(predicted_order[:k])
    return len(selected & set(relevant_indices)) / k


def empirical_percentiles(reference, values):
    """Percentile scores relative to a frozen training distribution."""
    reference = np.sort(np.asarray(reference, dtype=float))
    if not len(reference) or not np.isfinite(reference).all():
        raise ValueError("Reference must be nonempty and finite")
    return np.searchsorted(reference, values, side="right") / len(reference)


def fixed_threshold_relevance(training, test, quantile=0.80):
    """Fit a burden cutoff using training outcomes only, then freeze it.

    Unlike top-k overlap, neither the score transform nor the relevance cutoff
    changes when a different queue length k is evaluated.
    """
    training_score = np.zeros(len(training))
    test_score = np.zeros(len(test))
    for target, weight in zip(TARGETS, [0.55, 0.45]):
        training_score += 100 * weight * empirical_percentiles(training[target], training[target])
        test_score += 100 * weight * empirical_percentiles(training[target], test[target])
    cutoff = float(np.quantile(training_score, quantile))
    relevant = np.flatnonzero(test_score >= cutoff).tolist()
    return relevant, cutoff, test_score


def binary_ranking_metrics(order, relevant, k):
    hits = len(set(order[:k]) & set(relevant))
    prevalence = len(relevant) / len(order)
    precision = hits / k
    return {"hits": hits, "precision_at_k": precision,
            "recall_at_k": hits / len(relevant) if relevant else 0.0,
            "relevant_cells": len(relevant), "relevance_prevalence": prevalence,
            "lift_over_random": precision / prevalence if prevalence else None}


def main():
    parser = argparse.ArgumentParser(description="Evaluate held-out municipal priority ranking.")
    parser.add_argument("--input", default="data/processed/lagged_cell_dataset.parquet")
    parser.add_argument("--output", default="reports/metrics/priority_ranking_metrics.json")
    parser.add_argument("--queue-output", default="data/processed/heldout_priority_queue.parquet")
    args = parser.parse_args()

    source = pd.read_parquet(args.input)
    encoded, base_features, nlp_features = prepare_features(source)
    augmented = base_features + nlp_features
    train_mask = encoded["split"].isin(["train", "val"])
    test_mask = encoded["split"].eq("test")
    test = encoded.loc[test_mask].copy().reset_index(drop=True)

    predictions = {}
    for target in TARGETS:
        model = make_lightgbm(42)
        model.fit(encoded.loc[train_mask, augmented], encoded.loc[train_mask, target])
        predictions[target] = model.predict(encoded.loc[test_mask, augmented])

    test["predicted_delay"] = predictions["mean_resolution_delay_hours"]
    test["predicted_repeat"] = predictions["repeat_request_rate_14d"]
    test["predicted_priority_score"] = 100 * (
        0.45 * pd.Series(test["predicted_delay"]).rank(pct=True).to_numpy()
        + 0.35 * pd.Series(test["predicted_repeat"]).rank(pct=True).to_numpy()
        + 0.20 * test["citizen_dissatisfaction_rate"].rank(pct=True).to_numpy()
    )
    test["observed_burden_score"] = 100 * (
        0.55 * test["mean_resolution_delay_hours"].rank(pct=True)
        + 0.45 * test["repeat_request_rate_14d"].rank(pct=True)
    )

    predicted_order = test["predicted_priority_score"].sort_values(ascending=False).index.to_list()
    observed_order = test["observed_burden_score"].sort_values(ascending=False).index.to_list()
    n = len(test)
    k_values = sorted({min(k, n) for k in [10, 20, max(1, round(n * 0.10)), max(1, round(n * 0.20))]})
    metrics = {}
    for k in k_values:
        metrics[str(k)] = {
            **binary_ranking_metrics(predicted_order, observed_order[:k], k),
            "ndcg_at_k": float(
                ndcg_score(
                    test[["observed_burden_score"]].T.to_numpy(),
                    test[["predicted_priority_score"]].T.to_numpy(),
                    k=k,
                )
            ),
        }

    relevant, cutoff, fixed_scores = fixed_threshold_relevance(
        encoded.loc[encoded["split"].eq("train"), TARGETS], test[TARGETS]
    )
    fixed_metrics = {str(k): binary_ranking_metrics(predicted_order, relevant, k) for k in k_values}

    output = {
        "evaluation": "One-month-ahead held-out dashboard priority ranking",
        "test_cells": n,
        "test_target_period": "2024",
        "predicted_score": "45% predicted delay rank + 35% predicted repeat rank + 20% lagged dissatisfaction rank",
        "relevance_definition": "Top-k cells by observed 2024 burden: 55% delay rank + 45% repeat rank",
        "legacy_lift_interpretation": "Top-k relevance has prevalence k/N, so lift = Precision@k * N/k; it is a rescaling, not independent evidence of usefulness",
        "metrics_by_k": metrics,
        "fixed_threshold": {
            "score_definition": "55% delay percentile + 45% repeat percentile, relative to frozen February-August 2023 training-outcome distributions",
            "cutoff_definition": "At or above the 80th percentile of the training burden-score distribution",
            "cutoff_source": "train only; no validation or 2024 outcomes",
            "cutoff": cutoff,
            "independent_of_queue_k": True,
            "relevant_cells": len(relevant),
            "test_cells": n,
            "relevance_prevalence": len(relevant) / n,
            "metrics_by_k": fixed_metrics,
            "interpretation": "Exploratory burden proxy; cutoff is not a validated municipal service standard",
        },
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)

    queue_columns = [
        "complaint_type_upper", "borough", "year", "month", "target_year", "target_month",
        "total_request_volume", "predicted_delay", "predicted_repeat", "citizen_dissatisfaction_rate",
        "predicted_priority_score", "mean_resolution_delay_hours", "repeat_request_rate_14d",
        "observed_burden_score",
    ]
    os.makedirs(os.path.dirname(args.queue_output), exist_ok=True)
    test[queue_columns].sort_values("predicted_priority_score", ascending=False).to_parquet(args.queue_output, index=False)
    print(f"Wrote ranking metrics to {args.output}")


if __name__ == "__main__":
    main()
