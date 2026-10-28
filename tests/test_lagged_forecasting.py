"""Tests for one-month-ahead feature/target alignment."""

import pandas as pd

from src.models.train_lagged_predictive import build_lagged_dataset, assign_rolling_split


def test_lagged_target_comes_from_next_month():
    rows = []
    for month, delay in [(1, 10.0), (2, 20.0), (3, 30.0)]:
        rows.append({
            "complaint_type_upper": "NOISE",
            "borough": "QUEENS",
            "year": 2024,
            "month": month,
            "split": "test",
            "total_request_volume": 100,
            "mean_resolution_delay_hours": delay,
            "repeat_request_rate_14d": delay / 100,
        })
    result = build_lagged_dataset(pd.DataFrame(rows), lag_months=1)
    assert len(result) == 2
    ordered = result.sort_values("month")
    assert ordered.iloc[0]["mean_resolution_delay_hours"] == 20.0
    assert ordered.iloc[1]["mean_resolution_delay_hours"] == 30.0
    assert ordered.iloc[0]["target_year"] == 2024
    assert ordered.iloc[0]["target_month"] == 2


def test_lagged_alignment_drops_missing_next_month():
    df = pd.DataFrame([
        {"complaint_type_upper": "NOISE", "borough": "QUEENS", "year": 2024, "month": 1, "split": "test", "total_request_volume": 1, "mean_resolution_delay_hours": 1.0, "repeat_request_rate_14d": 0.1},
        {"complaint_type_upper": "NOISE", "borough": "QUEENS", "year": 2024, "month": 3, "split": "test", "total_request_volume": 3, "mean_resolution_delay_hours": 3.0, "repeat_request_rate_14d": 0.3},
    ])
    assert build_lagged_dataset(df, lag_months=1).empty


def test_rolling_split_excludes_future_and_unusable_months():
    df = pd.DataFrame({
        "target_year": [2023, 2023, 2023, 2024, 2025],
        "target_month": [2, 8, 10, 1, 1],
        "value": [1, 2, 3, 4, 5],
    })
    result = assign_rolling_split(df)
    assert result["split"].tolist() == ["train", "train", "val", "test"]
