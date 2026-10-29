# Reproducibility Guide

This repository contains the complete Team 16 pipeline. The primary research experiment uses information observed in month *t* to forecast resolution delay and 14-day repeat-request rate for the same service and borough in month *t+1*. Calendar year 2024 is the operational test horizon. The final-review subset-selection and fixed-cutoff ranking extensions reuse that previously examined horizon and are explicitly exploratory, not independent confirmatory tests.

## Data provenance

- NYC 311 Resolution Satisfaction Survey (RSAT), Socrata dataset `5ijn-vbdv`.
- NYC 311 Service Requests from 2010 to Present, Socrata dataset `erm2-nwe9`.
- The operational extract is limited to closed requests for the configured top 20 services, the five mapped boroughs, and calendar years 2023–2024.
- Public RSAT data suppress unrestricted citizen comments. NLP features therefore use agency-authored resolution descriptions, and ABSA results are interpreted as domain-transfer evidence.

Raw Socrata records are not redistributed in the small reproducibility archive. They can be reconstructed with the ingestion command below.

## Environment

Create a Python environment and install the research dependencies (the constraints in `requirements.txt` are minimum versions, while `requirements-lock.txt` records the original local versions):

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
venv\Scripts\python.exe scripts\compute_review_corrections.py
venv\Scripts\python.exe src\models\selected_feature_analysis.py
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
- `reports/metrics/selected_feature_results.json`
- `reports/figures/`

## Final-review analyses from the small archive

With the research dependencies installed, the bundled aggregate cells are sufficient for these commands; no raw re-download or model weights are needed:

```powershell
venv\Scripts\python.exe scripts\compute_review_corrections.py
venv\Scripts\python.exe src\models\selected_feature_analysis.py
venv\Scripts\python.exe src\models\evaluate_priority_ranking.py
venv\Scripts\python.exe -m pytest tests -q
```

The ranking command uses `lagged_cell_dataset.parquet`, which is bundled in the archive. `selected_feature_analysis.py` builds the lagged table in memory from integrated cells, selects among eight no-VADER family subsets using 2023 validation R² only, and reports fixed five-seed results and paired-cell bootstrap intervals on 2024. The fixed ranking cutoff uses training outcomes only; its prevalence is held constant across queue sizes. Original top-k overlap/lift is retained with raw hits and an explicit rescaling warning.

`scripts/apply_final_paper_corrections.py` rebuilds the corrected manuscript from the included preceding revised manuscript and saved metric artifacts. Use the bundled `scripts/build_reproducibility_archive.py --output outputs/team16_final_corrections_reproducibility.zip` to rebuild the compact archive. Dashboard-only users should follow `DASHBOARD_SETUP.md` instead of installing the training dependencies.

## Archiving and DOI

Public code: https://github.com/sani3055/Citizen_Sentiment_Analysis. The updated archive is `outputs/team16_final_corrections_reproducibility.zip`. Zenodo publication is deferred at the author's request; no DOI has been assigned or claimed. Before publishing, the authors should confirm the deposit metadata and chosen reuse licence. After publication, add the actual DOI to `CITATION.cff`, `.zenodo.json`, the manuscript data-availability statement, and the README.

