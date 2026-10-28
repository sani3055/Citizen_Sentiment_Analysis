# Final Project Report — Team 16

**Project:** Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP  
**Course:** BCSE316L — Design of Smart Cities  
**Institution:** Vellore Institute of Technology, Vellore  
**Team:** 16  
**Members:** Taher Panbiharwala (23BCT0028), Sanidhya Bhandari (23BCT0209), Chinmoy Deb (23BCT0050)  
**Faculty guide:** Dr. Kalaavathi B  
**Updated:** 20 October 2026

## 1. Research question and final design

This project asks whether sentiment, topic, grievance-aspect, and satisfaction signals add out-of-time predictive information for municipal resolution delay and repeat requests after service identity, borough, season, and request volume are controlled. The primary design uses features observed in month *t* to predict outcomes for the same service and borough in month *t+1*. Same-month models are retained only as a secondary monitoring analysis. The results are predictive associations and do not establish causality.

For a consistent headline analysis, LightGBM is the primary algorithm for both outcomes and is used in the headline comparison, robustness analysis, SHAP interpretation, and dashboard evidence. Ridge and Random Forest remain comparison models.

## 2. Data provenance and coverage

| Source | Socrata ID | Clean records | Analytic period | Role |
|---|---:|---:|---|---|
| NYC 311 Resolution Satisfaction Survey | `5ijn-vbdv` | 406,581 | 2023–2025 | Satisfaction and standardised grievance labels |
| NYC 311 Service Requests | `erm2-nwe9` | 4,204,783 | 2023–2024 | Text, delay, repeat flags, volume |

The 311 extract uses paged Socrata retrieval, a server-side count check, case-normalised top-service matching, timestamp validation, and an explicit 24-month completeness check. All months from January 2023 through December 2024 are present. Monthly counts: 2023-01: 159,717, 2023-02: 149,791, 2023-03: 159,894, 2023-04: 152,300, 2023-05: 170,316, 2023-06: 162,272, 2023-07: 162,594, 2023-08: 166,033, 2023-09: 167,909, 2023-10: 192,225, 2023-11: 188,844, 2023-12: 177,734, 2024-01: 189,388, 2024-02: 158,639, 2024-03: 172,614, 2024-04: 166,183, 2024-05: 174,668, 2024-06: 183,972, 2024-07: 170,812, 2024-08: 168,307, 2024-09: 198,552, 2024-10: 195,301, 2024-11: 193,645, 2024-12: 223,073.

Public RSAT rows suppress unrestricted citizen commentary. NLP features therefore come from agency-authored `resolution_description` fields. RSAT and 311 are not joined at request level; they are integrated at service × borough × year × month grain.

## 3. Leakage and reproducibility controls

- LDA and BERTopic are fitted only on January–July 2023 training text. Later records are transformed with frozen models.
- The primary operational experiment lags all feature information by one month.
- ABSA examples use the `resolution_description` and `dissatisfaction_reason` fields found together in an RSAT row; no unsupported ticket-level join is claimed.
- Normalised boilerplate descriptions are assigned to their first observed year. Only labels observed in that first year are retained, preventing text or future labels from crossing splits.
- Rule, TF-IDF, and DistilBERT ABSA models use the same duplicate-controlled 2025 test set.
- Five-seed robustness and 2,000 bootstrap resamples use the exact primary LightGBM recipe.
- The primary LightGBM analysis is compared with last-value and 12-month seasonal-naive baselines; feature-family ablations are reported for VADER, topics, ABSA, and RSAT satisfaction.
- Code, configurations, tests, processed cell tables, metrics, and figures are packaged for Zenodo deposition. A DOI must be assigned through an author-owned Zenodo account.

## 4. NLP evaluation

### 4.1 VADER baseline

VADER was evaluated on 1,747 robust cells. Accuracy was 0.6846, macro-F1 was 0.2750, and negative-class F1 was 0.8138. The difference between matched VADER cells and modelled cells is expected: VADER evaluation requires an RSAT cell with at least ten survey responses, while outcome modelling additionally requires all feature tables, an operational outcome cell, lag alignment, and an assigned temporal split.

### 4.2 Topic models

LDA used 10 topics and achieved C_v coherence 0.4675. BERTopic identified 14 non-outlier clusters. Both were fitted on 2023-01 through 2023-07; test-period text used for fitting is `False`.

### 4.3 Duplicate-controlled ABSA

The source contains 250,703 labelled RSAT rows but only 593 normalised descriptions and 1,647 retained text-label pairs. Cross-split normalised-text overlap is zero. With six classes, uniform random macro-F1 is approximately 0.167; the observed results are at or below this level. ABSA features are therefore retained as a documented failure of agency boilerplate to provide a reliable proxy for citizen voice.

| Model | Test records | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| Rule baseline | 173 | 0.3237 | 0.1668 |
| TF-IDF logistic regression | 173 | 0.2081 | 0.1420 |
| DistilBERT | 173 | 0.2254 | 0.1191 |

These results measure classification of privacy-limited agency narratives against standardised survey reasons. They are not a human-annotated evaluation of citizen free text.

## 5. Operational outcomes and repeat sensitivity

Across 4,204,783 valid requests, median raw delay was 2.85 hours, the 95th percentile was 369.75 hours, and the 99th-percentile winsorisation cap was 2044.34 hours. Repeat rates were 40.02% at 7 days, 46.27% at 14 days, and 52.89% at 30 days.

Heat/Hot Water accounts for 17.89% of all 14-day repeat flags; excluding it gives a repeat rate of 43.04%. The broader housing-service proxy accounts for 24.40% of repeat flags; excluding those services gives 45.74%. High-volume borough-address groups account for 90.41% of repeat flags. The public extract has no authoritative building-type field, so these are sensitivity proxies rather than verified multi-unit-building classifications.

