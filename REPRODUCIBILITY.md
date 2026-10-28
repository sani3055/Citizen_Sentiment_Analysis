# Reproducibility Guide

This repository contains the complete Team 16 pipeline. The primary research experiment uses information observed in month *t* to forecast resolution delay and 14-day repeat-request rate for the same service and borough in month *t+1*. Calendar year 2024 is the untouched operational test horizon.

## Data provenance

- NYC 311 Resolution Satisfaction Survey (RSAT), Socrata dataset `5ijn-vbdv`.
- NYC 311 Service Requests from 2010 to Present, Socrata dataset `erm2-nwe9`.
- The operational extract is limited to closed requests for the configured top 20 services, the five mapped boroughs, and calendar years 2023–2024.
- Public RSAT data suppress unrestricted citizen comments. NLP features therefore use agency-authored resolution descriptions, and ABSA results are interpreted as domain-transfer evidence.

Raw Socrata records are not redistributed in the small reproducibility archive. They can be reconstructed with the ingestion command below.

## Environment

Create a Python environment and install the pinned dependencies:

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Full execution order

```powershell
venv\Scripts\python.exe src\data\download_data.py --config configs\config.yaml
venv\Scripts\python.exe src\data\eda.py --config configs\config.yaml
venv\Scripts\python.exe src\sentiment\vader_baseline.py --config configs\config.yaml
venv\Scripts\python.exe src\topics\train_topics.py --config configs\config.yaml
venv\Scripts\python.exe src\absa\absa_pipeline.py --config configs\config.yaml
venv\Scripts\python.exe src\absa\train_deduplicated_transformer.py
venv\Scripts\python.exe src\absa\build_evaluation_summary.py
venv\Scripts\python.exe src\outcomes\calculate_outcomes.py --config configs\config.yaml
venv\Scripts\python.exe src\outcomes\repeat_sensitivity.py
venv\Scripts\python.exe src\outcomes\aggregate_integration.py --config configs\config.yaml
venv\Scripts\python.exe src\models\train_predictive.py --config configs\config.yaml
venv\Scripts\python.exe src\models\train_lagged_predictive.py --config configs\config.yaml
venv\Scripts\python.exe src\models\robustness_analysis.py
venv\Scripts\python.exe src\models\evaluate_priority_ranking.py
venv\Scripts\python.exe -m pytest -q
```

Topic models are fitted only on the configured 2023 training period and then frozen for later-month transformation. ABSA models share the same normalized-text-group split, so duplicate boilerplate cannot cross temporal partitions. Predictive robustness uses the same LightGBM recipe as the primary experiment across five random seeds and 2,000 bootstrap resamples.

## Outputs to verify

- `data/processed/integrated_cell_dataset.parquet`
- `data/processed/lagged_cell_dataset.parquet`
- `reports/metrics/lagged_predictive_modeling_results.json`
- `reports/metrics/robustness_results.json`
- `reports/metrics/absa_evaluation_summary.json`
- `reports/metrics/repeat_rate_sensitivity.json`
- `reports/metrics/priority_ranking_metrics.json`
- `reports/figures/`

## Archiving and DOI

The generated archive in `outputs/` is ready for upload to Zenodo. Uploading requires an author-owned account and cannot be completed automatically by this repository. After publication, add the assigned DOI to `CITATION.cff`, `.zenodo.json`, the manuscript data-availability statement, and the README.

