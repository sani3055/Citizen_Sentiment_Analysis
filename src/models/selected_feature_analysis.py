"""Exploratory, validation-selected augmentation requested in the final review.

The 2024 outcomes were already examined in earlier analyses. Although subset
selection below sees only 2023 validation scores, this revision is not a new
confirmatory test on previously unseen data.
"""

from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.train_lagged_predictive import (
    TARGETS, assign_rolling_split, build_lagged_dataset, evaluate,
)
from src.models.train_predictive import make_lightgbm, prepare_features

SEEDS = [42, 123, 2024, 7, 99]


def feature_groups(nlp_features):
    return {
        "topics": [c for c in nlp_features if c in {
            "dominant_topic_mode", "topic_entropy", "dominant_bertopic_mode", "bertopic_outlier_rate"}],
        "ABSA": [c for c in nlp_features if c.startswith("is_aspect_")],
        "RSAT": [c for c in nlp_features if c in {
            "citizen_dissatisfaction_rate", "citizen_satisfaction_rate"}],
    }


def candidate_subsets(groups):
    names = list(groups)
    return [list(subset) for size in range(len(names) + 1)
            for subset in combinations(names, size)]


def choose_validation_candidate(candidates):
    """Use validation R2 only; prefer fewer features on an exact tie."""
    return max(candidates, key=lambda row: (row["validation"]["r2"], -len(row["features"])))


def bootstrap_delta(y, base, selected, n_bootstrap=2000):
    rng = np.random.default_rng(20261029)
    samples = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y), len(y))
        actual = y[indices]
        denominator = np.sum((actual - actual.mean()) ** 2)
        if denominator > 0:
            samples.append(float((np.sum((actual - base[indices]) ** 2)
                                  - np.sum((actual - selected[indices]) ** 2)) / denominator))
    return {"n_resamples": n_bootstrap,
            "delta_r2_95_percentile_interval": np.quantile(samples, [0.025, 0.975]).tolist(),
            "method": "Paired held-out-cell bootstrap of seed-mean predictions; not a cluster bootstrap"}


def main():
    source = pd.read_parquet(ROOT / "data/processed/integrated_cell_dataset.parquet")
    lagged = assign_rolling_split(build_lagged_dataset(source))
    frame, base_features, nlp_features = prepare_features(lagged)
    groups = feature_groups(nlp_features)
    train = frame["split"].eq("train")
    val = frame["split"].eq("val")
    test = frame["split"].eq("test")
    fitting = train | val
    output = {
        "experiment": "Exploratory validation-selected LightGBM augmentation without VADER",
        "scope": "NYC, target months January-December 2024 only",
        "selection_rule": "Maximum September-December 2023 validation R2; exact ties use fewer features",
        "selection_uses_test_outcomes": False,
        "test_previously_examined": True,
        "interpretation": "Post-review exploratory refinement; independent future/cross-city confirmation remains necessary",
        "split_counts": frame["split"].value_counts().to_dict(),
        "feature_groups": groups,
        "seeds": SEEDS,
        "results_by_target": {},
    }
    for target in TARGETS:
        candidates = []
        for subset in candidate_subsets(groups):
            columns = base_features + [c for name in subset for c in groups[name]]
            model = make_lightgbm(42).fit(frame.loc[train, columns], frame.loc[train, target])
            candidates.append({"families": subset, "features": columns,
                               "validation": evaluate(frame.loc[val, target], model.predict(frame.loc[val, columns]))})
        chosen = choose_validation_candidate(candidates)
        y = frame.loc[test, target].to_numpy()
        runs, base_predictions, selected_predictions = [], [], []
        for seed in SEEDS:
            base = make_lightgbm(seed).fit(frame.loc[fitting, base_features], frame.loc[fitting, target])
            selected = make_lightgbm(seed).fit(frame.loc[fitting, chosen["features"]], frame.loc[fitting, target])
            pred_base = base.predict(frame.loc[test, base_features])
            pred_selected = selected.predict(frame.loc[test, chosen["features"]])
            base_predictions.append(pred_base)
            selected_predictions.append(pred_selected)
            mb, ms = evaluate(y, pred_base), evaluate(y, pred_selected)
            p_value = None if np.array_equal(pred_base, pred_selected) else float(
                ttest_rel(np.abs(y - pred_base), np.abs(y - pred_selected)).pvalue)
            runs.append({"seed": seed, "baseline": mb, "selected": ms,
                         "delta_r2": ms["r2"] - mb["r2"], "paired_absolute_error_p": p_value})
        no_vader = base_features + [c for family in groups.values() for c in family]
        reference = make_lightgbm(42).fit(frame.loc[fitting, no_vader], frame.loc[fitting, target])
        result = {"validation_candidates": candidates, "selected_families": chosen["families"],
                  "selected_features": chosen["features"], "selected_validation_metrics": chosen["validation"],
                  "primary_seed_42": runs[0], "seed_results": runs,
                  "mean_delta_r2": float(np.mean([r["delta_r2"] for r in runs])),
                  "std_delta_r2": float(np.std([r["delta_r2"] for r in runs], ddof=1)),
                  "all_non_vader_reference": evaluate(y, reference.predict(frame.loc[test, no_vader])),
                  "bootstrap": bootstrap_delta(y, np.mean(base_predictions, axis=0), np.mean(selected_predictions, axis=0))}
        output["results_by_target"][target] = result
        print(target, chosen["families"], json.dumps(result["primary_seed_42"]), flush=True)
    path = ROOT / "reports/metrics/selected_feature_results.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
