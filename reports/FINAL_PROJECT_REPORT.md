# Final Project Report — Team 16

**Project:** Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP  
**Course:** BCSE316L — Design of Smart Cities  
**Institution:** Vellore Institute of Technology, Vellore  
**Team:** 16  
**Members:** Taher Panbiharwala (23BCT0028), Sanidhya Bhandari (23BCT0209), Chinmoy Deb (23BCT0050)  
**Faculty guide:** Dr. Kalaavathi B  
**Updated:** 29 October 2026

## 1. Research question and corrected design

This project asks whether sentiment, topic, grievance-aspect, and satisfaction signals add out-of-time predictive information for municipal resolution delay and repeat requests after service identity, borough, season, and request volume are controlled. The primary design uses features observed in month *t* to predict outcomes for the same service and borough in month *t+1*. Same-month models are retained only as a secondary monitoring analysis. The results are predictive associations and do not establish causality.

All operational performance claims are limited to the selected NYC services and boroughs on the January–December 2024 target horizon. The final-review feature-selection and fixed-cutoff ranking extensions are exploratory analyses of an already examined test year, not independent confirmatory replications.

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
- Code, configurations, tests, processed cell tables, metrics, and figures are packaged for Zenodo deposition. A DOI must be assigned through an author-owned Zenodo account.

## 4. NLP evaluation

### 4.1 VADER baseline

VADER was evaluated on 1,747 robust cells. Accuracy was 0.6846, macro-F1 was 0.2750, and negative-class F1 was 0.8138. The difference between matched VADER cells and modelled cells is expected: VADER evaluation requires an RSAT cell with at least ten survey responses, while outcome modelling additionally requires all feature tables, an operational outcome cell, lag alignment, and an assigned temporal split.

The declared three-label macro-F1 averages Negative (0.8138), Neutral (0.0000), and Positive (0.0113) with equal weight and `zero_division=0`. Neutral has zero ground-truth support but remains in the explicit label list. This is not a two-class macro-F1.

### 4.2 Topic models

LDA used 10 topics and achieved C_v coherence 0.4675. BERTopic identified 14 non-outlier clusters. Both were fitted on 2023-01 through 2023-07; test-period text used for fitting is `False`.

### 4.3 Duplicate-controlled ABSA

The source contains 250,703 labelled RSAT rows but only 593 normalised descriptions and 1,647 retained text-label pairs. Cross-split normalised-text overlap is zero.

| Model | Test records | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| Rule baseline | 173 | 0.3237 | 0.1668 |
| TF-IDF logistic regression | 173 | 0.2081 | 0.1420 |
| DistilBERT | 173 | 0.2254 | 0.1191 |

These results measure classification of privacy-limited agency narratives against standardised survey reasons. They are not a human-annotated evaluation of citizen free text.

DistilBERT and TF-IDF both underperform the rule baseline. Uniform-guess accuracy of 1/6 is not an established macro-F1 chance benchmark on this imbalanced test set; no at/below-chance claim is made from that number.

## 5. Operational outcomes and repeat sensitivity

Across 4,204,783 valid requests, median raw delay was 2.85 hours, the 95th percentile was 369.75 hours, and the 99th-percentile winsorisation cap was 2044.34 hours. Repeat rates were 40.02% at 7 days, 46.27% at 14 days, and 52.89% at 30 days.

Heat/Hot Water accounts for 17.89% of all 14-day repeat flags; excluding it gives a repeat rate of 43.04%. The broader housing-service proxy accounts for 24.40% of repeat flags; excluding those services gives 45.74%. High-volume borough-address groups account for 90.41% of repeat flags. The public extract has no authoritative building-type field, so these are sensitivity proxies rather than verified multi-unit-building classifications.

## 6. Primary one-month-ahead predictive results

The lagged integrated table contains 1,885 cells: 578 training, 313 validation, and 994 held-out 2024 test cells.

