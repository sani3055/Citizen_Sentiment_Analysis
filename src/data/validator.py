"""
Data validation module for NYC 311 and RSAT datasets.
Verifies column schemas, value domains, and data hygiene constraints.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def validate_rsat(df: pd.DataFrame) -> bool:
    """
    Validate RSAT DataFrame integrity.
    Ensures required columns exist, no null boroughs, valid years, and valid Likert responses.
    """
    required_cols = {
        "complaint_type",
        "borough",
        "year",
        "month",
        "overall_satisfaction",
        "dissatisfaction_reason",
    }
    missing = required_cols - set(df.columns)
    assert not missing, f"RSAT missing required columns: {missing}"

    # Check null boroughs
    null_borough_count = df["borough"].isna().sum()
    assert null_borough_count == 0, f"RSAT contains {null_borough_count} null borough records"

    # Check year range
    years = set(df["year"].astype(int).unique())
    valid_years = {2023, 2024, 2025}
    assert years.issubset(valid_years), f"RSAT contains unexpected years: {years - valid_years}"

    # Check satisfaction values
    valid_satisfactions = {
        "Strongly Agree",
        "Agree",
        "Neutral",
        "Disagree",
        "Strongly Disagree",
    }
    actual_satisfactions = set(df["overall_satisfaction"].dropna().unique())
    assert actual_satisfactions.issubset(
        valid_satisfactions
    ), f"RSAT contains unexpected satisfaction values: {actual_satisfactions - valid_satisfactions}"

    logger.info(f"RSAT validation PASSED: {len(df):,} rows verified.")
    return True


def validate_311(df: pd.DataFrame) -> bool:
    """
    Validate NYC 311 closed service requests DataFrame integrity.
    Ensures closed_date is populated, delay is strictly non-negative, and required fields exist.
    """
    required_cols = {
        "complaint_type",
        "borough",
        "created_date",
        "closed_date",
        "resolution_description",
    }
    missing = required_cols - set(df.columns)
    assert not missing, f"NYC 311 missing required columns: {missing}"

    # Check closed_date is non-null
    null_closed = df["closed_date"].isna().sum()
    assert null_closed == 0, f"NYC 311 contains {null_closed} records with null closed_date"

    # Verify timestamps and delay ordering
    created = pd.to_datetime(df["created_date"], errors="coerce")
    closed = pd.to_datetime(df["closed_date"], errors="coerce")

    assert created.notna().all(), "NYC 311 contains unparseable created_date values"
    assert closed.notna().all(), "NYC 311 contains unparseable closed_date values"

    negative_delay = (created > closed).sum()
    assert negative_delay == 0, f"NYC 311 contains {negative_delay} records where created_date > closed_date"

    logger.info(f"NYC 311 validation PASSED: {len(df):,} rows verified.")
    return True
