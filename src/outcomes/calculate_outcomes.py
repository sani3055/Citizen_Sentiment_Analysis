"""
Phase 7: Operational Outcomes Module.
Computes resolution delay (in hours, with 99th percentile winsorization)
and multi-window repeat-request rates (7, 14, 30 days) from closed NYC 311 records.
Aggregates outcomes to the municipal service cell level (complaint_type, borough, year, month).
Satisfies VIT Review-2 criterion C4.
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


def compute_repeat_flags(df: pd.DataFrame, windows=(7, 14, 30)) -> pd.DataFrame:
    """
    Computes repeat request indicators based on chronological proximity
    matching same complaint_type, same borough, and same incident_address.
    """
    logger.info("Sorting records chronologically to detect repeat requests...")
    # Clean addresses before sorting.  The validity mask must be recomputed
    # after sorting/resetting the index; otherwise it can be aligned to the
    # wrong records when the input is not already chronological.
    df = df.copy()
    df["clean_address"] = df["incident_address"].fillna("").str.strip().str.upper()

    # Group key includes borough because street-address strings can recur in
    # different boroughs (for example, numbered avenues and "MAIN STREET").
    df = df.sort_values("created_dt").reset_index(drop=True)
    valid_address_mask = (df["clean_address"] != "") & (df["clean_address"] != "UNKNOWN")

    # Initialize repeat columns
    for w in windows:
        df[f"is_repeat_{w}d"] = 0

    logger.info(f"Computing repeat requests across windows: {windows} days...")
    # Calculate time difference between consecutive tickets at same address & complaint type
    # For speed and scale across 1M+ rows:
    sub_df = df[valid_address_mask].copy()
    sub_df["prev_created"] = sub_df.groupby(
        ["complaint_type", "borough", "clean_address"]
    )["created_dt"].shift(1)
    sub_df["time_diff_days"] = (sub_df["created_dt"] - sub_df["prev_created"]).dt.total_seconds() / 86400.0

    for w in windows:
        # Repeat condition: gap between 0 and w days
        repeat_indices = sub_df[(sub_df["time_diff_days"] > 0) & (sub_df["time_diff_days"] <= w)].index
        df.loc[repeat_indices, f"is_repeat_{w}d"] = 1
        rate = df[f"is_repeat_{w}d"].mean() * 100
        logger.info(f"Repeat rate ({w}-day window): {rate:.2f}% ({df[f'is_repeat_{w}d'].sum():,} requests)")

    return df


def main():
    parser = argparse.ArgumentParser(description="Calculate operational outcomes for Smart Cities project.")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    raw_dir = config["data"]["raw_dir"]
    proc_dir = config["data"]["processed_dir"]
    metrics_dir = "reports/metrics"

    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    outlier_pct = config["outcomes"].get("delay_outlier_percentile", 99.0)
    repeat_windows = config["data"].get("repeat_window_days", [7, 14, 30])

    nyc311_path = os.path.join(raw_dir, "nyc311_raw.parquet")
    logger.info(f"Loading NYC 311 records from {nyc311_path}...")
    df_311 = pd.read_parquet(nyc311_path)

    # 1. Compute Raw Delay Hours
    logger.info("Computing resolution delay hours...")
    df_311["created_dt"] = pd.to_datetime(df_311["created_date"], errors="coerce")
    df_311["closed_dt"] = pd.to_datetime(df_311["closed_date"], errors="coerce")

    # Filter any invalid dates
    valid_mask = df_311["created_dt"].notna() & df_311["closed_dt"].notna() & (df_311["created_dt"] <= df_311["closed_dt"])
    df_311 = df_311[valid_mask].copy()

    df_311["raw_delay_hours"] = (df_311["closed_dt"] - df_311["created_dt"]).dt.total_seconds() / 3600.0

    # 2. Winsorize Outlier Delay Hours
    p95 = float(np.percentile(df_311["raw_delay_hours"], 95))
    p99 = float(np.percentile(df_311["raw_delay_hours"], outlier_pct))
    logger.info(f"Delay distribution -> Median: {df_311['raw_delay_hours'].median():.2f}h, 95th: {p95:.2f}h, 99th: {p99:.2f}h")

    # Winsorize at p99
    df_311["resolution_delay_hours"] = np.clip(df_311["raw_delay_hours"], 0.0, p99)

    # 3. Compute Repeat Request Rates
    df_311 = compute_repeat_flags(df_311, windows=repeat_windows)

    # Save individual record outcomes
    out_record_path = os.path.join(proc_dir, "nyc311_with_outcomes.parquet")
    df_311.to_parquet(out_record_path, index=False)
    logger.info(f"Saved records with outcomes to {out_record_path} ({len(df_311):,} records)")

    # 4. Cell-Level Outcome Aggregations
    logger.info("Aggregating outcomes to (complaint_type, borough, year, month) cells...")
    df_311["complaint_type_upper"] = df_311["complaint_type"].str.upper()
    df_311["year"] = df_311["created_dt"].dt.year
    df_311["month"] = df_311["created_dt"].dt.month

    agg_rules = {
        "unique_key": "count",
        "resolution_delay_hours": ["mean", "median", "std"],
        "raw_delay_hours": ["mean", "median"],
    }
    for w in repeat_windows:
        agg_rules[f"is_repeat_{w}d"] = "mean"

    cell_grouped = df_311.groupby(["complaint_type_upper", "borough", "year", "month"]).agg(agg_rules)
    
    # Flatten column MultiIndex
    cell_grouped.columns = [
        f"{col}_{stat}".rstrip("_") if stat else col
        for col, stat in cell_grouped.columns
    ]
    cell_grouped = cell_grouped.reset_index()

    # Rename to canonical target variable names
    rename_map = {
        "unique_key_count": "total_request_volume",
        "resolution_delay_hours_mean": "mean_resolution_delay_hours",
        "resolution_delay_hours_median": "median_resolution_delay_hours",
        "resolution_delay_hours_std": "std_resolution_delay_hours",
        "raw_delay_hours_mean": "raw_mean_delay_hours",
        "is_repeat_7d_mean": "repeat_request_rate_7d",
        "is_repeat_14d_mean": "repeat_request_rate_14d",
        "is_repeat_30d_mean": "repeat_request_rate_30d",
    }
    cell_outcomes = cell_grouped.rename(columns=rename_map)
    cell_outcomes["std_resolution_delay_hours"] = cell_outcomes["std_resolution_delay_hours"].fillna(0.0)

    out_cell_path = os.path.join(proc_dir, "cell_outcomes.parquet")
    cell_outcomes.to_parquet(out_cell_path, index=False)
    logger.info(f"Saved cell-level outcomes to {out_cell_path} ({len(cell_outcomes):,} cells)")

    # 5. Save Outcomes Summary Metrics
    summary_metrics = {
        "resolution_delay": {
            "unit": "hours",
            "total_records": int(len(df_311)),
            "mean_raw_delay_hours": round(float(df_311["raw_delay_hours"].mean()), 2),
            "median_raw_delay_hours": round(float(df_311["raw_delay_hours"].median()), 2),
            "p95_delay_hours": round(p95, 2),
            "p99_delay_hours_winsorization_threshold": round(p99, 2),
            "mean_winsorized_delay_hours": round(float(df_311["resolution_delay_hours"].mean()), 2),
        },
        "repeat_request_rates": {
            "unit": "percentage",
            "repeat_rate_7d_pct": round(float(df_311["is_repeat_7d"].mean() * 100), 2),
            "repeat_rate_14d_pct": round(float(df_311["is_repeat_14d"].mean() * 100), 2),
            "repeat_rate_30d_pct": round(float(df_311["is_repeat_30d"].mean() * 100), 2),
        },
        "total_cells_aggregated": int(len(cell_outcomes)),
    }

    metrics_path = os.path.join(metrics_dir, "outcomes_summary.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=2)
    logger.info(f"Saved outcomes summary metrics to {metrics_path}")

    logger.info("Phase 7 Operational Outcomes completed successfully!")


if __name__ == "__main__":
    main()