| Target | Algorithm | Baseline R² | Augmented R² | ΔR² | Baseline MAE | Augmented MAE | Paired-error p |
|---|---|---:|---:|---:|---:|---:|---:|
| Delay (hours) | Ridge | 0.5840 | 0.5743 | -0.0096 | 63.7310 | 66.0898 | 0.00782 |
| Delay (hours) | RandomForest | 0.5553 | 0.4591 | -0.0962 | 57.0139 | 62.1412 | 0.1015 |
| Delay (hours) | LightGBM | 0.5995 | 0.4730 | -0.1264 | 56.1839 | 60.2874 | 0.1363 |
| Repeat rate (14d) | Ridge | 0.9128 | 0.8970 | -0.0158 | 0.0395 | 0.0414 | 0.004727 |
| Repeat rate (14d) | RandomForest | 0.9097 | 0.9165 | +0.0068 | 0.0409 | 0.0354 | 1.198e-07 |
| Repeat rate (14d) | LightGBM | 0.9224 | 0.9241 | +0.0017 | 0.0370 | 0.0354 | 0.05281 |

The p-values are from two-sided paired tests of per-cell absolute prediction errors. They are not direct significance tests of ΔR². Model selection uses validation R², and the strongest structured and augmented test models are reported even when they differ from the validation-selected algorithm. Therefore, any claim about NLP improvement is algorithm-specific unless an augmented model also exceeds the strongest structured baseline.

### 6.1 Persistence and individual feature families

| Target | Last-value R² | Seasonal-naive R² | Structured LightGBM R² | All-family R² |
|---|---:|---:|---:|---:|
| Delay | 0.8839 | 0.4625 | 0.5995 | 0.4730 |
| Repeat rate | 0.9469 | 0.9022 | 0.9224 | 0.9241 |

| Target | Added family | R² | ΔR² vs structured |
|---|---|---:|---:|
| Delay | VADER | 0.3644 | -0.2350 |
| Delay | topics | 0.6116 | +0.0122 |
| Delay | ABSA | 0.6420 | +0.0425 |
| Delay | RSAT satisfaction | 0.6101 | +0.0106 |
| Repeat rate | VADER | 0.8955 | -0.0269 |
| Repeat rate | topics | 0.9273 | +0.0048 |
| Repeat rate | ABSA | 0.8726 | -0.0498 |
| Repeat rate | RSAT satisfaction | 0.9224 | -0.0001 |

Topics, ABSA, and RSAT individually improve delay R², while VADER reduces it sharply. The all-family drop is therefore a feature-bundle failure, not a general demonstration that language cannot help. Repeat-rate R² near 0.92 is not an established modelling gain: persistence is stronger, and high-volume addresses account for 90.41% of observed repeat flags. This does not causally decompose the R² into persistence and address effects.

### 6.2 Exploratory validation-selected augmentation

All eight subsets of topics, ABSA, and RSAT, including no added family, are scored on September–December 2023 validation after training on February–August 2023 targets. VADER is excluded. Maximum validation R² determines the chosen subset, with fewer columns on an exact tie. The subset is refitted on train plus validation before the NYC-2024 evaluation.

| Target | Added families | Validation R² | 2024 R² | ΔR² vs structured | MAE |
|---|---|---:|---:|---:|---:|
| Delay | ABSA + RSAT | 0.7144 | 0.6228 | +0.0233 | 53.5087 |
| Repeat rate | None | 0.9037 | 0.9224 | +0.0000 | 0.0370 |

The seed-42 delay model retains ABSA + RSAT and gains +0.0233 R², with paired absolute-error p = 0.1087. Its five-seed gain is +0.0214 ± 0.0068; a 2,000-resample paired cell-bootstrap interval on seed-mean predictions is [-0.0263, +0.0762]. The interval includes zero and does not account for service/borough clustering. The all-non-VADER reference reaches delay R² 0.6115 and repeat R² 0.9240. Validation selects structured features alone for repeat rate; zero ΔR² then follows from model identity, not equivalence evidence between distinct models. No selected model beats persistence. This post-review extension reuses a previously examined test horizon and is exploratory.

## 7. Original all-family robustness and uncertainty

