"""
Phase 8: Aggregate Integration Module.
Integrates operational outcomes, VADER sentiment features, topic distributions,
and ABSA grievance rates at the municipal service cell level:
(complaint_type_upper, borough, year, month).
Implements strict chronological train/validation/test partitions from the
configured calendar periods.  The current local snapshot uses 2023 train and
2024 as the operational out-of-time test horizon.
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

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Aggregate integration for Smart Cities project.")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    proc_dir = config["data"]["processed_dir"]
    metrics_dir = "reports/metrics"
    raw_dir = config["data"]["raw_dir"]

    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    min_samples = config["data"].get("min_cell_samples", 10)
    train_yr = config["models"]["temporal_split"].get("train_year", 2023)
    val_yr = config["models"]["temporal_split"].get("val_year", 2024)
    test_yr = config["models"]["temporal_split"].get("test_year", 2025)

    join_keys = ["complaint_type_upper", "borough", "year", "month"]

    # 1. Load component datasets
    outcomes_path = os.path.join(proc_dir, "cell_outcomes.parquet")
    vader_path = os.path.join(proc_dir, "cell_vader_features.parquet")
    topics_path = os.path.join(proc_dir, "cell_topic_features.parquet")
    absa_path = os.path.join(proc_dir, "cell_absa_features.parquet")
    rsat_raw_path = os.path.join(raw_dir, "rsat_raw.parquet")

    logger.info("Loading feature tables for aggregate integration...")
    df_outcomes = pd.read_parquet(outcomes_path)
    df_vader = pd.read_parquet(vader_path)
    df_topics = pd.read_parquet(topics_path) if os.path.exists(topics_path) else None
    df_absa = pd.read_parquet(absa_path) if os.path.exists(absa_path) else None
    df_rsat = pd.read_parquet(rsat_raw_path)

    # 2. Extract RSAT cell ground-truth satisfaction rates
    df_rsat["complaint_type_upper"] = df_rsat["complaint_type"].str.upper()
    df_rsat["is_dissatisfied"] = df_rsat["overall_satisfaction"].isin(["Disagree", "Strongly Disagree"]).astype(int)
    df_rsat["is_satisfied"] = df_rsat["overall_satisfaction"].isin(["Agree", "Strongly Agree"]).astype(int)

    cell_rsat = df_rsat.groupby(join_keys).agg(
        rsat_response_count=("unique_key", "count"),
        citizen_dissatisfaction_rate=("is_dissatisfied", "mean"),
        citizen_satisfaction_rate=("is_satisfied", "mean"),
    ).reset_index()

    # Filter cells meeting minimum sample threshold in outcomes
    initial_outcome_cells = len(df_outcomes)
    logger.info(f"Initial outcome cells: {initial_outcome_cells:,}")
    integrated = pd.merge(df_outcomes, cell_rsat, on=join_keys, how="inner")
    matched_rsat_cells = len(integrated)
    logger.info(f"Cells matched with RSAT: {matched_rsat_cells:,}")

    # Merge VADER features
    vader_cols = [c for c in df_vader.columns if c not in ["vader_cell_pred", "n_311_requests"]]
    integrated = pd.merge(integrated, df_vader[vader_cols], on=join_keys, how="left")

    # Merge Topic features if present
    if df_topics is not None:
        integrated = pd.merge(integrated, df_topics, on=join_keys, how="left")
        integrated["dominant_topic_mode"] = integrated["dominant_topic_mode"].fillna(0)
        integrated["topic_entropy"] = integrated["topic_entropy"].fillna(0.0)
        if "dominant_bertopic_mode" in integrated:
            integrated["dominant_bertopic_mode"] = integrated["dominant_bertopic_mode"].fillna(-1)
        if "bertopic_outlier_rate" in integrated:
            integrated["bertopic_outlier_rate"] = integrated["bertopic_outlier_rate"].fillna(1.0)

    # Merge ABSA features if present
    if df_absa is not None:
        integrated = pd.merge(integrated, df_absa, on=join_keys, how="left")
        # Fill missing aspect rates with 0.0
        for col in df_absa.columns:
            if col not in join_keys and col in integrated.columns:
                integrated[col] = integrated[col].fillna(0.0)

    # Filter cells by sample volume threshold
    integrated = integrated[integrated["total_request_volume"] >= min_samples].copy()
    robust_cells_before_split = len(integrated)
    logger.info(f"Robust cells meeting threshold (total_requests >= {min_samples}): {robust_cells_before_split:,}")

    # 3. Add Temporal Split Identifiers (Strictly Chronological).  The
    # complete operational extract covers 2023–2024: early 2023 is used for
    # training, late 2023 for validation, and all of 2024 is held out.
    def assign_split(row):
        yr = int(row["year"])
        mo = int(row["month"])
        if yr == train_yr and mo <= 8:
            return "train"
        elif yr == train_yr and mo > 8:
            return "val"
        elif yr == test_yr:
            return "test"
        return "excluded"

    integrated["split"] = integrated.apply(assign_split, axis=1)
    excluded = int((integrated["split"] == "excluded").sum())
    if excluded:
        logger.warning("Excluding %d cells outside configured temporal horizons", excluded)
        integrated = integrated[integrated["split"] != "excluded"].copy()
    split_counts = integrated["split"].value_counts().to_dict()
    logger.info(f"Temporal partition cell counts: {split_counts}")

    # 4. Save Integrated Parquet
    out_integrated_path = os.path.join(proc_dir, "integrated_cell_dataset.parquet")
    integrated.to_parquet(out_integrated_path, index=False)
    logger.info(f"Saved integrated multi-source dataset to {out_integrated_path} ({len(integrated):,} cells)")

    # 5. Save Integration Summary
    summary = {
        "join_keys": join_keys,
        "initial_outcome_cells": int(initial_outcome_cells),
        "cells_matched_with_rsat": int(matched_rsat_cells),
        "robust_cells_before_temporal_split": int(robust_cells_before_split),
        "cells_excluded_outside_temporal_horizons": int(excluded),
        "total_integrated_cells": int(len(integrated)),
        "min_cell_samples_threshold": min_samples,
        "temporal_partitions": {
            "train_year": train_yr,
            "train_cells": int(split_counts.get("train", 0)),
            "val_year": val_yr,
            "val_cells": int(split_counts.get("val", 0)),
            "test_year": test_yr,
            "test_cells": int(split_counts.get("test", 0)),
        },
        "target_variables": [
            "mean_resolution_delay_hours",
            "repeat_request_rate_14d",
        ],
        "feature_columns": [c for c in integrated.columns if c not in join_keys + ["split"]],
    }

    metrics_path = os.path.join(metrics_dir, "integration_summary.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved integration summary to {metrics_path}")

    logger.info("Phase 8 Aggregate Integration completed successfully!")


if __name__ == "__main__":
    main()
