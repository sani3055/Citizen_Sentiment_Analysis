"""
Unit tests for operational outcome computation (delay and repeat request flags).
"""

import pandas as pd
from src.outcomes.calculate_outcomes import compute_repeat_flags


def test_compute_repeat_flags():
    df = pd.DataFrame({
        "unique_key": ["1", "2", "3"],
        "complaint_type": ["Illegal Parking", "Illegal Parking", "Illegal Parking"],
        "borough": ["MANHATTAN", "MANHATTAN", "MANHATTAN"],
        "incident_address": ["100 Broadway", "100 Broadway", "500 5th Ave"],
        "created_dt": pd.to_datetime([
            "2024-01-01 10:00:00",
            "2024-01-05 12:00:00",  # 4.08 days later -> repeat for 7d, 14d, 30d
            "2024-01-06 12:00:00",  # different address -> not repeat
        ]),
    })

    result = compute_repeat_flags(df, windows=[7, 14, 30])
    assert result.loc[0, "is_repeat_7d"] == 0
    assert result.loc[1, "is_repeat_7d"] == 1
    assert result.loc[1, "is_repeat_14d"] == 1
    assert result.loc[2, "is_repeat_7d"] == 0


def test_compute_repeat_flags_is_order_invariant():
    df = pd.DataFrame({
        "unique_key": ["2", "1", "3"],
        "complaint_type": ["Illegal Parking"] * 3,
        "borough": ["MANHATTAN"] * 3,
        "incident_address": ["100 Broadway", "100 Broadway", "500 5th Ave"],
        "created_dt": pd.to_datetime([
            "2024-01-05 12:00:00",
            "2024-01-01 10:00:00",
            "2024-01-06 12:00:00",
        ]),
    })
    result = compute_repeat_flags(df, windows=[7])
    by_key = result.set_index("unique_key")
    assert by_key.loc["1", "is_repeat_7d"] == 0
    assert by_key.loc["2", "is_repeat_7d"] == 1
    assert by_key.loc["3", "is_repeat_7d"] == 0


def test_compute_repeat_flags_does_not_cross_boroughs():
    df = pd.DataFrame({
        "unique_key": ["1", "2"],
        "complaint_type": ["Noise", "Noise"],
        "borough": ["BROOKLYN", "QUEENS"],
        "incident_address": ["10 Main Street", "10 Main Street"],
        "created_dt": pd.to_datetime(["2024-01-01", "2024-01-02"]),
    })
    result = compute_repeat_flags(df, windows=[7])
    assert result["is_repeat_7d"].sum() == 0
