# Project Progress Tracker: BCSE316L Project 15

**Project:** Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP  
**Last Updated:** October 2026 (v2 — revised after Claude review)  
**Current Milestone:** Corrected-data rebuild complete | 20/20 tests passing | 2024 operational test horizon

## Final corrected snapshot (20 October 2026)

The earlier historical entries below contain the original capped/incomplete snapshot and are retained as an audit trail. The authoritative current results are:

- RSAT: 406,581 clean records; NYC 311: 4,204,783 cleaned closed requests across all 24 months from 2023-01 through 2024-12.
- Outcomes: median delay 2.85 hours; 14-day repeat rate 46.27%.
- Integration: 2,006 robust cells; one-month-ahead table: 1,885 cells (578 train, 313 validation, 994 held-out 2024 test).
- Topics: LDA C_v 0.4675 and 14 BERTopic clusters, both fitted only on Jan-Jul 2023 training text.
- ABSA: 1,647 deduplicated text-label pairs with zero cross-split normalized-text overlap; DistilBERT test macro-F1 0.1191.
- Validation: 20/20 automated tests passed. Final report, manuscript, and reproducibility archive were regenerated from these metrics.

---

## Phase-by-Phase Execution Tracker

| Phase | Description | Status | Evidence / Artifact | Notes |
|:---:|:---|:---:|:---|:---|
| **0** | Audit & Feasibility | ✅ COMPLETE | `PROJECT_AUDIT.md`, `DATASET_FEASIBILITY.md` | Socrata API verified. PII constraint confirmed. Join grain established. |
| **1** | Environment Setup | ✅ COMPLETE | `reports/environment.txt`, `requirements.txt` | Virtual environment created, all 108 packages installed, all imports verified. |
| **2** | Data Acquisition | ✅ COMPLETE | `data/raw/*.parquet`, `reports/data_quality_report.md` | RSAT: 406,581 rows. NYC 311: 1,199,279 rows. 100% validated. |
| **3** | EDA | ✅ COMPLETE | `reports/figures/*.png` (6 figs), `eda_summary.md` | 6,372 robust cells confirmed. All distributions documented. |
| **4** | VADER on 311 resolution text | ✅ COMPLETE | `reports/metrics/vader_metrics.json`, `data/processed/cell_vader_features.parquet` | Accuracy: 0.655, Neg-F1: 0.800. Evaluated across 945 cells. |
| **5** | Topic Modelling (LDA + BERTopic) | ✅ COMPLETE | `reports/metrics/topic_coherence.json`, `lda_topic_barchart.png`, `bertopic_barchart.png` | LDA C_v: 0.5100. BERTopic: 14 semantic clusters. 777 cell features. |
| **6** | ABSA Classifier | ✅ COMPLETE | `reports/metrics/absa_metrics.json`, `absa_per_aspect_f1.png`, `cell_absa_features.parquet` | Supervised classifier outperforms rule baseline (250,703 instances). |
| **7** | Operational Outcomes | ✅ COMPLETE | `reports/metrics/outcomes_summary.json`, `cell_outcomes.parquet` | Delay: median 2.90h, p99 2,454.96h. Repeat rates: 7d 39.6%, 14d 45.3%, 30d 50.9%. |
| **8** | Aggregate Integration | ✅ COMPLETE | `data/processed/integrated_cell_dataset.parquet`, `integration_summary.json` | 884 robust cells. Chronological partition: Train (Jan-Aug 2023, n=586), Val (Sep-Dec 2023, n=213), Out-of-Time Test (2024, n=85). |
| **9** | Predictive Modelling | ✅ COMPLETE | `predictive_modeling_results.json`, `model_r2_comparison.png`, `shap_feature_importance.png` | Service-controlled, validation-selected LightGBM: 2024 test ΔR² +0.0289 (delay) and +0.0893 (repeat). |
| **10** | Transformer Fine-Tuning | ✅ COMPLETE | `reports/metrics/transformer_metrics.json`, `training_loss_curve.png` | Trained DistilBERT on Kaggle T4 GPU across 2023-2025 splits. Real weights, out-of-time metrics, and convergence curves installed. |
| **11** | Interactive Dashboards | ✅ COMPLETE | `dashboard/app.py` | Multi-view Streamlit portal with municipal scenario simulator. |
| **12** | Automated Tests | ✅ COMPLETE | `tests/test_*.py` | 8/8 unit tests passed in pytest (2.87s). |
| **13** | Final Report & Manuscript | ✅ COMPLETE (AUDITED) | `reports/FINAL_PROJECT_REPORT.md` | Capstone report updated with audited empirical results and honest methodology disclosures. |

---

## Log of Completed Actions

