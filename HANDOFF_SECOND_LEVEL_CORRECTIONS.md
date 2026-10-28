# Team 16 — Second-Level Corrections Handoff

**Workspace:** `D:\CITY PRJ`  
**Date:** 20 October 2026  
**Source correction memo:** `D:\Downloads\Team-16-DSC- Second Level Corrections.docx`

## 1. Current live jobs

Two jobs were running when this handoff was written. Check them before starting duplicate work.

1. **Final case-normalised NYC 311 download**
   - Process ID at handoff: `25272`
   - Expected server count: **4,205,256 rows** before invalid-timestamp cleaning.
   - Partial file at handoff: `data/raw/nyc311_raw.parquet.part`, approximately **80.74 MB** and growing.
   - Command:

     ```powershell
     venv\Scripts\python.exe -u src\data\download_data.py --config configs\config.yaml
     ```

   - This second download is necessary because Socrata complaint-type comparison is case-sensitive. The first full 3.23M-row attempt missed uppercase service series such as `HEAT/HOT WATER`. The corrected query uses `upper(complaint_type)`.

2. **Balanced duplicate-controlled DistilBERT ABSA rerun**
   - Process ID at handoff: `21900`
   - Command:

     ```powershell
     venv\Scripts\python.exe -u src\absa\train_deduplicated_transformer.py --epochs 4 --batch-size 16 --max-length 64
     ```

   - The metric file currently on disk was produced by the previous unweighted two-epoch run (test macro-F1 `0.0910`) and should be considered provisional until the active weighted run finishes.

