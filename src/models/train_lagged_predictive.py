"""One-month-ahead predictive experiment.

Uses features observed in cell month ``t`` to predict the operational outcome
of the same service/borough in month ``t+1``.  This is intentionally kept
separate from the contemporaneous experiment so both association and
forward-looking forecasting results remain auditable.
"""

import json
import os
import sys
import argparse
import logging

import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt
import shap
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import lightgbm as lgb

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.train_predictive import prepare_features, plot_r2_comparison, make_lightgbm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

JOIN_KEYS = ["complaint_type_upper", "borough", "year", "month"]
TARGETS = ["mean_resolution_delay_hours", "repeat_request_rate_14d"]


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_lagged_dataset(df: pd.DataFrame, lag_months: int = 1) -> pd.DataFrame:
    """Align month-t features with month-(t+lag) outcomes.

    Rows are retained only when the next month exists for the same service
    and borough.  The split belongs to the target month; every feature row is
    observed at least one month earlier.
    """
    if lag_months < 1:
        raise ValueError("lag_months must be >= 1")

    current = df.copy()
    current["period"] = pd.PeriodIndex(
        pd.to_datetime(dict(year=current["year"], month=current["month"], day=1)),
        freq="M",
    )
    future = current[JOIN_KEYS + TARGETS].copy()
    future["target_year"] = future["year"].astype(int)
    future["target_month"] = future["month"].astype(int)
    future["period"] = future.apply(
        lambda r: pd.Period(year=int(r["year"]), month=int(r["month"]), freq="M"), axis=1
    ) - lag_months
    future = future.drop(columns=["year", "month"])
    future = future.rename(columns={t: f"target_{t}" for t in TARGETS})

    # Do not carry the contemporaneous target columns into the feature side;
    # only the shifted target should be present in the final table.
    current_features = current.drop(columns=TARGETS)
    merged = current_features.merge(
        future,
        on=["complaint_type_upper", "borough", "period"],
        how="inner",
        validate="one_to_one",
    )
    merged = merged.drop(columns=["period"])
    merged = merged.rename(columns={f"target_{t}": t for t in TARGETS})
    return merged


def assign_rolling_split(df: pd.DataFrame) -> pd.DataFrame:
    """Split by the month being predicted, not by the feature month.

    Training predicts February-August 2023, validation predicts
    September-December 2023, and the untouched test predicts all available
    months of 2024 from one-month-lagged features.
    """
    out = df.copy()
    out["split"] = "excluded"
    year = out["target_year"].astype(int)
    month = out["target_month"].astype(int)
    out.loc[(year == 2023) & (month <= 8), "split"] = "train"
    out.loc[(year == 2023) & (month.between(9, 12)), "split"] = "val"
    out.loc[year == 2024, "split"] = "test"
    return out[out["split"] != "excluded"].copy()


def evaluate(y_true, y_pred):
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def model_factories():
    return {
        "Ridge": lambda: Ridge(alpha=1.0),
        "RandomForest": lambda: RandomForestRegressor(
            n_estimators=100, max_depth=8, random_state=42, n_jobs=-1
        ),
        "LightGBM": lambda: make_lightgbm(42),
    }


