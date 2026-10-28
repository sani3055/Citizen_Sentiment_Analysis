"""
Unit tests for data validation functions (validate_rsat, validate_311).
"""

import pytest
import pandas as pd
from src.data.validator import validate_rsat, validate_311


def test_validate_rsat_success():
    df = pd.DataFrame({
        "complaint_type": ["Illegal Parking", "Noise"],
        "borough": ["BROOKLYN", "MANHATTAN"],
        "year": [2023, 2024],
        "month": [1, 5],
        "overall_satisfaction": ["Strongly Agree", "Disagree"],
        "dissatisfaction_reason": [None, "The Agency did not correct the issue."],
    })
    assert validate_rsat(df) is True


def test_validate_rsat_null_borough_raises():
    df = pd.DataFrame({
        "complaint_type": ["Illegal Parking"],
        "borough": [None],
        "year": [2023],
        "month": [1],
        "overall_satisfaction": ["Agree"],
        "dissatisfaction_reason": [None],
    })
    with pytest.raises(AssertionError, match="null borough"):
        validate_rsat(df)


def test_validate_311_success():
    df = pd.DataFrame({
        "complaint_type": ["Noise - Residential"],
        "borough": ["QUEENS"],
        "created_date": ["2024-01-01T10:00:00.000"],
        "closed_date": ["2024-01-01T14:30:00.000"],
        "resolution_description": ["Condition was resolved by police."],
    })
    assert validate_311(df) is True


def test_validate_311_negative_delay_raises():
    df = pd.DataFrame({
        "complaint_type": ["Noise - Residential"],
        "borough": ["QUEENS"],
        "created_date": ["2024-01-01T15:00:00.000"],
        "closed_date": ["2024-01-01T10:00:00.000"],
        "resolution_description": ["Anomaly"],
    })
    with pytest.raises(AssertionError, match="records where created_date > closed_date"):
        validate_311(df)
