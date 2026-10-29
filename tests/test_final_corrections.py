"""Checks for validation-only feature selection and fixed ranking relevance."""

import pandas as pd
import pytest

from src.models.selected_feature_analysis import choose_validation_candidate, candidate_subsets
from src.models.evaluate_priority_ranking import fixed_threshold_relevance, binary_ranking_metrics


def test_subset_choice_uses_validation_not_test_result():
    candidates = [
        {"features": ["x"], "validation": {"r2": 0.4}, "test_r2": 0.99},
        {"features": ["x", "topic"], "validation": {"r2": 0.6}, "test_r2": -10},
    ]
    assert choose_validation_candidate(candidates) is candidates[1]
    assert candidate_subsets({"topics": [], "ABSA": [], "RSAT": []})[0] == []
    assert len(candidate_subsets({"topics": [], "ABSA": [], "RSAT": []})) == 8


def test_fixed_cutoff_is_not_fitted_on_test_distribution():
    cols = ["mean_resolution_delay_hours", "repeat_request_rate_14d"]
    train = pd.DataFrame({cols[0]: [1, 2, 3, 4, 5], cols[1]: [.1, .2, .3, .4, .5]})
    test = pd.DataFrame({cols[0]: [1, 3, 10], cols[1]: [.1, .3, 1.]})
    relevant, cutoff, _ = fixed_threshold_relevance(train, test)
    _, shifted_cutoff, _ = fixed_threshold_relevance(train, test * 100)
    assert cutoff == shifted_cutoff
    assert relevant == [2]


def test_fixed_relevance_prevalence_stays_constant_across_k():
    order, relevant = [3, 1, 4, 2, 0], [3, 4]
    one = binary_ranking_metrics(order, relevant, 1)
    three = binary_ranking_metrics(order, relevant, 3)
    assert one["relevance_prevalence"] == three["relevance_prevalence"] == .4
    assert three["hits"] == 2
    assert three["lift_over_random"] == pytest.approx((2 / 3) / .4)
