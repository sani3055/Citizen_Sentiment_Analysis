# Required Research Resources & Authoritative Bibliography

**Project Title:** Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP  
**Course:** BCSE316L — Design of Smart Cities | Project 15 | Team 15  
**Compilation Date:** October 2026  
**Auditor / Mentor:** Senior Research Supervisor & AI/NLP Software Architect

---

## Category A: Core Academic & Institutional Documents

| Resource Title | Authors / Issuing Body | Year | Document Purpose & Phase Used | Access Method |
| :--- | :--- | :---: | :--- | :--- |
| **BCSE316L Project Title Allocation Matrix** | VIT Vellore (Dean SCOPE / Course Faculty) | 2026 | Authoritative assignment of Project 15, title, objectives, scope boundaries, and SDGs. *(Phase 0)* | Uploaded by User |
| **DA-1 Problem Formulation & Design Presentation** | Team 15 (Taher P., Sanidhya B., Chinmoy D., Guide: Dr. Kalaavathi B) | 2026 | Initial student formulation, literature survey overview, conceptual architecture, and city context. *(Phase 0)* | Uploaded by User |
| **Research Manuscript Draft (`CityReview`)** | Team 15 & Dr. Kalaavathi B | 2026 | Academic draft containing problem formulation, formal equations (1)–(3), Table 1 literature survey, and scope boundaries. *(Phase 0, 13)* | Uploaded by User |
| **Review-1 Evaluation Rubric (40 Marks)** | BCSE316L Course Committee, VIT | 2026 | Grading standards for problem context, literature review (25+ papers), gaps, objectives, baseline/alternative methods, and metrics. *(Phase 0, 13)* | Uploaded by User |
| **Review-2 Evaluation Rubric (60 Marks)** | BCSE316L Course Committee, VIT | 2026 | Grading standards for live environment, dataset justification, pipeline detail, parameter measurements, result graphs, conclusions, and publication status. *(Phases 1–13)* | Uploaded by User |

---

## Category B: Official NYC Open Data Datasets & Documentation

