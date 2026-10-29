# Team 16 final corrections update

Updated 29 October 2026 using the highlighted decision-tree route in the final correction memo: fixes 2, 3, and 6 plus fix 1. Fix 4 is addressed by explicitly restricting claims to NYC-2024, rather than claiming an unperformed external-city experiment. Fix 5's interpretation is also corrected.

## Completed work

1. **Feature selection:** Added `src/models/selected_feature_analysis.py`. It evaluates all eight subsets of topics, ABSA, and RSAT (including none), excludes VADER, and selects using September–December 2023 validation R² after fitting on February–August 2023 targets. After selection, models are refitted on train plus validation. No 2024 outcome is used by the subset-selection rule. Because the review already examined 2024 results, the extension is labelled exploratory rather than a new untouched test.
2. **Actual selected-model results:** Delay retains ABSA + RSAT: R² **0.6228** versus structured **0.5995**, ΔR² **+0.0233**, MAE **53.5087 h**, paired absolute-error p **0.1087**. Five-seed ΔR² is **+0.0214 ± 0.0068**, with paired-cell bootstrap interval **[-0.0263, +0.0762]**. The interval includes zero. Repeat selection retains **no added family**, with R² **0.9224**. Last-value persistence remains stronger for both targets. The no-VADER three-family reference is also reported (delay 0.6115, repeat 0.9240).
3. **Ranking correction:** Preserved the original strict overlap and reported raw hits: **1/10, 3/20, 48/99, 108/199**. Explained that its lift equals Precision@k × N/k because relevance is the observed top k. Added a separate burden cutoff fitted on training data only: 55% delay percentile + 45% repeat percentile, using the training 80th-percentile cutoff **61.9031**. Relevance is fixed across k: **202/994** test cells. Hits under this broader definition are **9/10, 18/20, 69/99, 111/199**. These are different relevance questions, not directly comparable metrics. The cutoff is exploratory, not a validated municipal standard, and no staff/persistence queue advantage is claimed.
4. **Manuscript cleanup:** Renumbered Tables 2/3 in order, added selected-model and fixed-cutoff tables, explained VADER macro-F1 as the equal-weight Negative/Neutral/Positive average with zero-support Neutral retained, and added DistilBERT **0.1191** versus rule **0.1668** macro-F1 to the abstract. Removed the unsupported shortcut equating uniform-guess accuracy 1/6 with macro-F1 chance performance.
5. **Interpretation:** Distinguished harmful all-family bundling from modest family-specific delay gains. Scoped operational claims to the selected NYC services and boroughs in January–December 2024. Explained that repeat R² near 0.92 is not a demonstrated improvement over persistence; high-volume address concentration is descriptive, not a causal decomposition of R².
6. **Project consistency:** Updated dashboard evidence, report generation, setup instructions, reproducibility documentation, citation metadata, and compact archive builder. The dashboard continues to use the original all-family queue for comparability; its selected-model evidence is separately labelled exploratory. SHAP now points to the one-month-ahead figure rather than the older same-month file.
7. **Verification:** All **24 pytest tests passed**, including both dashboard views from a copied runtime-only file set, validation-only subset selection, and fixed relevance across k. The paper is exported through Word and checked visually before delivery.

## Files to use

- Manuscript: `TeamNo_16_23BCT0029_FINAL_CORRECTIONS.docx`.
- Deposit package: `outputs/team16_final_corrections_reproducibility.zip`.
- Model evidence: `reports/metrics/selected_feature_results.json`.
- Ranking evidence: `reports/metrics/priority_ranking_metrics.json`.
- Public repository: https://github.com/sani3055/Citizen_Sentiment_Analysis.

## Intentionally pending

**Zenodo publication and DOI:** Deferred at the user's explicit request to do it last. No DOI has been invented or claimed. The authors must publish the prepared package through their account, confirm deposit metadata and reuse licence, and then supply the assigned DOI for the manuscript, `CITATION.cff`, `.zenodo.json`, and README. Journal submission is not performed by this correction task. External-city validation remains optional future research; it is not presented as completed.
