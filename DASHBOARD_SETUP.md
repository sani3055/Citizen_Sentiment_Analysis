# Run the dashboard on another computer

The dashboard displays the project's saved, aggregate research results. It does not download live complaints, retrain models, or require a GPU, API key, raw datasets, or model checkpoints.

## Windows (PowerShell)

Install Python 3.12 or 3.13 and Git first. Open PowerShell in a folder where you want the project, then run:

```powershell
git clone https://github.com/sani3055/Citizen_Sentiment_Analysis.git
cd Citizen_Sentiment_Analysis
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dashboard.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

If Python 3.13 is installed instead, change `py -3.12` to `py -3.13`. These commands use the environment's Python directly, so PowerShell activation/execution-policy changes are unnecessary.

Open **http://localhost:8501** on that same computer. Keep PowerShell running while using the dashboard. Press **Ctrl+C** in PowerShell to stop it.

## macOS / Linux

With Python 3.12 or 3.13 and Git installed:

```bash
git clone https://github.com/sani3055/Citizen_Sentiment_Analysis.git
cd Citizen_Sentiment_Analysis
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dashboard.txt
.venv/bin/python -m streamlit run dashboard/app.py
```

## Open it again later (Windows)

From the cloned project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

To get updates, stop Streamlit, run `git pull`, then run the command again. If dependency requirements changed, reinstall `requirements-dashboard.txt` first.

## Files needed at runtime

| File | Purpose |
| --- | --- |
| `dashboard/app.py` | Streamlit application, both workspaces |
| `.streamlit/config.toml` | Dark theme |
| `requirements-dashboard.txt` | Five direct dashboard dependencies |
| `data/processed/integrated_cell_dataset.parquet` | 2,006 historical aggregate service cells |
| `data/processed/heldout_priority_queue.parquet` | 994 held-out prediction/ranking rows |
| `reports/metrics/lagged_predictive_modeling_results.json` | Predictive evaluation |
| `reports/metrics/robustness_results.json` | Multi-seed robustness |
| `reports/metrics/priority_ranking_metrics.json` | Ranking evaluation |
| `reports/metrics/review_corrections_results.json` | Corrected baselines and feature ablations |
| `reports/metrics/selected_feature_results.json` | Exploratory validation-selected family comparison |
| `reports/figures/lagged_shap_feature_importance.png` | Optional one-month-ahead feature-importance figure |

All these files are included in the repository. No separate data download or Git LFS is needed. Use `requirements-dashboard.txt`, not the full research `requirements.txt` or `requirements-lock.txt`, for dashboard-only setup.

## Troubleshooting

- **Not reachable:** make sure the Streamlit command is still running successfully. `localhost` always means the computer opening the link; your friend must run their own local copy.
- **Port already in use:** add `--server.port 8502` to the run command, then open http://localhost:8502.
- **Integrated dataset not found:** run `git pull` in the cloned project, then check that the two Parquet files above exist under `data/processed/`.
- **Module not found:** reinstall with the same environment Python: `.\.venv\Scripts\python.exe -m pip install -r requirements-dashboard.txt`.
- **Do not double-click `app.py`:** start it with `python -m streamlit run` as shown above.