For delay, the five-seed mean ΔR² is -0.1396 ± 0.0158; the 2,000-resample 95% interval is [-0.2282, -0.0402]. For repeat rate, the corresponding mean is -0.0008 ± 0.0017, with interval [-0.0070, +0.0060]. Borough- and service-level MAE results are stored in `robustness_results.json`.

## 8. Dashboard ranking validity

The municipal queue combines 45% predicted delay rank, 35% predicted repeat rank, and 20% lagged dissatisfaction rank. Held-out ranking performance is:

| k | Raw hits | Precision@k | Lift (rescaled P@k) | NDCG@k |
|---:|---:|---:|---:|---:|
| 10 | 1/10 | 0.100 | 9.94 | 0.859 |
| 20 | 3/20 | 0.150 | 7.46 | 0.876 |
| 99 | 48/99 | 0.485 | 4.87 | 0.898 |
| 199 | 108/199 | 0.543 | 2.71 | 0.907 |

Strict top-k relevance has prevalence k/N, so lift = Precision@k × N/k. The original 9.94-fold lift is therefore a rescaling of 1/10 hits, not independent evidence of a strong queue. Top-20 overlap is only 3/20. Continuous NDCG is a graded-score statistic and does not contradict low extreme-cell overlap.

For a separate fixed relevance definition, delay and repeat are mapped to percentiles of February–August 2023 training outcomes. A 55% delay / 45% repeat burden score uses the training 80th-percentile cutoff (61.9031), frozen across k and 2024. It identifies 202/994 relevant cells (20.32% prevalence).

| k | Raw hits | Fixed-cutoff precision | Recall | Lift vs fixed prevalence |
|---:|---:|---:|---:|---:|
| 10 | 9/10 | 0.900 | 0.045 | 4.43 |
| 20 | 18/20 | 0.900 | 0.089 | 4.43 |
| 99 | 69/99 | 0.697 | 0.342 | 3.43 |
| 199 | 111/199 | 0.558 | 0.550 | 2.74 |

This broader screen is not directly comparable to top-k overlap and is not a validated municipal standard. At k=10 it finds 9/10 qualifying cells but only 4.46% of all 202 relevant cells. Neither definition establishes an advantage over a persistence-ranked queue or staff decisions.

The dashboard also contains a resident-facing historical view. It displays aggregate statistics only and must not be used for individual-level decisions.

## 9. Limitations

1. Agency-authored closure text is not equivalent to citizen free text.
2. ABSA labels are standardised survey reasons, and heavy boilerplate leaves a small number of genuinely distinct texts.
3. The study covers one city and one two-year operational period; cross-city transfer remains untested.
4. Repeat flags are operational recurrence proxies, not proof that the same resident or underlying incident returned.
5. Address concentration is observable, but verified building type is not available in the selected public fields.
6. Paired cell-error tests do not remove dependence among cells sharing a service or borough.
7. A public DOI is pending author upload to Zenodo.
8. Final-review feature-selection and ranking-cutoff extensions are exploratory and need an independent later-year or cross-city confirmation.

## 10. Deliverables

- Dark-mode Streamlit municipal and resident dashboard.
- Complete Socrata ingestion with atomic streaming and row-count verification.
- Train-only LDA/BERTopic features and duplicate-controlled ABSA models.
- Lagged primary forecasting, contemporaneous secondary monitoring, five-seed robustness, bootstrap intervals, and Precision@k.
- Automated tests, `CITATION.cff`, `.zenodo.json`, `REPRODUCIBILITY.md`, and a compact repository archive.

## 11. Conclusion

The project identifies feature-specific effects and limitations in NYC-2024 rather than a universal positive or negative verdict on language features. Excluding VADER and validation-selecting ABSA + RSAT gives a modest, uncertain delay gain over structured LightGBM, while persistence remains stronger and repeat selection retains no added family. DistilBERT underperforms the rule classifier. Ranking usefulness depends strongly on the definition of relevance. Public code and reproducibility artifacts support checking these exploratory findings; a permanent DOI remains pending author publication.
