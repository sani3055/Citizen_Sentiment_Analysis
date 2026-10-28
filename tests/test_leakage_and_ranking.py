"""Regression tests for reviewer-requested leakage and ranking controls."""

import pandas as pd

from src.absa.absa_pipeline import build_group_deduplicated_split
from src.models.evaluate_priority_ranking import precision_at_k


def test_absa_normalized_text_groups_do_not_cross_year_splits():
    rows = [
        {
            "unique_key": "1",
            "year": 2023,
            "resolution_description": " The agency inspected the condition. ",
            "dissatisfaction_reason": "The Agency did not correct the issue.",
        },
        {
            "unique_key": "2",
            "year": 2024,
            "resolution_description": "the agency inspected   the condition.",
            "dissatisfaction_reason": "The Agency corrected the issue, but they took too long to respond.",
        },
        {
            "unique_key": "3",
            "year": 2024,
            "resolution_description": "A new and distinct closure narrative.",
            "dissatisfaction_reason": "Other",
        },
    ]
    result, audit = build_group_deduplicated_split(pd.DataFrame(rows))

    grouped = result.groupby("normalized_description")["split_year"].nunique()
    assert grouped.max() == 1
    assert all(value == 0 for value in audit["cross_split_text_overlap_counts"].values())
    assert result.loc[
        result["normalized_description"] == "the agency inspected the condition.", "split_year"
    ].unique().tolist() == [2023]
    retained_labels = result.loc[
        result["normalized_description"] == "the agency inspected the condition.", "canonical_aspect"
    ].tolist()
    assert retained_labels == ["Issue Correction"]


def test_precision_at_k_uses_top_ranked_overlap():
    predicted_order = [3, 1, 4, 2, 0]
    relevant = [3, 4]
    assert precision_at_k(predicted_order, relevant, 2) == 0.5
    assert precision_at_k(predicted_order, relevant, 3) == 2 / 3
