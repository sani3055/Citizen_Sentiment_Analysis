# NYC Open Data Ingestion & Quality Report (Review-2 Criterion C2)

**Generated:** 2026-10-20 21:46:23  
**Target Windows:** RSAT 2023–2025; operational NYC 311 extract 2023–2024  
**Data Sources:**
- NYC 311 Resolution Satisfaction Survey (RSAT): `5ijn-vbdv`
- NYC 311 Service Requests: `erm2-nwe9`

---

## 1. Summary Counts & Schema Health

| Dataset | Verified Row Count | Required Schema Validated | Date Range | Primary Key Fill Rate |
|---|:---:|:---:|:---:|:---:|
| **RSAT Raw** | 406,581 | PASSED (6/6 core cols) | 2023–2025 (months 1–12) | 100.0% |
| **NYC 311 Closed** | 4,204,783 | PASSED (5/5 core cols) | 2023-01-01 to 2024-12-31 | 100.0% |

---

## 2. RSAT Ground-Truth Sentiment Polarity Distribution

| Satisfaction Category | Total Count | Percentage | Research Mapping |
|---|:---:|:---:|---|
| Strongly Disagree | 221,113 | 54.38% |
| Strongly Agree | 97,732 | 24.04% |
| Agree | 37,181 | 9.14% |
| Disagree | 31,521 | 7.75% |
| Neutral | 19,034 | 4.68% |

---

## 3. RSAT Ground-Truth Dissatisfaction Aspects (Top Reasons)

| Aspect / Grievance Statement | Count | % of RSAT Total |
|---|:---:|:---:|
| nan | 154,395 | 37.97% |
| The Agency did not correct the issue. | 107,990 | 26.56% |
| Other | 81,700 | 20.09% |
| The Agency did not correct the issue and this Service Request should be reopened. | 31,259 | 7.69% |
| Status updates were unhelpful, inaccurate, incomplete, and/or confusing. | 18,246 | 4.49% |
| The Agency corrected the issue, but they took too long to respond. | 4,545 | 1.12% |
| The Agency said I did not provide complete or accurate information, but I did. | 3,554 | 0.87% |
| The Agency did not provide enough status updates. | 2,692 | 0.66% |
| The Agency corrected the issue, but the work they did was unsatisfactory. | 2,200 | 0.54% |

---

## 4. Geographic Distribution Across Boroughs

| Borough | RSAT Survey Responses | NYC 311 Service Requests |
|---|:---:|:---:|
| BRONX | 60,433 | 953,064 |
| BROOKLYN | 142,797 | 1,320,746 |
| MANHATTAN | 79,246 | 794,280 |
| QUEENS | 105,121 | 1,003,978 |
| STATEN ISLAND | 18,984 | 132,715 |

---

## 5. NYC 311 Narrative Text Quality (Primary NLP Feature Source)

- **Total 311 Closed Records Analyzed:** 4,204,783
- **Resolution Description Fill Count:** 4,196,225 (99.8%)
- **Distinct Resolution Narrative Strings:** 265
- **Average Character Length:** 140.5 characters
- **Median Character Length:** 101.0 characters

---

## 6. Data Integrity & Feasibility Assertions

- [x] All RSAT records possess non-null, valid NYC Borough mappings.
- [x] All RSAT satisfaction ratings strictly match valid 5-point Likert categories.
- [x] All NYC 311 records have verified non-null `closed_date`.
- [x] Temporal constraint strictly enforced: `created_date <= closed_date` (zero negative delays).
- [x] Case normalization verified: `complaint_type.str.upper()` ready for multi-source aggregate join.
