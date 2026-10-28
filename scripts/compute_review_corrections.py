"""Compute the additional baselines and feature-family ablations requested in review."""

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.train_predictive import make_lightgbm, prepare_features
from src.models.train_lagged_predictive import build_lagged_dataset, assign_rolling_split, TARGETS


def metrics(y_true, y_pred):
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def main():
    source = pd.read_parquet(os.path.join(PROJECT_ROOT, "data", "processed", "integrated_cell_dataset.parquet"))
    lagged = assign_rolling_split(build_lagged_dataset(source, lag_months=1))
    encoded, base_features, nlp_features = prepare_features(lagged)
    train_val = encoded["split"].isin(["train", "val"])
    test = encoded["split"] == "test"

    source_key = source.set_index(["complaint_type_upper", "borough", "year", "month"])
    service_month = source.groupby(["complaint_type_upper", "year", "month"])[TARGETS].mean()
    borough_month = source.groupby(["borough", "year", "month"])[TARGETS].mean()
    calendar_month = source.groupby(["year", "month"])[TARGETS].mean()
    last_values = []
    seasonal_values = []
    for row in lagged.loc[test].itertuples(index=False):
        target_key = (row.complaint_type_upper, row.borough, int(row.target_year), int(row.target_month))
        target_period = pd.Period(year=int(row.target_year), month=int(row.target_month), freq="M")
        previous = target_period - 1
        seasonal = target_period - 12
        last_key = (row.complaint_type_upper, row.borough, previous.year, previous.month)
        seasonal_key = (row.complaint_type_upper, row.borough, seasonal.year, seasonal.month)
        last_values.append({target: float(source_key.loc[last_key, target]) for target in TARGETS})
        seasonal_row = None
        if seasonal_key in source_key.index:
            seasonal_row = source_key.loc[seasonal_key]
        elif (row.complaint_type_upper, seasonal.year, seasonal.month) in service_month.index:
            seasonal_row = service_month.loc[(row.complaint_type_upper, seasonal.year, seasonal.month)]
        elif (row.borough, seasonal.year, seasonal.month) in borough_month.index:
            seasonal_row = borough_month.loc[(row.borough, seasonal.year, seasonal.month)]
        else:
            seasonal_row = calendar_month.loc[(seasonal.year, seasonal.month)]
        seasonal_values.append({target: float(seasonal_row[target]) for target in TARGETS})

    output = {
        "evaluation": "Held-out 2024 one-month-ahead baselines and LightGBM feature-family ablations",
        "primary_algorithm": "LightGBM",
        "test_cells": int(test.sum()),
        "naive_baselines": {},
        "feature_family_ablations": {},
        "feature_groups": {
            "structured": base_features,
            "VADER": [c for c in nlp_features if c.startswith("vader_") or c in {"mean_vader_score", "std_vader_score"}],
            "topics": [c for c in nlp_features if c in {"dominant_topic_mode", "topic_entropy", "dominant_bertopic_mode", "bertopic_outlier_rate"}],
            "ABSA": [c for c in nlp_features if c.startswith("is_aspect_")],
            "RSAT satisfaction": [c for c in nlp_features if c in {"citizen_dissatisfaction_rate", "citizen_satisfaction_rate"}],
        },
    }

    for target in TARGETS:
        y_test = encoded.loc[test, target].to_numpy()
        base_model = make_lightgbm(42).fit(encoded.loc[train_val, base_features], encoded.loc[train_val, target])
        full_model = make_lightgbm(42).fit(encoded.loc[train_val, base_features + nlp_features], encoded.loc[train_val, target])
        base_metrics = metrics(y_test, base_model.predict(encoded.loc[test, base_features]))
        full_metrics = metrics(y_test, full_model.predict(encoded.loc[test, base_features + nlp_features]))
        output["feature_family_ablations"][target] = {
            "structured_only": base_metrics,
            "all_augmented": full_metrics,
            "families": {},
        }
        for family, cols in output["feature_groups"].items():
            if family == "structured" or not cols:
                continue
            model = make_lightgbm(42).fit(encoded.loc[train_val, base_features + cols], encoded.loc[train_val, target])
            family_metrics = metrics(y_test, model.predict(encoded.loc[test, base_features + cols]))
            output["feature_family_ablations"][target]["families"][family] = {
                "features": cols,
                "metrics": family_metrics,
                "delta_r2_vs_structured": float(family_metrics["r2"] - base_metrics["r2"]),
                "delta_mae_vs_structured": float(base_metrics["mae"] - family_metrics["mae"]),
            }
        last_pred = np.array([x[target] for x in last_values])
        seasonal_pred = np.array([x[target] for x in seasonal_values])
        output["naive_baselines"][target] = {
            "last_value": metrics(y_test, last_pred),
            "seasonal_naive_12_month": metrics(y_test, seasonal_pred),
        }

    out_path = os.path.join(PROJECT_ROOT, "reports", "metrics", "review_corrections_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    print(out_path)


if __name__ == "__main__":
    main()
