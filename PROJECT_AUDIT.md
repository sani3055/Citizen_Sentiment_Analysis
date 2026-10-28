# Project Audit: Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP

**Project Details:**
- **Course:** BCSE316L — Design of Smart Cities (AY 2026–27)
- **Class Number:** VL2026270102475
- **Project Number:** 15 | **Team Number:** 15
- **Team Members:** Taher Panbiharwala (23BCT0028), Sanidhya Bhandari (23BCT0209), Chinmoy Deb (23BCT0050)
- **Project Guide:** Dr. Kalaavathi B, School of Computer Science and Engineering (SCOPE), VIT Vellore
- **Audit Date:** October 2026
- **Auditor / Mentor:** Senior Research Supervisor & AI/NLP Software Architect

---

## 1. Executive Summary & Audit Scope

This document provides a comprehensive, rigorous comparative audit of all authoritative project documents provided for Project 15:
1. **Official Project-Title Assignment Sheet (`VL2026270102475` Project Matrix)**
2. **DA-1 Presentation Slide Deck (27 slides, `BCSE316L_Team15_DA1.pdf`)**
3. **Research Manuscript Draft (`A Transformer-Based Framework for Aspect-Level Citizen Sentiment Analysis and Municipal Service Outcome Prediction: Evidence from NYC 311`, 10 pages)**
4. **Review 1 Evaluation Rubric (40 Marks: Problem Formulation & Design)**
5. **Review 2 Evaluation Rubric (60 Marks: Implementation & Dissemination)**

The goal of this audit is to establish unambiguous project scope, align objectives with academic grading criteria, identify discrepancies between preliminary presentation proposals and formal manuscript formulations, and define exact boundaries to prevent scope creep or methodological errors.

---

## 2. Comparative Analysis Across Authoritative Documents

| Dimension | 1. Assignment Sheet (Project 15) | 2. DA-1 Presentation Deck | 3. Manuscript Draft (`CityReview`) | 4. Evaluation Rubrics Alignment | Status & Reconciled Directive |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Official Title** | Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP | Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP | A Transformer-Based Framework for Aspect-Level Citizen Sentiment Analysis and Municipal Service Outcome Prediction: Evidence from NYC 311 | Title must reflect domain relevance and municipal outcomes. | **Title Alignment:** The course catalog title is retained for university filings, while the extended academic title is used on the manuscript paper. |
| **Scope & Boundaries** | Analyse citizen feedback/complaints about city services to surface sentiment trends and priority issues for governance dashboards. | Problem formulation & design in NYC; 311 operational outcomes paired with RSAT feedback; aggregate-level integration. | Investigate whether aspect-level sentiment adds predictive value for resolution delay and repeat-request rate beyond 311 structured fields alone. | Rubric 1 Criterion 4: "Scope boundaries explicitly declared; measurable and achievable." | **Scope Boundary:** Strict boundary established. Predictive association only; no causal claims; aggregate grain at Service $\times$ Borough $\times$ Month; prototype dashboards. |
| **Target SDGs** | SDG 11 (Sustainable Cities & Communities); SDG 16 (Peace, Justice & Strong Institutions). | SDG 11 (Target 11.6/Participatory management); SDG 16 (Institutional responsiveness & accountability). | Highlighted in introduction and motivation; response time and repeat rates as proxies for civic accountability. | Rubric 1 Criterion 1: "SDG linkage stated and justified." | **SDG Alignment:** Fully consistent across all documents. |
| **Reference Cities** | New York (311), Seoul, Chennai (listed in deployment column). | New York City as the primary reference deployment case study; open data law cited. | New York City (NYC 311 + RSAT); future work notes potential transfer to other open 311 cities. | Rubric 1 Criterion 1 & Rubric 2 Criterion 1: Specific setting defined and demonstrated. | **Case City:** New York City is the primary empirical testbed due to public availability of both 311 operational records and RSAT survey satisfaction records. |
| **Data Sources** | NYC 311 Service Requests, municipal complaint portals, geotagged X/Twitter civic data. | NYC 311 Service Requests (operational ground truth) + NYC 311 Resolution Satisfaction Survey (RSAT). | NYC 311 Service Requests (2010–present) + NYC 311 Resolution Satisfaction Survey (RSAT, 2022–2026). | Rubric 2 Criterion 2: "Dataset(s) named with source, size, class distribution, feature set and licence." | **Reconciled Data Strategy:** NYC 311 (`erm2-nwe9`) + RSAT (`5ijn-vbdv`). Social media is excluded as noisy/unrepresentative per literature survey recommendations. |
| **Core NLP Models** | Fine-tuned Transformer (BERT/RoBERTa); ABSA per service; Baselines: BERTopic/LDA + VADER. | VADER baseline, BERT/RoBERTa fine-tuning, ABSA, LDA and BERTopic for topic/aspect discovery. | VADER baseline (lexicon), BERT and RoBERTa (supervised Transformer classification), ABSA, LDA and BERTopic. | Rubric 1 Criterion 5 & Rubric 2 Criterion 3: Baseline plus at least one alternative; parameters tabulated. | **Model Suite:** Baseline: VADER. Supervised: BERT (`bert-base-uncased`) and RoBERTa (`roberta-base`). Discovery: LDA and BERTopic. |
| **Downstream Outcomes** | Ranking problem areas; governance-facing dashboard. | Resolution delay ($d_c$) and repeat-request rate ($r_c$). | Dual outcomes: Mean Resolution Delay $d_c$ (hours/days) and Repeat-Request Rate $r_c$ (percentage). | Rubric 1 Criterion 6 & Rubric 2 Criterion 4: Exact metrics to be reported named with baselines. | **Operational Outcomes:** Formally defined in Eq. (1)–(3) of manuscript. Structured-only baseline vs. Sentiment/aspect-augmented model. |
| **Dashboards** | Governance-facing trend dashboard. | Governance-facing dashboard (ranking service-locality cells by priority) + Citizen-facing dashboard. | Dual dashboards: Government-facing (ranked cells via Precision@k) and Citizen-facing (borough service trends). | Rubric 2 Criterion 1 & 5: Live demonstrated tool with labelled graphs. | **Dual Deliverable:** Both dashboards implemented via Streamlit/FastAPI web interface. |

