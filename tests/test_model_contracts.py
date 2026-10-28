"""Regression tests for model feature and temporal contracts."""

import pandas as pd

from src.models.train_predictive import prepare_features


def test_structured_baseline_controls_service_identity():
    df = pd.DataFrame({
        "complaint_type_upper": ["NOISE", "PARKING"],
        "borough": ["QUEENS", "QUEENS"],
        "month": [1, 2],
        "total_request_volume": [100, 200],
        "mean_vader_score": [0.1, -0.2],
    })
    _, base, augmented = prepare_features(df)
    assert any(c.startswith("service_") for c in base)
    assert len(base + augmented) > len(base)


def test_feature_contract_has_no_target_columns():
    df = pd.DataFrame({
        "complaint_type_upper": ["NOISE"],
        "borough": ["QUEENS"],
        "month": [1],
        "total_request_volume": [100],
        "mean_resolution_delay_hours": [4.0],
        "repeat_request_rate_14d": [0.2],
    })
    _, base, augmented = prepare_features(df)
    assert "mean_resolution_delay_hours" not in base + augmented
    assert "repeat_request_rate_14d" not in base + augmented
