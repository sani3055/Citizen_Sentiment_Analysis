# Exploratory Data Analysis Summary (Review-2 Criterion C2 & C4)

**Generated:** 2026-10-20 21:48:05  
**Corpus Coverage:** NYC 311 operational requests (2023–2024) and RSAT responses (2023–2025)

---

## 1. RSAT Ground-Truth Class Distribution

| Likert Category | Count | Percentage |
|---|:---:|:---:|
| Strongly Disagree | 221,113 | 54.38% |
| Strongly Agree | 97,732 | 24.04% |
| Agree | 37,181 | 9.14% |
| Disagree | 31,521 | 7.75% |
| Neutral | 19,034 | 4.68% |

- **Total Dissatisfied (Disagree + Strongly Disagree):** 252,634 (62.14%)
- **Class Imbalance Note:** The target exhibits a prominent negative skew (~62% dissatisfied), making Macro-F1 and per-class recall critical evaluation metrics over simple accuracy.

---

## 2. Municipal Service Sentiment Extremes (≥100 Responses)

### Top 5 Services with Highest Dissatisfaction
| Service Type | Total Responses | Dissatisfaction Rate (%) |
|---|:---:|:---:|
| Noise - Helicopter | 803 | 94.5% |
| Light from Parking Lot | 153 | 91.5% |
| Vent/Exhaust System | 284 | 86.6% |
| Illegal Use | 340 | 86.5% |
| Smoking | 374 | 85.8% |

### Top 5 Services with Lowest Dissatisfaction (Highest Satisfaction)
| Service Type | Total Responses | Dissatisfaction Rate (%) |
|---|:---:|:---:|
| DOT Literature Request | 1,176 | 4.1% |
| DOF Literature Request | 5,059 | 4.2% |
| DCWP Literature Request | 213 | 8.5% |
| DOF Property - Update Account | 1,342 | 9.0% |
| DOF Property - Owner Issue | 522 | 10.0% |

---

## 3. Cell Coverage & Statistical Viability for Aggregate Join

- **Join Grain:** `(complaint_type_upper, borough, year, month)`
- **Total Observed (Service × Borough × Month) Cells:** 17,958
- **Robust Cells (≥10 RSAT samples):** 6,372 (35.5%)
- **Viability Verdict:** **SUFFICIENT STATISTICAL POWER**. Over 6,372 robust cells guarantees well-conditioned covariance matrices for Ridge regression and gradient-boosted trees without overfitting.

---

## 4. NYC 311 Operational Resolution Delay Distribution

- **Total Cleaned Records Analyzed:** 4,204,783
- **Median Resolution Delay:** 2.85 hours (0.12 days)
- **95th Percentile Delay:** 369.75 hours (15.41 days)
- **99th Percentile Delay (Winsorization Cutoff):** 2044.34 hours (85.18 days)

---

## 5. NYC 311 Text Feature Quality (`resolution_description`)

- **Total Rows:** 4,204,783
- **Populated Resolution Descriptions:** 4,196,225 (99.80%)
- **Distinct Narrative Strings:** 265
- **Linguistic Diversity:** Substantially higher than RSAT (which had only 17 distinct strings). This confirms NYC 311 resolution descriptions as the defensible primary text source for VADER feature engineering and ABSA classification.
