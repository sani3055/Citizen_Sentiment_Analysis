"""Contract checks for the role-based Streamlit dashboard."""

from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def test_dashboard_exposes_both_role_views():
    source = APP_PATH.read_text(encoding="utf-8")
    assert '"Municipal Operations"' in source
    assert '"Resident View"' in source


def test_dashboard_uses_privacy_safe_aggregate_language():
    source = APP_PATH.read_text(encoding="utf-8")
    assert "individual requests" in source
    assert "service × borough × month" in source


def test_dashboard_exposes_heldout_ranking_evidence():
    source = APP_PATH.read_text(encoding="utf-8")
    assert 'load_json("lagged_predictive_modeling_results.json")' in source
    assert 'load_json("priority_ranking_metrics.json")' in source
    assert "Priority Precision@" in source