Check status with:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.WorkingSet64 -gt 100MB} | Select-Object Id,CPU,WorkingSet,StartTime
Get-Item data\raw\nyc311_raw.parquet.part -ErrorAction SilentlyContinue | Select-Object Length,LastWriteTime
Get-Item reports\metrics\transformer_metrics.json | Select-Object Length,LastWriteTime
```

If the jobs are no longer running and the expected final artifacts were not written, rerun the commands above. The Socrata command needs internet access.

## 2. Corrections already implemented in source code

### Complete and validated ingestion

- `src/data/socrata_client.py`
  - Added server count queries, paged iteration, atomic streamed Parquet writing, and exact downloaded-count verification.
- `src/data/download_data.py`
  - Removed the silent 1.2M-row cap.
  - Uses 2023–2024 for operational records and 2023–2025 for RSAT.
  - Uses case-normalised service matching with `upper(complaint_type)`.
  - Restricts records to five mapped boroughs.
  - Validates timestamps and explicitly fails if any of the 24 operational months is absent.
  - Corrected the data-quality report period wording.
- `configs/config.yaml`
  - Added `operational_end_year: 2024`.
  - Added topic training cutoff `train_end_month: 7`.
  - Corrected team ID to 16.
- The original 1.2M-row extract is preserved as `data/raw/nyc311_raw_truncated_backup.parquet`.

### Post-closure leakage correction

- `src/models/train_lagged_predictive.py`
  - Month-*t* features now predict outcomes in month *t+1*.
  - Splits use **target months**: train targets February–August 2023, validation targets September–December 2023, test targets January–December 2024.
  - Added lagged SHAP output `reports/figures/lagged_shap_feature_importance.png`.
- Same-month modelling remains in `src/models/train_predictive.py` only as a secondary monitoring analysis.

### Train-only topic modelling

- `src/topics/train_topics.py`
  - LDA and BERTopic fit only on January–July 2023 text.
  - Later periods are transformed with frozen models.
  - Repeated narratives are scored once.
  - Cell features now include LDA mode/entropy and BERTopic mode/outlier rate.
- `src/models/train_predictive.py` includes both LDA and BERTopic features.

### Fair ABSA evaluation and duplicate control

- `src/absa/absa_pipeline.py`
  - Explains that `resolution_description` and `dissatisfaction_reason` are paired within the same RSAT row; no direct RSAT-to-311 request join is claimed.
  - Normalises boilerplate descriptions and assigns each text group to its first observed year.
  - Only labels genuinely observed in the text group's first year are retained, preventing future labels from moving backward into training.
  - One row per text-label pair remains.
  - Current valid split audit: 250,703 labelled rows → 593 unique normalised descriptions → 1,647 retained pairs; train 1,325, validation 149, test 173; zero cross-split text overlap.
  - TF-IDF predictions on full 311 data are now made once per unique narrative to reduce memory use.
- `src/absa/train_deduplicated_transformer.py`
  - Uses the exact same deduplicated 2023/2024/2025 split.
  - Selects the best epoch by validation macro-F1.
  - Active rerun uses inverse-frequency class weighting from the training split.
- `src/absa/build_evaluation_summary.py`
  - Produces one common-split rule/TF-IDF/DistilBERT table and figure.
- Current strict baseline results (valid and reusable):
  - Rule macro-F1: **0.1668**
  - TF-IDF macro-F1: **0.1420**
  - The older duplicate-heavy claim that TF-IDF/DistilBERT strongly outperformed the rule baseline must not be reused.

### Statistical wording and common robustness recipe

- `src/models/train_predictive.py`
  - Added a shared `make_lightgbm(seed)` recipe.
- `src/models/robustness_analysis.py`
  - Uses the lagged dataset and the exact primary LightGBM recipe.
  - Runs five seeds and 2,000 bootstrap resamples.
  - Bootstraps the mean prediction across seeds.
  - Reports borough and service subgroup metrics.
- `src/models/train_lagged_predictive.py`
  - Saves p-values from paired tests of **absolute cell prediction errors**.
  - The manuscript/report builders explicitly state that these p-values are not direct significance tests of Delta R-squared.

### Repeat-rate validity and sensitivity

- `src/outcomes/calculate_outcomes.py`
  - Repeat groups now include borough, complaint type, and cleaned incident address. This prevents identical street names in different boroughs from being linked.
- `src/outcomes/repeat_sensitivity.py`
  - Reports all-request, Heat/Hot Water, housing-service proxy, exclusion, and high-volume borough-address sensitivity.
  - Explicitly states that no authoritative building-type field is present.
- Existing outcome metrics were generated from the intermediate 3.23M extract and **must be regenerated after the final 4.21M case-normalised download**.

### Dashboard ranking evidence

- `src/models/evaluate_priority_ranking.py`
  - Builds held-out one-month-ahead rankings.
  - Reports Precision@k, lift over random, and NDCG@k.
- `dashboard/app.py`
  - Dark mode only.
  - Municipal and resident views retained.
  - Municipal queue loads held-out predictions when available.
  - Model evidence reads lagged primary results and displays Priority Precision@k.
  - Removed duplicate old function definitions and fixed the repeat-target JSON key.

### Reproducibility and paper infrastructure

- Added `CITATION.cff`.
- Added `.zenodo.json`.
- Added `REPRODUCIBILITY.md`.
- Added `scripts/build_reproducibility_archive.py`.
- Added `scripts/build_final_report.py`, which regenerates `reports/FINAL_PROJECT_REPORT.md` directly from saved JSON metrics.
- Heavily revised `scripts/build_journal_manuscript.py`:
  - Correct corresponding-author asterisk on Sanidhya Bhandari.
  - Dynamic counts and metrics instead of stale hard-coded values.
  - Lagged primary framing.
  - Train-only topic wording.
  - Common-split ABSA description.
  - Correct paired-error significance wording.
  - Best structured vs. best augmented comparison.
  - Repeat sensitivity.
  - AI-use declaration.
  - Data-availability statement for the prepared archive and pending DOI.
  - Output path: `outputs/Citizen_Sentiment_Analysis_Journal_Manuscript_Second_Level_Corrected.docx`.
- A real DOI has **not** been minted. Uploading the prepared archive to Zenodo requires an author-owned account. Do not invent a DOI.

## 3. Tests already added and passing

New/updated tests cover:

- Target-month lag alignment.
- Missing-next-month exclusion.
- Duplicate text and future-label leakage.
- Precision@k logic.
- Borough-aware repeat detection.
- Dashboard loading of lagged metrics and held-out ranking evidence.

The most recent focused run passed **11/11 tests**:

```powershell
venv\Scripts\python.exe -m pytest tests\test_dashboard_contract.py tests\test_outcomes.py tests\test_lagged_forecasting.py tests\test_leakage_and_ranking.py -q -p no:cacheprovider
```

Run the full suite after all final artifacts are rebuilt.

## 4. Artifacts that are currently stale

Do not report numbers from these until the final case-normalised download and pipeline rerun are complete:

- `reports/metrics/vader_metrics.json`
- `reports/metrics/topic_coherence.json`
- `reports/metrics/outcomes_summary.json`
- `reports/metrics/repeat_rate_sensitivity.json`
- `reports/metrics/integration_summary.json`
- `reports/metrics/predictive_modeling_results.json`
- `reports/metrics/lagged_predictive_modeling_results.json`
- `reports/metrics/robustness_results.json`
- `reports/metrics/priority_ranking_metrics.json`
- Most `data/processed/*.parquet` files except `absa_deduplicated_split.parquet`
- `reports/FINAL_PROJECT_REPORT.md`
- `PROGRESS.md`
- The README phase/status table and old snapshot wording
- Any previously generated manuscript DOCX

## 5. Required remaining execution order

After `data/raw/nyc311_raw.parquet.part` disappears and the final download reports success, run these sequentially to control memory:

```powershell
venv\Scripts\python.exe -u src\data\eda.py --config configs\config.yaml
venv\Scripts\python.exe -u src\sentiment\vader_baseline.py --config configs\config.yaml
venv\Scripts\python.exe -u src\topics\train_topics.py --config configs\config.yaml
venv\Scripts\python.exe -u src\absa\absa_pipeline.py --config configs\config.yaml
```

If the active weighted Transformer finished successfully, do not retrain it. Otherwise run:

```powershell
venv\Scripts\python.exe -u src\absa\train_deduplicated_transformer.py --epochs 4 --batch-size 16 --max-length 64
```

Then:

```powershell
venv\Scripts\python.exe -u src\absa\build_evaluation_summary.py
venv\Scripts\python.exe -u src\outcomes\calculate_outcomes.py --config configs\config.yaml
venv\Scripts\python.exe -u src\outcomes\repeat_sensitivity.py
venv\Scripts\python.exe -u src\outcomes\aggregate_integration.py --config configs\config.yaml
venv\Scripts\python.exe -u src\models\train_predictive.py --config configs\config.yaml
venv\Scripts\python.exe -u src\models\train_lagged_predictive.py --config configs\config.yaml
venv\Scripts\python.exe -u src\models\robustness_analysis.py
venv\Scripts\python.exe -u src\models\evaluate_priority_ranking.py
venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

## 6. Mandatory post-run audits

### Raw data coverage

```powershell
venv\Scripts\python.exe -c "import pandas as pd; d=pd.read_parquet(r'data/raw/nyc311_raw.parquet',columns=['created_date','complaint_type']); x=pd.to_datetime(d.created_date); print(len(d)); print(x.dt.to_period('M').value_counts().sort_index()); print(d.complaint_type.str.upper().value_counts().head(25))"
```

Confirm:

- Final cleaned count is near but slightly below the server count of 4,205,256 because invalid timestamps are removed.
- Exactly 24 months appear from 2023-01 through 2024-12.
- Uppercase housing services have realistic counts; Heat/Hot Water must no longer be approximately 1,455 rows.

### Model/result audit

- Verify `lagged_predictive_modeling_results.json` has all 12 months of 2024 represented through target-month splitting.
- Identify the strongest structured and strongest augmented test model for each target; do not report only the validation-selected LightGBM.
- Describe p-values only as paired tests of absolute cell errors.
- Verify `robustness_results.json` says `one_month_lagged_primary_recipe_lightgbm_robustness`.
- Verify ABSA cross-split overlap counts are all zero.
- Verify topic metrics report `test_period_text_used_for_fit: false` for both LDA and BERTopic.
- Verify repeat sensitivity uses borough-address keys.
- Verify Precision@k appears in both the JSON and dashboard.

## 7. Final documentation sequence

Regenerate dynamic reports only after every metric JSON is final:

```powershell
venv\Scripts\python.exe scripts\build_final_report.py
venv\Scripts\python.exe scripts\build_journal_manuscript.py
venv\Scripts\python.exe scripts\build_reproducibility_archive.py
```

Then manually update:

- `PROGRESS.md` with final counts, metrics, test total, and correction history.
- `README.md` phase table, final data horizon, Team 16 wording, and final primary results.

Run the dashboard and check it locally:

```powershell
venv\Scripts\streamlit.exe run dashboard\app.py --server.port 8501 --server.headless true
```

## 8. DOCX visual verification requirement

The final manuscript must be rendered and visually inspected before delivery. Use the document skill workflow and render every page. Previous attempts in this environment encountered missing `pdf2image`, unavailable LibreOffice, and intermittent Word COM logon-session failures. Try, in order:

1. The document skill's `render_docx.py` after confirming its dependencies.
2. Microsoft Word COM export to PDF if Word automation is available.
3. LibreOffice headless conversion if installed.

Inspect page images for clipped tables, blank pages, missing figures, broken symbols, header/footer issues, and table overflow. Do not deliver an unrendered DOCX without explicitly disclosing that visual QA could not be completed.

## 9. Remaining external action

The only correction that cannot be completed locally is minting a DOI. After the archive is generated:

1. Upload `outputs/team16_reproducibility_archive.zip` to an author-owned Zenodo account.
2. Publish the record.
3. Add the assigned DOI to `CITATION.cff`, `.zenodo.json`, `README.md`, and the manuscript data-availability statement.

Do not fabricate or use a placeholder DOI in the submitted paper.