---

## 3. Detailed Objectives and Research Questions

### Authoritative Problem Statement
> *"To investigate whether aspect-level sentiment extracted from citizen feedback provides predictive value for municipal resolution delay and repeat-service-request rates across services and localities."*

### The Four Core Research Objectives
1. **O1 — Sentiment Classification:**
   - Implement VADER as the unsupervised lexicon baseline.
   - Fine-tune BERT (`bert-base-uncased`) and RoBERTa (`roberta-base`) on municipal sentiment classification.
   - Evaluate on independently annotated ground-truth data using Accuracy, Macro-F1, per-class Precision, Recall, and F1.
   - *Strict Guardrail:* VADER must never be used to pseudo-label training data for Transformers.
2. **O2 — Aspect Identification & Topic Discovery:**
   - Define service-specific municipal aspects (e.g., Response Time, Communication/Updates, Work Quality, Issue Resolution, Information Accuracy).
   - Implement Aspect-Based Sentiment Analysis (ABSA) for aspect category extraction and polarity classification.
   - Apply unsupervised topic discovery using Latent Dirichlet Allocation (LDA) and BERTopic to identify emergent sub-themes.
   - Evaluate aspect extraction F1, aspect sentiment F1, and topic coherence ($C_v$ and $U_{mass}$).
3. **O3 — Aggregate-Level Integration & Outcome Modeling:**
   - Compute cell-level operational ground truth from NYC 311: Mean Resolution Delay $d_c$ and Repeat-Request Rate $r_c$ per Service ($s$) $\times$ Borough ($b$) $\times$ Month ($t$).
   - Integrate structured 311 features $x_c$ (volume, agency mix, complaint distribution) with aggregated sentiment/aspect features $z_c$.
   - Train and compare structured-only baseline $f_0(x_c)$ against augmented model $f_1(x_c, z_c)$.
   - Measure incremental predictive gain $\Delta = L_0 - L_1$ using MAE, RMSE, and $R^2$ on held-out chronological test sets.
4. **O4 — Interactive Dashboards & Decision Support:**
   - **Government-Facing Dashboard:** Rank service-locality cells by predictive delay and negative aspect intensity; evaluate ranking quality using Precision@$k$.
   - **Citizen-Facing Dashboard:** Provide public visibility into borough-level resolution speeds, recurring issues, and satisfaction trends with data-quality caveats.

---

## 4. Conflict Identification and Resolution

The audit identified three critical methodological tensions between preliminary slides and the rigorous research manuscript:

### Conflict 1: Data Matching Granularity (Row-Level vs. Aggregate-Level)
- **Tension:** Early proposals informally suggested matching survey respondents to their original 311 complaint.
- **Resolution in Manuscript:** The RSAT survey is anonymized by NYC OTI (timestamps truncated to year/month, geographic coordinates removed and reduced to borough). Furthermore, `unique_key` in RSAT is a survey response ID, not the 311 complaint ID.
- **Authoritative Rule:** **No row-level match is attempted.** All integration is strictly performed at the aggregate cell grain: $\text{Service Category} \times \text{Borough} \times \text{Month}$.