### RSAT count reconciliation

| Count | Meaning |
|---|---|
| Portal headline | All records shown by the public portal, including records outside the study period and rows that fail validation |
| 406,581 | Audited analytic responses remaining after study-period, borough, and Likert-value checks |

## 6. Primary one-month-ahead predictive results

The lagged integrated table contains 1,885 cells: 578 training, 313 validation, and 994 untouched 2024 test cells.

| Target | Algorithm | Baseline R² | Augmented R² | ΔR² | Baseline MAE | Augmented MAE | Paired-error p |
|---|---|---:|---:|---:|---:|---:|---:|
| Delay (hours) | Ridge | 0.5840 | 0.5743 | -0.0096 | 63.7310 | 66.0898 | 0.00782 |
| Delay (hours) | RandomForest | 0.5553 | 0.4591 | -0.0962 | 57.0139 | 62.1412 | 0.1015 |
| Delay (hours) | LightGBM | 0.5995 | 0.4730 | -0.1264 | 56.1839 | 60.2874 | 0.1363 |
| Repeat rate (14d) | Ridge | 0.9128 | 0.8970 | -0.0158 | 0.0395 | 0.0414 | 0.004727 |
| Repeat rate (14d) | RandomForest | 0.9097 | 0.9165 | +0.0068 | 0.0409 | 0.0354 | 1.198e-07 |
| Repeat rate (14d) | LightGBM | 0.9224 | 0.9241 | +0.0017 | 0.0370 | 0.0354 | 0.05281 |

The p-values are from two-sided paired tests of per-cell absolute prediction errors. They are not direct significance tests of ΔR². A negative ΔR² or higher augmented MAE means that the augmented model performed worse. The primary LightGBM comparison is used consistently in the headline, robustness, SHAP, and dashboard analyses. The strongest structured benchmark is the last-value baseline for both outcomes, so the language/satisfaction features do not establish improvement over persistence.

### 6.1 Naive baselines and feature-family ablations

| Target | Last-value R² | Seasonal-naive R² | Structured LightGBM R² | All-feature LightGBM R² |
|---|---:|---:|---:|---:|
| Mean delay (hours) | 0.8839 | 0.4625 | 0.5995 | 0.4730 |
| Repeat rate (14d) | 0.9469 | 0.9022 | 0.9224 | 0.9241 |

The last-value baseline uses the previous month's observed outcome for the same service-borough cell. The seasonal-naive baseline uses the same calendar month from the previous year, with aggregate fallback when an exact cell is absent. Feature-family ablations are saved in `reports/metrics/review_corrections_results.json`: for delay, topics (+0.0122 ΔR²) and ABSA (+0.0425) were the only positive single-family additions, while VADER reduced R² by 0.2350; for repeat rate, topics added 0.0048, while VADER and ABSA reduced R².

## 7. Robustness and uncertainty

For delay, the five-seed mean ΔR² is -0.1396 ± 0.0158; the 2,000-resample 95% interval is [-0.2282, -0.0402]. For repeat rate, the corresponding mean is -0.0008 ± 0.0017, with interval [-0.0070, +0.0060]. Borough- and service-level MAE results are stored in `robustness_results.json`.

## 8. Dashboard ranking validity

The municipal queue combines 45% predicted delay rank, 35% predicted repeat rank, and 20% lagged dissatisfaction rank. Held-out ranking performance is:

| k | Precision@k | Lift over random | NDCG@k |
|---:|---:|---:|---:|
| 10 | 0.100 | 9.94 | 0.859 |
| 20 | 0.150 | 7.46 | 0.876 |
| 99 | 0.485 | 4.87 | 0.898 |
| 199 | 0.543 | 2.71 | 0.907 |

The dashboard also contains a resident-facing historical view. It displays aggregate statistics only and must not be used for individual-level decisions.

The queue metrics are included in the manuscript because dashboard usefulness is evaluated separately from outcome prediction. Precision@10 is 0.100 with 9.94 lift and NDCG@10 of 0.859; Precision@20 is 0.150 with 7.46 lift and NDCG@20 of 0.876.

## 9. Limitations

1. Agency-authored closure text is not equivalent to citizen free text.
2. ABSA labels are standardised survey reasons, and heavy boilerplate leaves a small number of genuinely distinct texts.
3. The study covers one city and one two-year operational period; cross-city transfer remains untested.
4. Repeat flags are operational recurrence proxies, not proof that the same resident or underlying incident returned.
5. Address concentration is observable, but verified building type is not available in the selected public fields.
6. Paired cell-error tests do not remove dependence among cells sharing a service or borough.
7. A public DOI is pending author upload to Zenodo.

## 10. Deliverables

- Dark-mode Streamlit municipal and resident dashboard.
- Complete Socrata ingestion with atomic streaming and row-count verification.
- Train-only LDA/BERTopic features and duplicate-controlled ABSA models.
- Lagged primary forecasting, contemporaneous secondary monitoring, five-seed robustness, bootstrap intervals, and Precision@k.
- Automated tests, `CITATION.cff`, `.zenodo.json`, `REPRODUCIBILITY.md`, and a compact repository archive.

## 11. Conclusion

The project is a reproducible test of whether privacy-safe language and satisfaction signals improve future aggregate municipal-outcome prediction. The held-out results support a careful negative or near-null conclusion: the augmented model does not beat the strongest last-value benchmark, although selected feature families provide limited signal within some learned models. Conclusions therefore report signed effect sizes, paired-error significance accurately, and retain the documented privacy, domain-transfer, and dependence limitations.
