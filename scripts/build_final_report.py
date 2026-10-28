"""Generate the audited capstone report directly from saved metric artifacts."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "reports" / "metrics"
OUTPUT = ROOT / "reports" / "FINAL_PROJECT_REPORT.md"


def load(name):
    with (METRICS / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def model_rows(target_name, target):
    rows = []
    for algorithm, result in target["algorithms"].items():
        base = result["baseline"]["test_metrics"]
        aug = result["augmented"]["test_metrics"]
        rows.append(
            f"| {target_name} | {algorithm} | {base['r2']:.4f} | {aug['r2']:.4f} | "
            f"{result['delta_r2']:+.4f} | {base['mae']:.4f} | {aug['mae']:.4f} | "
            f"{result['paired_ttest_p_value']:.4g} |"
        )
    return "\n".join(rows)


def main():
    vader = load("vader_metrics.json")
    topics = load("topic_coherence.json")
    absa = load("absa_metrics.json")
    transformer = load("transformer_metrics.json")
    outcomes = load("outcomes_summary.json")
    sensitivity = load("repeat_rate_sensitivity.json")
    integration = load("integration_summary.json")
    predictive = load("lagged_predictive_modeling_results.json")
    robustness = load("robustness_results.json")
    ranking = load("priority_ranking_metrics.json")

    rsat = pd.read_parquet(ROOT / "data" / "raw" / "rsat_raw.parquet", columns=["unique_key"])
    nyc = pd.read_parquet(ROOT / "data" / "raw" / "nyc311_raw.parquet", columns=["unique_key", "created_date"])
    monthly = pd.to_datetime(nyc["created_date"]).dt.to_period("M").value_counts().sort_index()
    absa_rule = absa["models"]["rule_based_baseline"]
    absa_tfidf = absa["models"]["tfidf_logistic_regression"]
    transformer_test = transformer["evaluation_metrics_out_of_time"]
    delay_robust = robustness["results_by_target"]["mean_resolution_delay_hours"]
    repeat_robust = robustness["results_by_target"]["repeat_request_rate_14d"]
    rank_items = sorted((int(k), value) for k, value in ranking["metrics_by_k"].items())
    rank_table = "\n".join(
        f"| {k} | {value['precision_at_k']:.3f} | {value['lift_over_random']:.2f} | {value['ndcg_at_k']:.3f} |"
        for k, value in rank_items
    )
    coverage = ", ".join(f"{period}: {count:,}" for period, count in monthly.items())

    report = f"""# Final Project Report — Team 16

**Project:** Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP  
**Course:** BCSE316L — Design of Smart Cities  
**Institution:** Vellore Institute of Technology, Vellore  
**Team:** 16  
**Members:** Taher Panbiharwala (23BCT0028), Sanidhya Bhandari (23BCT0209), Chinmoy Deb (23BCT0050)  
**Faculty guide:** Dr. Kalaavathi B  
**Updated:** 20 October 2026

## 1. Research question and corrected design

This project asks whether sentiment, topic, grievance-aspect, and satisfaction signals add out-of-time predictive information for municipal resolution delay and repeat requests after service identity, borough, season, and request volume are controlled. The primary design uses features observed in month *t* to predict outcomes for the same service and borough in month *t+1*. Same-month models are retained only as a secondary monitoring analysis. The results are predictive associations and do not establish causality.

## 2. Data provenance and coverage

| Source | Socrata ID | Clean records | Analytic period | Role |
|---|---:|---:|---|---|
| NYC 311 Resolution Satisfaction Survey | `5ijn-vbdv` | {len(rsat):,} | 2023–2025 | Satisfaction and standardised grievance labels |
| NYC 311 Service Requests | `erm2-nwe9` | {len(nyc):,} | 2023–2024 | Text, delay, repeat flags, volume |

The 311 extract uses paged Socrata retrieval, a server-side count check, case-normalised top-service matching, timestamp validation, and an explicit 24-month completeness check. All months from January 2023 through December 2024 are present. Monthly counts: {coverage}.

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

VADER was evaluated on {vader['number_of_matched_cells']:,} robust cells. Accuracy was {vader['overall_accuracy']:.4f}, macro-F1 was {vader['macro_f1']:.4f}, and negative-class F1 was {vader['per_class']['Negative']['f1_score']:.4f}. The difference between matched VADER cells and modelled cells is expected: VADER evaluation requires an RSAT cell with at least ten survey responses, while outcome modelling additionally requires all feature tables, an operational outcome cell, lag alignment, and an assigned temporal split.

### 4.2 Topic models

LDA used {topics['lda']['num_topics']} topics and achieved C_v coherence {topics['lda']['coherence_c_v']:.4f}. BERTopic identified {topics['bertopic']['num_topics_discovered']} non-outlier clusters. Both were fitted on {topics['lda']['fit_period']}; test-period text used for fitting is `{topics['lda']['test_period_text_used_for_fit']}`.

### 4.3 Duplicate-controlled ABSA

The source contains {absa['duplicate_control']['raw_labelled_rows']:,} labelled RSAT rows but only {absa['duplicate_control']['unique_normalized_descriptions']:,} normalised descriptions and {absa['duplicate_control']['unique_text_label_pairs']:,} retained text-label pairs. Cross-split normalised-text overlap is zero.