### Conflict 2: Availability of Free-Text Comments in Public RSAT
- **Tension:** Early documentation assumed RSAT would include an open-ended narrative text box where citizens describe their complaint.
- **Resolution from Empirical API Audit:** NYC Open Data dataset `5ijn-vbdv` omits free-text citizen paragraphs to protect PII. `dissatisfaction_reason` contains 8 standardized grievance statements, and `resolution_description` contains agency narrative responses.
- **Authoritative Rule:** We must document this finding in `DATASET_FEASIBILITY.md` and utilize a principled multi-source textual corpus:
  1. RSAT grievance statements and agency resolution narratives.
  2. NYC 311 detailed descriptors and complaint text.
  3. A verified municipal civic feedback corpus for robust Transformer fine-tuning and ABSA benchmarking.

### Conflict 3: Causation vs. Predictive Association
- **Tension:** Some smart cities literature loosely claims sentiment "causes" service delays or that improving sentiment "speeds up" repairs.
- **Resolution in Manuscript:** The manuscript explicitly constrains claims: *"We do not make any causal claims but interpret a positive $\Delta$ as evidence of predictive association."*
- **Authoritative Rule:** All reporting, dashboard outputs, and manuscript text must maintain strict epistemological discipline: predictive association only.

---

## 5. Review-1 and Review-2 Rubric Mapping

### Review 1 Rubric (40 Marks — Problem Formulation and Design)
| Criterion | Max Marks | Target Deliverables & Evidence |
| :--- | :---: | :--- |
| **1. Introduction & problem context** | 4 | Domain context, 311 blind spots, SDG 11 & 16 linkage, reference city setting (NYC). Covered in `PROJECT_AUDIT.md`, `README.md`, and manuscript Section 1. |
| **2. Literature survey (min. 25 papers)** | 10 | 27 peer-reviewed papers (21 from 2021+), organized across 8 themes. Complete comparison table with method, testbed, findings, and limitations. Listed in `REQUIRED_RESOURCES.md` and manuscript Table 1. |
| **3. Research gaps** | 6 | 4 explicitly formulated gaps (G1: Missing outcome validation, G2: Separation of text and 311 modeling, G3: Uneven spatial-temporal analysis, G4: Lack of independent sentiment evaluation) traced row-by-row. |
| **4. Problem statement & objectives** | 5 | Formal 1-sentence statement, mathematical formulation (Eq. 1–3), 4 measurable objectives (O1–O4), explicit scope boundaries. |
| **5. Methodologies identified** | 8 | End-to-end data-flow diagram; VADER baseline vs. BERT/RoBERTa; LDA/BERTopic; structured vs. augmented regression models; feasibility verified via Socrata API. |
| **6. Expected outcomes & parameters** | 4 | Exact metrics defined: Accuracy, Macro-F1, ABSA F1, Topic Coherence ($C_v$), MAE, RMSE, $R^2$, Precision@$k$. Comparison against structured baselines throughout. |
| **7. Presentation & documentation** | 3 | Rigorous documentation files, clear modular structure, reproducible scripts. |

### Review 2 Rubric (60 Marks — Implementation and Dissemination)
| Criterion | Max Marks | Target Deliverables & Evidence |
| :--- | :---: | :--- |
| **1. Implementation environment** | 8 | Python 3.13 virtual environment (`venv`), PyTorch, Hugging Face Transformers, scikit-learn, BERTopic, Streamlit, automated test suite, version-controlled scripts. |
| **2. Dataset description & justification** | 6 | NYC 311 (`erm2-nwe9`) + RSAT (`5ijn-vbdv`), official license (Open Data Law), schema, size (568k RSAT, 35M+ 311), cleaning, class balance, temporal split (train/val/test). |
| **3. Implementation methodology detail** | 12 | End-to-end reproducible pipeline, hyperparameter tables, baseline (VADER, structured regression) + alternatives (BERT, RoBERTa, LightGBM/Ridge), modular `src/` codebase. |
| **4. Parameters measured** | 8 | All metrics measured with units; repeated seeds; mean and standard deviation; overhead (training runtime, inference latency). |
| **5. Result analysis with graphs and tables** | 12 | High-resolution publication-ready plots (confusion matrices, ROC/PR curves, loss curves, residual plots, feature importances, trend graphs) with axes, legends, and error bars. |
| **6. Conclusion & future enhancement** | 6 | Answers problem statement; quantifies incremental predictive gain $\Delta$; honest limitations; technically grounded future work. |
| **7. Publication status** | 8 | Manuscript in publication format (IEEE/Scopus conference template or target journal); bibliography formatted in APA/IEEE; submission package ready. |

---

## 6. Audit Conclusion & Next Steps

The project requirements and research framework are solid, well-scoped, and directly aligned with the highest tier of both VIT evaluation rubrics. With the authoritative parameters set, the next prerequisite is to formalize `DATASET_FEASIBILITY.md` and `IMPLEMENTATION_PLAN.md`.
