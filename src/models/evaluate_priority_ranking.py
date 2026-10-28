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
    selected = set(predicted_order[:k])
    return len(selected & set(relevant_indices)) / k


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
            "precision_at_k": float(precision_at_k(predicted_order, observed_order[:k], k)),
            "lift_over_random": float(precision_at_k(predicted_order, observed_order[:k], k) / (k / n)),
            "ndcg_at_k": float(
                ndcg_score(
                    test[["observed_burden_score"]].T.to_numpy(),
                    test[["predicted_priority_score"]].T.to_numpy(),
                    k=k,
                )
            ),
        }

    output = {
        "evaluation": "One-month-ahead held-out dashboard priority ranking",
        "test_cells": n,
        "test_target_period": "2024",
        "predicted_score": "45% predicted delay rank + 35% predicted repeat rank + 20% lagged dissatisfaction rank",
        "relevance_definition": "Top-k cells by observed 2024 burden: 55% delay rank + 45% repeat rank",
        "metrics_by_k": metrics,
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
