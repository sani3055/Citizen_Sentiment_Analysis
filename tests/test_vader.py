"""
Unit tests for VADER scoring and label mapping logic.
"""

from src.sentiment.vader_baseline import map_vader_label


def test_map_vader_label_positive():
    assert map_vader_label(0.45) == "Positive"
    assert map_vader_label(0.05) == "Positive"


def test_map_vader_label_negative():
    assert map_vader_label(-0.35) == "Negative"
    assert map_vader_label(-0.05) == "Negative"


def test_map_vader_label_neutral():
    assert map_vader_label(0.0) == "Neutral"
    assert map_vader_label(0.02) == "Neutral"
    assert map_vader_label(-0.02) == "Neutral"
