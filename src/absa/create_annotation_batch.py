"""Create a human-annotation batch for municipal ABSA evaluation.

The generated CSV intentionally contains blank labels.  Model-generated
labels must not be presented as manual ground truth.
"""

import argparse
import json
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


ASPECTS = [
    "Information Intake",
    "Issue Correction",
    "Other",
    "Response Time",
    "Status Updates",
    "Work Quality",
]


def make_batch(df: pd.DataFrame, n: int = 600, seed: int = 42) -> pd.DataFrame:
    required = {"unique_key", "complaint_type", "borough", "resolution_description"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    usable = df.copy()
    if "year" not in usable.columns or "month" not in usable.columns:
        created = pd.to_datetime(usable["created_date"], errors="coerce")
        usable["year"] = created.dt.year
        usable["month"] = created.dt.month
    required_dates = {"year", "month"}
    if usable[list(required_dates)].isna().any().any():
        usable = usable.dropna(subset=list(required_dates)).copy()
    usable["text"] = usable["resolution_description"].fillna("").astype(str).str.strip()
    usable = usable[usable["text"].str.len() >= 20].copy()
    usable["stratum"] = usable["complaint_type"].astype(str) + " | " + usable["borough"].astype(str)
    n = min(n, len(usable))

    # Ensure geographic/service coverage before filling the remainder.
    first = usable.groupby("stratum", group_keys=False).sample(n=1, random_state=seed)
    remaining = usable.drop(index=first.index)
    fill_n = max(0, n - len(first))
    fill = remaining.sample(n=min(fill_n, len(remaining)), random_state=seed)
    batch = pd.concat([first, fill], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)
    batch = batch.rename(columns={"unique_key": "request_key"})
    batch.insert(0, "annotation_id", [f"ABSA_{i:04d}" for i in range(1, len(batch) + 1)])
    keep = ["annotation_id", "request_key", "complaint_type", "borough", "year", "month", "text"]
    batch = batch[keep]
    batch["annotator_1_label"] = ""
    batch["annotator_2_label"] = ""
    batch["adjudicated_label"] = ""
    batch["notes"] = ""
    return batch


def main():
    parser = argparse.ArgumentParser(description="Create a stratified ABSA annotation batch.")
    parser.add_argument("--input", default="data/raw/nyc311_raw.parquet")
    parser.add_argument("--output", default="data/annotation/absa_annotation_batch.csv")
    parser.add_argument("--size", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_parquet(args.input)
    batch = make_batch(df, n=args.size, seed=args.seed)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    batch.to_csv(args.output, index=False, encoding="utf-8-sig")
    metadata = {
        "sample_size": int(len(batch)),
        "seed": args.seed,
        "source": args.input,
        "label_set": ASPECTS,
        "labels_required": ["annotator_1_label", "annotator_2_label", "adjudicated_label"],
        "instruction": "Complete labels manually; leave no blank labels before evaluation.",
    }
    meta_path = os.path.splitext(args.output)[0] + ".json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Wrote {len(batch):,} annotation rows to {args.output}")
    print(f"Wrote annotation metadata to {meta_path}")


if __name__ == "__main__":
    main()