def main():
    parser = argparse.ArgumentParser(description="Run one-month-ahead municipal outcome forecasting.")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--lag-months", type=int, default=1)
    args = parser.parse_args()
    config = load_config(args.config)

    proc_dir = config["data"]["processed_dir"]
    metrics_dir = "reports/metrics"
    fig_dir = "reports/figures"
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    source_path = os.path.join(proc_dir, "integrated_cell_dataset.parquet")
    source = pd.read_parquet(source_path)
    lagged = build_lagged_dataset(source, lag_months=args.lag_months)
    lagged = assign_rolling_split(lagged)
    lagged_path = os.path.join(proc_dir, "lagged_cell_dataset.parquet")
    lagged.to_parquet(lagged_path, index=False)

    if lagged["split"].value_counts().get("train", 0) == 0 or lagged["split"].value_counts().get("val", 0) == 0 or lagged["split"].value_counts().get("test", 0) == 0:
        raise RuntimeError(f"Insufficient temporal partitions after lagging: {lagged['split'].value_counts().to_dict()}")

    encoded, base_features, nlp_features = prepare_features(lagged)
    augmented_features = base_features + nlp_features
    train_mask = encoded["split"] == "train"
    val_mask = encoded["split"] == "val"
    test_mask = encoded["split"] == "test"
    results = {}

    for target in TARGETS:
        y_train = encoded.loc[train_mask, target].values
        y_val = encoded.loc[val_mask, target].values
        y_test = encoded.loc[test_mask, target].values
        target_results = {"algorithms": {}}
        best_name = None
        best_val = -np.inf

        for name, factory in model_factories().items():
            base_val_model = factory()
            aug_val_model = factory()
            base_val_model.fit(encoded.loc[train_mask, base_features], y_train)
            aug_val_model.fit(encoded.loc[train_mask, augmented_features], y_train)
            val_base = evaluate(y_val, base_val_model.predict(encoded.loc[val_mask, base_features]))
            val_aug = evaluate(y_val, aug_val_model.predict(encoded.loc[val_mask, augmented_features]))

            # Refit both comparison models on train+validation before the
            # untouched test evaluation.
            train_val = train_mask | val_mask
            base_model = factory().fit(encoded.loc[train_val, base_features], encoded.loc[train_val, target].values)
            aug_model = factory().fit(encoded.loc[train_val, augmented_features], encoded.loc[train_val, target].values)
            pred_base = base_model.predict(encoded.loc[test_mask, base_features])
            pred_aug = aug_model.predict(encoded.loc[test_mask, augmented_features])
            eval_base = evaluate(y_test, pred_base)
            eval_aug = evaluate(y_test, pred_aug)
            _, p_value = stats.ttest_rel(np.abs(y_test - pred_base), np.abs(y_test - pred_aug))

            target_results["algorithms"][name] = {
                "baseline": {"test_metrics": eval_base},
                "augmented": {"test_metrics": eval_aug},
                "validation": {
                    "baseline_r2": val_base["r2"],
                    "augmented_r2": val_aug["r2"],
                },
                "delta_r2": round(eval_aug["r2"] - eval_base["r2"], 4),
                "delta_mae": round(eval_base["mae"] - eval_aug["mae"], 4),
                "paired_ttest_p_value": float(p_value),
                "statistically_significant": bool(p_value < 0.05),
            }
            if val_aug["r2"] > best_val:
                best_val = val_aug["r2"]
                best_name = name

        target_results["selected_algorithm"] = best_name
        target_results["validation_selected_r2"] = float(best_val)
        results[target] = target_results

    output = {
        "experiment": "one_month_ahead_forecasting",
        "lag_months": args.lag_months,
        "target_period_split": "train Feb-Aug 2023, validation Sep-Dec 2023, test Jan-Dec 2024",
        "source_cells": int(len(source)),
        "lagged_cells": int(len(lagged)),
        "split_counts": lagged["split"].value_counts().to_dict(),
        "target_period_definition": "features at month t predict outcomes at month t+1",
        "results_by_target": results,
    }
    # Explain the lagged augmented LightGBM delay model.  This replaces the
    # earlier same-month SHAP artifact so post-closure signals are interpreted
    # only as month-t predictors of month-(t+1) outcomes.
    try:
        train_val = train_mask | val_mask
        explain_model = make_lightgbm(42).fit(
            encoded.loc[train_val, augmented_features],
            encoded.loc[train_val, "mean_resolution_delay_hours"],
        )
        explain_frame = encoded.loc[test_mask, augmented_features]
        shap_values = shap.TreeExplainer(explain_model).shap_values(explain_frame)
        shap.summary_plot(shap_values, explain_frame, show=False, max_display=12)
        plt.title("Lagged SHAP Attribution: Month-t Features Predicting Month-(t+1) Delay")
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, "lagged_shap_feature_importance.png"), dpi=150)
        plt.close()
        ranking_values = np.abs(shap_values).mean(axis=0)
        output["shap_feature_importance_ranking"] = {
            str(name): float(value)
            for name, value in pd.Series(ranking_values, index=augmented_features)
            .sort_values(ascending=False)
            .head(12)
            .items()
        }
    except Exception as exc:
        logger.warning("Lagged SHAP generation failed: %s", exc)
        output["shap_feature_importance_ranking"] = {}
    metrics_path = os.path.join(metrics_dir, "lagged_predictive_modeling_results.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    plot_r2_comparison(results, os.path.join(fig_dir, "lagged_model_r2_comparison.png"))
    logger.info("Saved lagged dataset to %s", lagged_path)
    logger.info("Saved lagged metrics to %s", metrics_path)


if __name__ == "__main__":
    main()
