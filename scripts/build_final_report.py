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
    review = load("review_corrections_results.json")
    selected = load("selected_feature_results.json")

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
        f"| {k} | {value['hits']}/{k} | {value['precision_at_k']:.3f} | {value['lift_over_random']:.2f} | {value['ndcg_at_k']:.3f} |"
        for k, value in rank_items
    )
    fixed = ranking["fixed_threshold"]
    fixed_table = "\n".join(
        f"| {k} | {value['hits']}/{k} | {value['precision_at_k']:.3f} | {value['recall_at_k']:.3f} | {value['lift_over_random']:.2f} |"
        for k, value in fixed["metrics_by_k"].items()
    )
    naive_rows, family_rows, selected_rows = [], [], []
    for target, label in [("mean_resolution_delay_hours", "Delay"), ("repeat_request_rate_14d", "Repeat rate")]:
        family = review["feature_family_ablations"][target]
        naive = review["naive_baselines"][target]
        naive_rows.append(f"| {label} | {naive['last_value']['r2']:.4f} | {naive['seasonal_naive_12_month']['r2']:.4f} | {family['structured_only']['r2']:.4f} | {family['all_augmented']['r2']:.4f} |")
        for name, result in family["families"].items():
            family_rows.append(f"| {label} | {name} | {result['metrics']['r2']:.4f} | {result['delta_r2_vs_structured']:+.4f} |")
        result = selected["results_by_target"][target]
        primary = result["primary_seed_42"]
        selected_rows.append(f"| {label} | {' + '.join(result['selected_families']) or 'None'} | {result['selected_validation_metrics']['r2']:.4f} | {primary['selected']['r2']:.4f} | {primary['delta_r2']:+.4f} | {primary['selected']['mae']:.4f} |")
    naive_table, family_table, selected_table = map("\n".join, [naive_rows, family_rows, selected_rows])
    coverage = ", ".join(f"{period}: {count:,}" for period, count in monthly.items())

    report = f"""# Final Project Report — Team 16

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

The declared three-label macro-F1 averages Negative (0.8138), Neutral (0.0000), and Positive (0.0113) with equal weight and `zero_division=0`. Neutral has zero ground-truth support but remains in the explicit label list. This is not a two-class macro-F1.

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

DistilBERT and TF-IDF both underperform the rule baseline. Uniform-guess accuracy of 1/6 is not an established macro-F1 chance benchmark on this imbalanced test set; no at/below-chance claim is made from that number.

## 5. Operational outcomes and repeat sensitivity

Across {outcomes['resolution_delay']['total_records']:,} valid requests, median raw delay was {outcomes['resolution_delay']['median_raw_delay_hours']:.2f} hours, the 95th percentile was {outcomes['resolution_delay']['p95_delay_hours']:.2f} hours, and the 99th-percentile winsorisation cap was {outcomes['resolution_delay']['p99_delay_hours_winsorization_threshold']:.2f} hours. Repeat rates were {outcomes['repeat_request_rates']['repeat_rate_7d_pct']:.2f}% at 7 days, {outcomes['repeat_request_rates']['repeat_rate_14d_pct']:.2f}% at 14 days, and {outcomes['repeat_request_rates']['repeat_rate_30d_pct']:.2f}% at 30 days.

Heat/Hot Water accounts for {sensitivity['heat_hot_water']['share_of_all_repeat_flags']:.2%} of all 14-day repeat flags; excluding it gives a repeat rate of {sensitivity['excluding_heat_hot_water']['repeat_rate_14d']:.2%}. The broader housing-service proxy accounts for {sensitivity['housing_service_proxy']['share_of_all_repeat_flags']:.2%} of repeat flags; excluding those services gives {sensitivity['excluding_housing_service_proxy']['repeat_rate_14d']:.2%}. High-volume borough-address groups account for {sensitivity['high_volume_address_proxy']['share_of_all_repeat_flags']:.2%} of repeat flags. The public extract has no authoritative building-type field, so these are sensitivity proxies rather than verified multi-unit-building classifications.

## 6. Primary one-month-ahead predictive results

The lagged integrated table contains {predictive['lagged_cells']:,} cells: {predictive['split_counts'].get('train', 0):,} training, {predictive['split_counts'].get('val', 0):,} validation, and {predictive['split_counts'].get('test', 0):,} held-out 2024 test cells.

| Target | Algorithm | Baseline R² | Augmented R² | ΔR² | Baseline MAE | Augmented MAE | Paired-error p |
|---|---|---:|---:|---:|---:|---:|---:|
{model_rows('Delay (hours)', predictive['results_by_target']['mean_resolution_delay_hours'])}
{model_rows('Repeat rate (14d)', predictive['results_by_target']['repeat_request_rate_14d'])}

The p-values are from two-sided paired tests of per-cell absolute prediction errors. They are not direct significance tests of ΔR². Model selection uses validation R², and the strongest structured and augmented test models are reported even when they differ from the validation-selected algorithm. Therefore, any claim about NLP improvement is algorithm-specific unless an augmented model also exceeds the strongest structured baseline.

### 6.1 Persistence and individual feature families

| Target | Last-value R² | Seasonal-naive R² | Structured LightGBM R² | All-family R² |
|---|---:|---:|---:|---:|
{naive_table}

| Target | Added family | R² | ΔR² vs structured |
|---|---|---:|---:|
{family_table}

Topics, ABSA, and RSAT individually improve delay R², while VADER reduces it sharply. The all-family drop is therefore a feature-bundle failure, not a general demonstration that language cannot help. Repeat-rate R² near 0.92 is not an established modelling gain: persistence is stronger, and high-volume addresses account for 90.41% of observed repeat flags. This does not causally decompose the R² into persistence and address effects.

### 6.2 Exploratory validation-selected augmentation

All eight subsets of topics, ABSA, and RSAT, including no added family, are scored on September–December 2023 validation after training on February–August 2023 targets. VADER is excluded. Maximum validation R² determines the chosen subset, with fewer columns on an exact tie. The subset is refitted on train plus validation before the NYC-2024 evaluation.

| Target | Added families | Validation R² | 2024 R² | ΔR² vs structured | MAE |
|---|---|---:|---:|---:|---:|
{selected_table}

The seed-42 delay model retains ABSA + RSAT and gains +0.0233 R², with paired absolute-error p = 0.1087. Its five-seed gain is +0.0214 ± 0.0068; a 2,000-resample paired cell-bootstrap interval on seed-mean predictions is [-0.0263, +0.0762]. The interval includes zero and does not account for service/borough clustering. The all-non-VADER reference reaches delay R² 0.6115 and repeat R² 0.9240. Validation selects structured features alone for repeat rate; zero ΔR² then follows from model identity, not equivalence evidence between distinct models. No selected model beats persistence. This post-review extension reuses a previously examined test horizon and is exploratory.

## 7. Original all-family robustness and uncertainty

For delay, the five-seed mean ΔR² is {delay_robust['aggregate']['delta_r2']['mean']:+.4f} ± {delay_robust['aggregate']['delta_r2']['std']:.4f}; the 2,000-resample 95% interval is [{delay_robust['bootstrap_95_percent_intervals']['delta_r2']['lower_95']:+.4f}, {delay_robust['bootstrap_95_percent_intervals']['delta_r2']['upper_95']:+.4f}]. For repeat rate, the corresponding mean is {repeat_robust['aggregate']['delta_r2']['mean']:+.4f} ± {repeat_robust['aggregate']['delta_r2']['std']:.4f}, with interval [{repeat_robust['bootstrap_95_percent_intervals']['delta_r2']['lower_95']:+.4f}, {repeat_robust['bootstrap_95_percent_intervals']['delta_r2']['upper_95']:+.4f}]. Borough- and service-level MAE results are stored in `robustness_results.json`.

## 8. Dashboard ranking validity

The municipal queue combines 45% predicted delay rank, 35% predicted repeat rank, and 20% lagged dissatisfaction rank. Held-out ranking performance is:

| k | Raw hits | Precision@k | Lift (rescaled P@k) | NDCG@k |
|---:|---:|---:|---:|---:|
{rank_table}

Strict top-k relevance has prevalence k/N, so lift = Precision@k × N/k. The original 9.94-fold lift is therefore a rescaling of 1/10 hits, not independent evidence of a strong queue. Top-20 overlap is only 3/20. Continuous NDCG is a graded-score statistic and does not contradict low extreme-cell overlap.

For a separate fixed relevance definition, delay and repeat are mapped to percentiles of February–August 2023 training outcomes. A 55% delay / 45% repeat burden score uses the training 80th-percentile cutoff ({fixed['cutoff']:.4f}), frozen across k and 2024. It identifies {fixed['relevant_cells']}/{fixed['test_cells']} relevant cells ({fixed['relevance_prevalence']:.2%} prevalence).

| k | Raw hits | Fixed-cutoff precision | Recall | Lift vs fixed prevalence |
|---:|---:|---:|---:|---:|
{fixed_table}

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
"""
    OUTPUT.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