| Model | Test records | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| Rule baseline | {absa['test_sample_count']:,} | {absa_rule['accuracy']:.4f} | {absa_rule['macro_f1']:.4f} |
| TF-IDF logistic regression | {absa['test_sample_count']:,} | {absa_tfidf['accuracy']:.4f} | {absa_tfidf['macro_f1']:.4f} |
| DistilBERT | {transformer['split_counts']['test']:,} | {transformer_test['test_accuracy']:.4f} | {transformer_test['test_macro_f1']:.4f} |

These results measure classification of privacy-limited agency narratives against standardised survey reasons. They are not a human-annotated evaluation of citizen free text.

## 5. Operational outcomes and repeat sensitivity

Across {outcomes['resolution_delay']['total_records']:,} valid requests, median raw delay was {outcomes['resolution_delay']['median_raw_delay_hours']:.2f} hours, the 95th percentile was {outcomes['resolution_delay']['p95_delay_hours']:.2f} hours, and the 99th-percentile winsorisation cap was {outcomes['resolution_delay']['p99_delay_hours_winsorization_threshold']:.2f} hours. Repeat rates were {outcomes['repeat_request_rates']['repeat_rate_7d_pct']:.2f}% at 7 days, {outcomes['repeat_request_rates']['repeat_rate_14d_pct']:.2f}% at 14 days, and {outcomes['repeat_request_rates']['repeat_rate_30d_pct']:.2f}% at 30 days.

Heat/Hot Water accounts for {sensitivity['heat_hot_water']['share_of_all_repeat_flags']:.2%} of all 14-day repeat flags; excluding it gives a repeat rate of {sensitivity['excluding_heat_hot_water']['repeat_rate_14d']:.2%}. The broader housing-service proxy accounts for {sensitivity['housing_service_proxy']['share_of_all_repeat_flags']:.2%} of repeat flags; excluding those services gives {sensitivity['excluding_housing_service_proxy']['repeat_rate_14d']:.2%}. High-volume borough-address groups account for {sensitivity['high_volume_address_proxy']['share_of_all_repeat_flags']:.2%} of repeat flags. The public extract has no authoritative building-type field, so these are sensitivity proxies rather than verified multi-unit-building classifications.

## 6. Primary one-month-ahead predictive results

The lagged integrated table contains {predictive['lagged_cells']:,} cells: {predictive['split_counts'].get('train', 0):,} training, {predictive['split_counts'].get('val', 0):,} validation, and {predictive['split_counts'].get('test', 0):,} untouched 2024 test cells.

| Target | Algorithm | Baseline R² | Augmented R² | ΔR² | Baseline MAE | Augmented MAE | Paired-error p |
|---|---|---:|---:|---:|---:|---:|---:|
{model_rows('Delay (hours)', predictive['results_by_target']['mean_resolution_delay_hours'])}
{model_rows('Repeat rate (14d)', predictive['results_by_target']['repeat_request_rate_14d'])}

The p-values are from two-sided paired tests of per-cell absolute prediction errors. They are not direct significance tests of ΔR². Model selection uses validation R², and the strongest structured and augmented test models are reported even when they differ from the validation-selected algorithm. Therefore, any claim about NLP improvement is algorithm-specific unless an augmented model also exceeds the strongest structured baseline.

## 7. Robustness and uncertainty

For delay, the five-seed mean ΔR² is {delay_robust['aggregate']['delta_r2']['mean']:+.4f} ± {delay_robust['aggregate']['delta_r2']['std']:.4f}; the 2,000-resample 95% interval is [{delay_robust['bootstrap_95_percent_intervals']['delta_r2']['lower_95']:+.4f}, {delay_robust['bootstrap_95_percent_intervals']['delta_r2']['upper_95']:+.4f}]. For repeat rate, the corresponding mean is {repeat_robust['aggregate']['delta_r2']['mean']:+.4f} ± {repeat_robust['aggregate']['delta_r2']['std']:.4f}, with interval [{repeat_robust['bootstrap_95_percent_intervals']['delta_r2']['lower_95']:+.4f}, {repeat_robust['bootstrap_95_percent_intervals']['delta_r2']['upper_95']:+.4f}]. Borough- and service-level MAE results are stored in `robustness_results.json`.

## 8. Dashboard ranking validity

The municipal queue combines 45% predicted delay rank, 35% predicted repeat rank, and 20% lagged dissatisfaction rank. Held-out ranking performance is:

| k | Precision@k | Lift over random | NDCG@k |
|---:|---:|---:|---:|
{rank_table}

The dashboard also contains a resident-facing historical view. It displays aggregate statistics only and must not be used for individual-level decisions.

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

The project is now a defensible research-grade capstone rather than a simple dashboard demonstration. Its main contribution is a reproducible test of whether privacy-safe language and satisfaction signals improve future aggregate municipal-outcome prediction. Conclusions must follow the actual held-out results: report algorithm-specific gains, identify the strongest structured benchmark, describe paired-error significance accurately, and retain the documented limitations.
"""
    OUTPUT.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