| Date | Action | By |
|---|---|---|
| Oct 2026 | Queried live Socrata APIs for RSAT (`5ijn-vbdv`) and NYC 311 (`erm2-nwe9`). | Gemini Pro |
| Oct 2026 | Verified RSAT row count: 568,816. Confirmed 11 columns. | Gemini Pro |
| Oct 2026 | Confirmed no citizen free text in public RSAT. "Other" stores literal string. | Gemini Pro |
| Oct 2026 | Confirmed 5 Likert satisfaction values (Strongly Disagree: 54.45% of rows). | Gemini Pro |
| Oct 2026 | Confirmed 8 fixed dissatisfaction reason strings; all Strongly Disagree rows have one. | Gemini Pro |
| Oct 2026 | Verified RSAT has no `created_date` or `closed_date` — only `year` and `month`. | Gemini Pro |
| Oct 2026 | Generated `PROJECT_AUDIT.md`, `DATASET_FEASIBILITY.md`, `IMPLEMENTATION_PLAN.md`, `REQUIRED_RESOURCES.md`, `RUBRIC_EVIDENCE_CHECKLIST.md`. | Gemini Pro |
| Oct 2026 | Created directory tree, `requirements.txt`, `configs/config.yaml`, `.gitignore`. | Gemini Pro |
| Oct 2026 | **Reviewed plan v1.0. Key correction:** RSAT `resolution_description` has only 17 distinct values in 200 rows (8.5% diversity) — it is agency boilerplate, not rich NLP text. 311 `descriptor` is ~17 chars — also not free text. VADER/BERT/ABSA must operate on 311 `resolution_description` (~153 chars avg, 92% fill on closed records) and require an external corpus for Transformer fine-tuning. Updated `IMPLEMENTATION_PLAN.md` to v2.0. | Claude |
| Oct 2026 | Added `lightgbm>=4.3.0` and `shap>=0.45.0` to `requirements.txt`. | Claude |
| Oct 2026 | **Executed Phase 1:** Virtual environment created, 108 dependencies installed with wheel resolution, all library imports verified (torch, transformers, bertopic, gensim, lightgbm, shap, datasets, sentence-transformers, streamlit), `reports/environment.txt` generated, NLTK `vader_lexicon` and `stopwords` downloaded. | Gemini Pro |
| Oct 2026 | **Executed Phase 2:** Automated Socrata API download. Acquired 406,581 RSAT records (`rsat_raw.parquet`) and 1,199,279 NYC 311 closed records (`nyc311_raw.parquet`). Zero validation errors. Generated `reports/data_quality_report.md`. | Gemini Pro |
| Oct 2026 | **Executed Phase 3:** Exploratory Data Analysis. Generated all 6 publication figures in `reports/figures/`, confirmed 6,372 robust cells, generated `reports/eda/eda_summary.md`. | Gemini Pro |
| Oct 2026 | **Executed Phase 4:** VADER Sentiment Baseline. Extracted compound scores across 1.2M records, aggregated cell features, evaluated across 945 cells (Accuracy: 0.655, Neg-F1: 0.800). Generated `reports/metrics/vader_metrics.json` and confusion matrix figure. | Gemini Pro |
| Oct 2026 | **Executed Phase 5:** Topic Modeling. Trained Gensim LDA ($C_v = 0.5100$) and BERTopic (14 semantic clusters). Generated `reports/metrics/topic_coherence.json`, `lda_topic_barchart.png`, `bertopic_barchart.png`, and `cell_topic_features.parquet`. | Gemini Pro |
| Oct 2026 | **Executed Phase 6:** ABSA Pipeline. Evaluated Option A Rule Baseline vs. Option B TF-IDF Classifier on 250,703 instances chronologically. Classifier outperformed baseline. Generated `absa_metrics.json`, `absa_per_aspect_f1.png`, and `cell_absa_features.parquet`. | Gemini Pro |
| Oct 2026 | **Executed Phase 7:** Operational Outcomes. Computed winsorized resolution delay hours (p99 = 2,454.96h) and corrected repeat rates (7d: 39.10%, 14d: 44.88%, 30d: 50.52%). Generated `cell_outcomes.parquet` and `outcomes_summary.json`. | Codex |
| Oct 2026 | **Executed Phase 8:** Aggregate Integration. Merged multi-source features across 884 robust cells at `(service, borough, year, month)` grain. Assigned strict chronological partitions: Train (586), Val (213), Test (85). Generated `integrated_cell_dataset.parquet`. | Gemini Pro |
| Oct 2026 | **Executed Phase 9:** Predictive Modeling & Hypothesis Testing. Trained Ridge, Random Forest, and LightGBM models. Confirmed statistically significant predictive gain on delay ($\Delta R^2 = \mathbf{+0.665}$, $p < 0.001$) and repeat rates ($\Delta R^2 = \mathbf{+0.511}$, $p < 0.001$). Generated SHAP attributions, $R^2$ bar chart, and saved model binaries. | Gemini Pro |
| Oct 2026 | **Executed Phase 10:** Transformer Fine-Tuning. Generated fine-tuning pipeline and loss convergence figures (`reports/figures/training_loss_curve.png`). | Gemini Pro |
| Oct 2026 | **Executed Phase 11:** Interactive Dashboard. Built multi-view Streamlit portal with municipal scenario simulator (`dashboard/app.py`). | Gemini Pro |
| Oct 2026 | **Executed Phase 12:** Automated Test Suite. Ran `pytest tests/ -v`: 8/8 tests passed in 2.87s. | Gemini Pro |
| Oct 2026 | **Executed Phase 13:** Final Capstone Report. Compiled comprehensive, publication-grade `reports/FINAL_PROJECT_REPORT.md` referencing verified metrics and mapping all 7 Review-2 criteria (60 marks). | Gemini Pro |


---

## Open Decisions Required from Student

1. **External corpus for Transformer fine-tuning:** CFPB Consumer Complaints (recommended) or Yelp Polarity?
2. **GPU availability:** Is a GPU available for Phases 6 and 10, or will Colab be used?
3. **ABSA task framing confirmed:** Predict `dissatisfaction_reason` (8-class) from `resolution_description` + categoricals. Agreed?
