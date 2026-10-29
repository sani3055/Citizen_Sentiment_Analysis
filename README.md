# Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP

[![Project Status](https://img.shields.io/badge/Status-Research%20pipeline%20complete-brightgreen)]()
[![Course](https://img.shields.io/badge/Course-BCSE316L%20Design%20of%20Smart%20Cities-blue)]()
[![Institution](https://img.shields.io/badge/Institution-VIT%20Vellore-orange)]()
[![SDG Alignment](https://img.shields.io/badge/SDG-11%20%7C%2016-yellowgreen)]()

An end-to-end, reproducible research project investigating whether aspect-level sentiment extracted from citizen feedback provides predictive value for municipal resolution delay and repeat-service-request rates across services and localities.

## Run the dashboard

See [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md) for Windows and macOS/Linux setup. Install `requirements-dashboard.txt` for the lightweight dashboard-only environment. The two small aggregate data files needed by the app are included; raw datasets, training packages, model weights, and Git LFS are not required.

## Final-review update (29 October 2026)

The final-review manuscript is `TeamNo_16_23BCT0029_FINAL_CORRECTIONS.docx`. An exploratory validation-selected ABSA + RSAT model improves NYC-2024 delay R² from 0.5995 to 0.6228, but its bootstrap interval spans zero and persistence remains stronger (0.8839). Repeat-rate selection retains structured features alone. This narrows the earlier all-family negative result rather than claiming that all language features fail. Strict dashboard top-10 overlap is only 1/10; separate fixed-cutoff results use a training-derived burden definition and must not be confused with that overlap. All 24 tests pass. See `FINAL_CORRECTIONS_UPDATE.md` and the saved metric JSON files for details. Zenodo publication/DOI is deferred to the authors.

## Earlier corrected data snapshot (20 October 2026)

The completed remediation uses 4,204,783 cleaned NYC 311 requests across all 24 operational months from 2023 through 2024, 2,006 integrated cells, and a 1,885-cell one-month-ahead forecasting table. LDA and BERTopic are fitted only on January-July 2023 training text; ABSA uses duplicate-controlled groups with zero cross-split normalized-text overlap; and the full automated suite passes 20/20 tests. The authoritative final metrics are in `reports/FINAL_PROJECT_REPORT.md` and the corrected manuscript is in `outputs/`.

---

## 1. Project Metadata
- **Institution:** Vellore Institute of Technology (VIT Vellore)
- **Course:** BCSE316L — Design of Smart Cities (AY 2026–27)
- **Class Number:** VL2026270102475
- **Project Number:** 15 | **Team:** Team 16
- **Team Members:**
  - Taher Panbiharwala (`23BCT0028`)
  - Sanidhya Bhandari (`23BCT0209`)
  - Chinmoy Deb (`23BCT0050`)
- **Faculty Guide:** Dr. Kalaavathi B, School of Computer Science and Engineering (SCOPE)
- **Reference City:** New York City (NYC 311 & RSAT)

---

## 2. Research Question & Formal Formulation

**Central Research Question:**
> *Does aspect-level sentiment extracted from citizen feedback provide predictive value for municipal resolution delay and repeat-service-request rates across services and localities?*

For each observation cell $c = (s, b, t)$ representing Service Category $s$, Borough $b$, and Month $t$:
- $x_c$: Structured 311 features (request volume, agency mix, service distribution).
- $z_c$: Sentiment polarity and aspect grievance intensity extracted from citizen feedback.
- $y_c = (d_c, r_c)$: Operational outcomes, where $d_c$ is mean resolution delay and $r_c$ is repeat-request rate.

We compare:
$$\text{Baseline: } y_c = f_0(x_c) + \varepsilon_c$$
$$\text{Augmented: } y_c = f_1(x_c, z_c) + \varepsilon_c$$
$$\text{Incremental Value: } \Delta = L_0 - L_1$$

Where sentiment is considered predictive if $\Delta > 0$ on strictly held-out chronological test partitions.

---

## 3. Repository Architecture

```
d:\CITY PRJ\
├── README.md                     # Comprehensive project documentation
├── PROJECT_AUDIT.md              # Authoritative document audit & rubric mapping
├── DATASET_FEASIBILITY.md        # Empirical Socrata API audit and schema verification
├── IMPLEMENTATION_PLAN.md        # Detailed Phase 0 to Phase 13 roadmap
├── RUBRIC_EVIDENCE_CHECKLIST.md  # Review 1 (40M) & Review 2 (60M) evidence tracker
├── REQUIRED_RESOURCES.md         # 7-category authoritative bibliography with DOIs
├── PROGRESS.md                   # Real-time task progress tracker
├── requirements.txt              # Pinned Python package dependencies
├── .gitignore                    # Prevents checking in large parquets / model weights
├── configs/
│   └── config.yaml               # Centralized experiment & model configuration
├── data/
│   ├── raw/                      # Unmodified Parquet exports from Socrata API
│   └── processed/                # Cleaned, tokenized, and aggregated datasets
├── src/
│   ├── data/                     # Ingestion, validation, and preprocessing modules
│   ├── sentiment/                # VADER baseline, BERT, and RoBERTa fine-tuning
│   ├── absa/                     # Aspect-based sentiment analysis extraction & classification
│   ├── topics/                   # Unsupervised LDA and BERTopic topic modeling
│   ├── outcomes/                 # Resolution delay and repeat-request calculation
│   ├── models/                   # Baseline and augmented predictive regression models
│   └── evaluation/               # Metrics generation, confusion matrices, and figures
├── dashboard/
│   ├── app.py                    # Multi-page Streamlit application entry point
│   ├── views/                    # Government-facing & citizen-facing dashboard views
│   └── components/               # Interactive Plotly chart components
├── reports/
│   ├── metrics/                  # Output JSON metric logs (F1, MAE, RMSE, Coherence)
│   ├── figures/                  # 300-DPI publication-ready charts (PNG/PDF)
│   └── eda/                      # Exploratory data analysis tables
└── tests/                        # Automated unit, integration, and reproducibility tests
```

---

## 4. Execution Workflow (Phases)

| Phase | Milestone | Key Deliverable | Status |
| :---: | :--- | :--- | :---: |
| **0** | **Audit & Feasibility** | `PROJECT_AUDIT.md`, `DATASET_FEASIBILITY.md` | **Completed** |
| **1** | **Development Environment** | Virtual environment, `requirements.txt`, `config.yaml` | **Active / Next** |
| **2** | **Data Acquisition & Quality** | Parquet ingestion of NYC 311 & RSAT from Socrata API | Planned |
| **3** | **Exploratory Data Analysis** | Service & borough distributions, temporal trends | Planned |
| **4** | **Lexicon Baseline (VADER)** | VADER sentiment benchmark (Macro-F1, Accuracy) | Planned |
| **5** | **Transformer Sentiment Models** | Fine-tuned BERT & RoBERTa models | Planned |
| **6** | **Aspect-Based Sentiment (ABSA)**| Service aspect extraction & aspect-level sentiment | Planned |
| **7** | **Topic Discovery** | LDA vs. BERTopic topic coherence ($C_v$) comparison | Planned |
| **8** | **Operational Outcomes** | Resolution delay ($d_c$) & repeat-request rate ($r_c$) | Planned |
| **9** | **Aggregate Integration** | Service $\times$ Borough $\times$ Month joined cells | Planned |
| **10**| **Predictive Modeling** | Structured baseline vs. Augmented model ($\Delta$) | Planned |
| **11**| **Interactive Dashboards** | Government & citizen Streamlit dashboards | Planned |
| **12**| **Testing & Reproducibility** | Automated test suite passing with `pytest` | Planned |
| **13**| **Manuscript & Final Report** | Updated publication manuscript & final report | Planned |

---

## 5. Verification & Ground Truth Discipline

To ensure strict academic honesty and eliminate hallucinated findings:
1. **Zero Data Fabrication:** All models run on authentic data acquired from NYC Open Data.
2. **Leakage-Proof Evaluation:** VADER is strictly an unsupervised baseline and is never used to pseudo-label training data for Transformers.
3. **Temporal Generalization:** The corrected local experiment uses Jan-Aug 2023 for training, Sep-Dec 2023 for validation, and 2024 as the out-of-time test horizon. The current 311 snapshot has only 21 records from 2025.
4. **Epistemological Constraint:** Findings report predictive association, never causality.