| Resource Name & ID | Publishing Agency | Year | Official Portal URL & API Endpoint | Why Required & Implementation Phase | Direct Antigravity Access |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **311 Resolution Satisfaction Survey (RSAT)** <br>`5ijn-vbdv` | NYC Office of Technology and Innovation (OTI) | 2022–2026 | [NYC Open Data 5ijn-vbdv](https://data.cityofnewyork.us/d/5ijn-vbdv)<br>Endpoint: `https://data.cityofnewyork.us/resource/5ijn-vbdv.json` | Supplies 568,816 citizen satisfaction ratings (5-point Likert) and 8 categorical dissatisfaction reasons for aspect ground truth. *(Phases 2, 4, 6, 9)* | **Yes (Direct SODA REST API)** |
| **311 Service Requests from 2010 to Present** <br>`erm2-nwe9` | NYC Office of Technology and Innovation (OTI) | 2010–Present | [NYC Open Data erm2-nwe9](https://data.cityofnewyork.us/d/erm2-nwe9)<br>Endpoint: `https://data.cityofnewyork.us/resource/erm2-nwe9.json` | Supplies operational ground-truth requests (35M+ rows) for resolution delay ($d_c$) and repeat-request rate ($r_c$). *(Phases 2, 8, 9)* | **Yes (Direct SODA REST API)** |
| **Socrata Open Data API (SODA) Developer Docs** | Tyler Technologies / Socrata | 2025 | [SODA Developer Guide](https://dev.socrata.com/consumers/getting-started.html) | Technical standard for SoQL queries, pagination (`$limit`, `$offset`), filtering, and aggregation. *(Phase 2)* | **Yes (Public Web)** |
| **NYC 311 Monitoring Tool Report** | Office of the NY State Comptroller | 2025 | Report 3-2026, [OSC NYC311 Report](https://www.osc.ny.gov/) | Background evidence on reporting volume, lack of valid zip codes, repeat requesters, and neighbourhood demand disparities. *(Phases 0, 3)* | **Yes (Public Web)** |
| **NYC Open Data Law & Progress Report** | NYC Mayor's Office of Data Analytics (MODA) | 2025 | [MODA Annual Report](https://opendata.cityofnewyork.us/) | Authoritative legal framework requiring agency release of public records. *(Phases 0, 13)* | **Yes (Public Web)** |

---

## Category C: Foundational Papers for Core NLP & Topic Models

| Paper Title | Authors | Year | Venue / Identifier / DOI | Method / Role in Project | Phase |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **VADER: A Parsimonious Rule-Based Model for Sentiment Analysis of Social Media Text** | C.J. Hutto, E. Gilbert | 2014 | *ICWSM 2014*, [AAAI ICWSM](https://ojs.aaai.org/index.php/ICWSM/article/view/14550) | Rule-based lexicon baseline for civic sentiment; establishes benchmark to beat without training. | Phase 4 |
| **BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding** | J. Devlin, M.-W. Chang, K. Lee, K. Toutanova | 2019 | *NAACL-HLT 2019*, [arXiv:1810.04805](https://arxiv.org/abs/1810.04805) | Primary bidirectional Transformer architecture; fine-tuned on civic feedback text. | Phase 5 |
| **RoBERTa: A Robustly Optimized BERT Pretraining Approach** | Y. Liu, M. Ott, N. Goyal, et al. | 2019 | *arXiv preprint*, [arXiv:1907.11692](https://arxiv.org/abs/1907.11692) | Optimized Transformer alternative using dynamic masking and larger mini-batches; benchmarked against BERT. | Phase 5 |
| **Latent Dirichlet Allocation** | D.M. Blei, A.Y. Ng, M.I. Jordan | 2003 | *Journal of Machine Learning Research*, 3:993–1022 | Generative probabilistic baseline for unsupervised topic discovery; evaluates $C_v$ topic coherence. | Phase 7 |
| **BERTopic: Neural topic modeling with a class-based TF-IDF procedure** | M. Grootendorst | 2022 | *arXiv:2203.05794*, [arXiv Link](https://arxiv.org/abs/2203.05794) | Modern embedding-based topic discovery utilizing sentence-transformers, UMAP, and HDBSCAN. | Phase 7 |

---

## Category D: Aspect-Based Sentiment Analysis (ABSA) Methodology Papers

| Paper Title | Authors | Year | Venue / DOI | Methodological Contribution | Phase |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **A Survey on Aspect-Based Sentiment Analysis: Tasks, Methods, and Challenges** | W. Zhang, X. Li, Y. Deng, L. Bing, W. Lam | 2022 | *IEEE TKDE*, 35(11):11019–11038, [doi:10.1109/TKDE.2022.3230975](https://doi.org/10.1109/TKDE.2022.3230975) | Comprehensive taxonomy of ABSA tasks: Aspect Category Detection (ACD) and Aspect Sentiment Classification (ASC). | Phase 6 |
| **A Systematic Review of Aspect-Based Sentiment Analysis: Domains, Methods, and Trends** | Y.C. Hua, P. Denny, J. Wicker, K. Taskova | 2024 | *Artificial Intelligence Review*, 57(11):296, [doi:10.1007/s10462-024-10925-5](https://doi.org/10.1007/s10462-024-10925-5) | Evidence of critical research gap: reviews 519 studies showing public-sector/civic domains are addressed by fewer than 13 studies. | Phases 0, 6 |
| **Aspect Based Sentiment Analysis Using Deep Learning Approaches: A Survey** | G.S. Chauhan, R. Nahta, Y.K. Meena, D. Gopalani | 2023 | *Computer Science Review*, 49:100576, [doi:10.1016/j.cosrev.2023.100576](https://doi.org/10.1016/j.cosrev.2023.100576) | Evaluates deep learning ABSA models, highlighting domain shift vulnerabilities and feature extraction. | Phase 6 |
| **Issues and Challenges of Aspect-Based Sentiment Analysis: A Comprehensive Survey** | A. Nazir, Y. Rao, L. Wu, L. Sun | 2022 | *IEEE Trans. Affective Computing*, 13(2):845–863, [doi:10.1109/TAFFC.2020.2970399](https://doi.org/10.1109/TAFFC.2020.2970399) | Organizes unresolved challenges including implicit aspects and domain adaptation in civic governance. | Phase 6 |
| **Explainable Aspect-Based Sentiment Analysis Using Transformer Models** | I. Perikos, A. Diamantopoulos | 2024 | *Big Data and Cognitive Computing*, 8(11):141, [doi:10.3390/bdcc8110141](https://doi.org/10.3390/bdcc8110141) | Benchmarks BERT and RoBERTa on ABSA datasets with LIME/SHAP interpretability. | Phases 5, 6 |
| **A Novel Weight-Oriented Graph Convolutional Network for ABSA** | B. Yu, S. Zhang | 2023 | *The Journal of Supercomputing*, 79(1):947–972, [doi:10.1007/s11227-022-04691-3](https://doi.org/10.1007/s11227-022-04691-3) | Demonstrates how dependency trees capture aspect-opinion alignments in noisy text. | Phase 6 |
| **An Empirical Study of Sentiment-Enhanced Pre-Training for ABSA** | Y. Zhang, Y. Yang, B. Liang, et al. | 2023 | *Findings of ACL 2023*, pp. 9633–9651, [ACL Anthology](https://aclanthology.org/2023.findings-acl.612/) | Demonstrates that domain-adapted pre-training substantially elevates fine-grained ABSA performance. | Phase 6 |

---

## Category E: Municipal 311 Outcomes & Civic NLP Research

| Paper Title | Authors | Year | Venue / DOI | Critical Finding & Project Justification | Phase |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Structure of 311 Service Requests as a Signature of Urban Location** | L. Wang, C. Qian, P. Kats, C. Kontokosta, S. Sobolevsky | 2017 | *PLOS ONE*, 12(10):e0186314, [doi:10.1371/journal.pone.0186314](https://doi.org/10.1371/journal.pone.0186314) | Proves 311 complaint distribution serves as a structural signature of urban neighborhoods. Used for baseline structured features $x_c$. | Phases 8, 9 |
| **Estimating Reporting Bias in 311 Complaint Data** | K.S. Boxer, B. Hong, C.E. Kontokosta, D.B. Neill | 2025 | *Annals of Applied Statistics*, 19(2), [arXiv:2104.14442](https://arxiv.org/abs/2104.14442) | Demonstrates that complaint volume under-represents true distress in underserved areas; motivates sentiment as an alternative signal. | Phases 0, 10 |
| **Bias in Smart City Governance: Socio-Spatial Disparities in 311** | C.E. Kontokosta, B. Hong | 2021 | *Sustainable Cities and Society*, 64:102503, [doi:10.1016/j.scs.2020.102503](https://doi.org/10.1016/j.scs.2020.102503) | Proves that naive resource allocation based purely on request counts biases delivery against vulnerable groups. | Phases 0, 10 |
| **311 Service Requests as Indicators of Neighborhood Distress** | Y. Li, A. Hyder, L.T. Southerland, et al. | 2020 | *Scientific Reports*, 10:19579, [doi:10.1038/s41598-020-76673-8](https://doi.org/10.1038/s41598-020-76673-8) | Establishes statistical methodology for pairing municipal 311 data with downstream operational indicators. | Phase 8 |
| **Performance Evaluation of ML Techniques on Resolution Time Prediction** | T.-E. Tai, S.-C. Haw, W.-E. Kong, K.-W. Ng | 2024 | *Int. J. Robotics, Automation & Sciences*, 6(2):59–68 | Demonstrates ensemble ML superiority in ticket resolution time prediction. Informs baseline model $f_0(x_c)$. | Phase 10 |
| **Topic-Sentiment Analysis of Citizen Environmental Complaints in China** | J. Liu, R. Long, H. Chen, et al. | 2024 | *Journal of Environmental Management*, 371:123112, [doi:10.1016/j.jenvman.2024.123112](https://doi.org/10.1016/j.jenvman.2024.123112) | Analyzes 102k+ citizen complaints using Stacking-BERT; notes lack of downstream resolution linkage (Gap G1). | Phase 7 |
| **Analyzing Public Demands on China's Online Government Inquiry Platform** | Z. Tang, X. Pan, Z. Gu | 2024 | *PLOS ONE*, 19(2):e0296855, [doi:10.1371/journal.pone.0296855](https://doi.org/10.1371/journal.pone.0296855) | Uses BERTopic on civic text; documents thematic shifts during municipal emergencies. | Phase 7 |
| **Tales of a City: Sentiment Analysis of Urban Green Space in Dublin** | M. Ghahramani, N.J. Galle, C. Ratti, F. Pilla | 2021 | *Cities*, 119:103395, [doi:10.1016/j.cities.2021.103395](https://doi.org/10.1016/j.cities.2021.103395) | Employs LDA and sentiment scoring on civic reviews to uncover citizen valuation patterns. | Phase 7 |

---

## Category F: Official Library & Tool Documentation

| Library / Tool | Primary Purpose in Implementation | Verified Documentation URL | Phase Used |
| :--- | :--- | :--- | :---: |
| **PyTorch (v2.x)** | Deep learning backend, tensor computation, GPU acceleration | [pytorch.org/docs](https://pytorch.org/docs/) | Phases 5, 6 |
| **Hugging Face Transformers** | Model definitions for BERT, RoBERTa, tokenizers, trainer | [huggingface.co/docs/transformers](https://huggingface.co/docs/transformers/) | Phases 5, 6 |
| **Hugging Face Datasets** | Memory-mapped parquet loading and tokenization mapping | [huggingface.co/docs/datasets](https://huggingface.co/docs/datasets/) | Phases 2, 5 |
| **scikit-learn (v1.5+)** | Preprocessing, Ridge/RandomForest regressors, metrics | [scikit-learn.org](https://scikit-learn.org/) | Phases 4, 8, 10 |
| **NLTK (VADER)** | Lexicon sentiment analyzer baseline | [nltk.org](https://www.nltk.org/) | Phase 4 |
| **BERTopic & Gensim** | Embeddings-based topic modeling and LDA coherence scoring | [maartengr.github.io/BERTopic](https://maartengr.github.io/BERTopic/) | Phase 7 |
| **Streamlit (v1.38+)** | Interactive government & citizen dual dashboards | [docs.streamlit.io](https://docs.streamlit.io/) | Phase 11 |
| **Plotly (v5.x)** | Publication-grade interactive and static visual plots | [plotly.com/python](https://plotly.com/python/) | Phases 3, 11 |
| **Pytest** | Automated test suite execution and verification | [docs.pytest.org](https://docs.pytest.org/) | Phase 12 |

---

## Category G: Optional & Supporting Resources

1. **SHAP (SHapley Additive exPlanations):** Model interpretability library for explaining regression feature importances $\rightarrow$ [shap.readthedocs.io](https://shap.readthedocs.io/)
2. **LightGBM:** Fast gradient-boosted decision tree algorithm for tabular cell regression $\rightarrow$ [lightgbm.readthedocs.io](https://lightgbm.readthedocs.io/)
3. **Pre-trained Hugging Face Hub Models:**
   - `bert-base-uncased`: [huggingface.co/bert-base-uncased](https://huggingface.co/bert-base-uncased)
   - `roberta-base`: [huggingface.co/roberta-base](https://huggingface.co/roberta-base)
   - `sentence-transformers/all-MiniLM-L6-v2`: [huggingface.co/sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
