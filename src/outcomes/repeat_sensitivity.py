"""Sensitivity analysis for high 14-day municipal repeat-request rates."""

import argparse
import json
import os

import pandas as pd


HOUSING_SERVICE_PROXY = {
    "HEAT/HOT WATER",
    "PLUMBING",
    "PAINT/PLASTER",
    "UNSANITARY CONDITION",
}


def rate(series: pd.Series) -> float:
    return float(series.mean()) if len(series) else float("nan")


def main():
    parser = argparse.ArgumentParser(description="Audit repeat-rate sensitivity to housing and address concentration.")
    parser.add_argument("--input", default="data/processed/nyc311_with_outcomes.parquet")
    parser.add_argument("--output", default="reports/metrics/repeat_rate_sensitivity.json")
    parser.add_argument("--high-volume-address-threshold", type=int, default=10)
    args = parser.parse_args()

    columns = ["complaint_type", "borough", "incident_address", "is_repeat_14d"]
    df = pd.read_parquet(args.input, columns=columns)
    df["complaint_type_upper"] = df["complaint_type"].fillna("").str.upper()
    address = df["incident_address"].fillna("").astype(str).str.upper().str.strip()
    usable_address = address.ne("") & address.ne("UNKNOWN")
    address_key = df["borough"].fillna("").astype(str).str.upper().str.strip() + "|" + address
    address_counts = address_key[usable_address].value_counts()
    high_volume_addresses = set(address_counts[address_counts >= args.high_volume_address_threshold].index)
    high_volume_mask = address_key.isin(high_volume_addresses)

    heat_mask = df["complaint_type_upper"].eq("HEAT/HOT WATER")
    housing_mask = df["complaint_type_upper"].isin(HOUSING_SERVICE_PROXY)
    repeat_total = int(df["is_repeat_14d"].sum())

    output = {
        "definition": "A repeat is a later request in the same borough, at the same cleaned address, and for the same complaint type within more than 0 and no more than 14 days.",
        "all_requests": {
            "n": int(len(df)),
            "repeat_count_14d": repeat_total,
            "repeat_rate_14d": rate(df["is_repeat_14d"]),
        },
        "heat_hot_water": {
            "n": int(heat_mask.sum()),
            "repeat_count_14d": int(df.loc[heat_mask, "is_repeat_14d"].sum()),
            "repeat_rate_14d": rate(df.loc[heat_mask, "is_repeat_14d"]),
            "share_of_all_repeat_flags": float(df.loc[heat_mask, "is_repeat_14d"].sum() / repeat_total) if repeat_total else 0.0,
        },
        "excluding_heat_hot_water": {
            "n": int((~heat_mask).sum()),
            "repeat_count_14d": int(df.loc[~heat_mask, "is_repeat_14d"].sum()),
            "repeat_rate_14d": rate(df.loc[~heat_mask, "is_repeat_14d"]),
        },
        "housing_service_proxy": {
            "included_services": sorted(HOUSING_SERVICE_PROXY),
            "n": int(housing_mask.sum()),
            "repeat_count_14d": int(df.loc[housing_mask, "is_repeat_14d"].sum()),
            "repeat_rate_14d": rate(df.loc[housing_mask, "is_repeat_14d"]),
            "share_of_all_repeat_flags": float(df.loc[housing_mask, "is_repeat_14d"].sum() / repeat_total) if repeat_total else 0.0,
        },
        "excluding_housing_service_proxy": {
            "n": int((~housing_mask).sum()),
            "repeat_count_14d": int(df.loc[~housing_mask, "is_repeat_14d"].sum()),
            "repeat_rate_14d": rate(df.loc[~housing_mask, "is_repeat_14d"]),
        },
        "high_volume_address_proxy": {
            "minimum_requests_per_address": args.high_volume_address_threshold,
            "distinct_high_volume_addresses": int(len(high_volume_addresses)),
            "n_requests": int(high_volume_mask.sum()),
            "repeat_count_14d": int(df.loc[high_volume_mask, "is_repeat_14d"].sum()),
            "repeat_rate_14d": rate(df.loc[high_volume_mask, "is_repeat_14d"]),
            "share_of_all_repeat_flags": float(df.loc[high_volume_mask, "is_repeat_14d"].sum() / repeat_total) if repeat_total else 0.0,
        },
        "limitation": "The public extract has no authoritative building-type field. Housing-service and high-volume-address results are sensitivity proxies, not verified multi-unit-building classifications.",
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    print(f"Wrote repeat-rate sensitivity metrics to {args.output}")


if __name__ == "__main__":
    main()
