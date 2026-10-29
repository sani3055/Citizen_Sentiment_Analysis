"""Check the dashboard using only the files shipped for dashboard users."""

from pathlib import Path
import shutil

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_runs_with_distributed_runtime_files(tmp_path):
    runtime_files = [
        "dashboard/app.py",
        ".streamlit/config.toml",
        "data/processed/integrated_cell_dataset.parquet",
        "data/processed/heldout_priority_queue.parquet",
        "reports/metrics/lagged_predictive_modeling_results.json",
        "reports/metrics/robustness_results.json",
        "reports/metrics/priority_ranking_metrics.json",
        "reports/metrics/review_corrections_results.json",
        "reports/metrics/selected_feature_results.json",
        "reports/figures/lagged_shap_feature_importance.png",
    ]
    for relative in runtime_files:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)

    app = AppTest.from_file(str(tmp_path / "dashboard/app.py"))
    app.run(timeout=60)
    assert not app.exception, [e.message for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert len(app.metric) >= 4

    app.sidebar.radio[0].set_value("Resident View").run(timeout=60)
    assert not app.exception, [e.message for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert len(app.metric) >= 4
