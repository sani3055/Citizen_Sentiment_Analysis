"""Multi-seed robustness, bootstrap uncertainty, and subgroup analysis."""

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.train_predictive import prepare_features, make_lightgbm


TARGETS = ["mean_resolution_delay_hours", "repeat_request_rate_14d"]


def metrics(y, pred):
    return {
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
    }


def lightgbm_model(seed):
    return make_lightgbm(seed)


def bootstrap_delta(y, base_pred, aug_pred, n_bootstrap=2000, seed=42):
    rng = np.random.default_rng(seed)
    n = len(y)
    delta_r2 = []
    delta_mae = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        y_b = y[idx]
        if np.unique(y_b).size < 2:
            continue
        delta_r2.append(r2_score(y_b, aug_pred[idx]) - r2_score(y_b, base_pred[idx]))
        delta_mae.append(mean_absolute_error(y_b, base_pred[idx]) - mean_absolute_error(y_b, aug_pred[idx]))

    def summary(values):
        values = np.asarray(values, dtype=float)
        return {
            "mean": float(np.mean(values)),
            "lower_95": float(np.percentile(values, 2.5)),
            "upper_95": float(np.percentile(values, 97.5)),
            "n_bootstrap": int(len(values)),
        }

    return {"delta_r2": summary(delta_r2), "delta_mae": summary(delta_mae)}


def subgroup_metrics(test_df, y, base_pred, aug_pred, column):
    output = {}
    for value, group in test_df.groupby(column, dropna=False):
        idx = group.index.to_numpy()
        # The caller gives a test dataframe with a RangeIndex-aligned prediction.
        positions = test_df.index.get_indexer(idx)
        if len(positions) < 3:
            continue
        y_g = y[positions]
        base_g = base_pred[positions]
        aug_g = aug_pred[positions]
        entry = {
            "n": int(len(positions)),
            "baseline_mae": float(mean_absolute_error(y_g, base_g)),
            "augmented_mae": float(mean_absolute_error(y_g, aug_g)),
            "delta_mae": float(mean_absolute_error(y_g, base_g) - mean_absolute_error(y_g, aug_g)),
        }
        if np.unique(y_g).size > 1:
            entry["baseline_r2"] = float(r2_score(y_g, base_g))
            entry["augmented_r2"] = float(r2_score(y_g, aug_g))
        output[str(value)] = entry
    return output


def main():
    parser = argparse.ArgumentParser(description="Run multi-seed and bootstrap robustness analysis.")
    parser.add_argument("--input", default="data/processed/lagged_cell_dataset.parquet")
    parser.add_argument("--output", default="reports/metrics/robustness_results.json")
    parser.add_argument("--seeds", default="0,1,2,3,4")
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()

    source = pd.read_parquet(args.input)
    encoded, base_features, nlp_features = prepare_features(source)
    augmented_features = base_features + nlp_features
    train_mask = encoded["split"].isin(["train", "val"])
    test_mask = encoded["split"] == "test"
    train_df = encoded.loc[train_mask]
    test_df = encoded.loc[test_mask].reset_index(drop=True)
    encoded_test = encoded.loc[test_mask].reset_index(drop=True)
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]

    output = {
        "experiment": "one_month_lagged_primary_recipe_lightgbm_robustness",
        "train_definition": "Lagged train plus validation cells using the exact primary LightGBM recipe",
        "test_definition": "One-month-ahead 2024 out-of-time target cells",
        "seeds": seeds,
        "bootstrap_replicates": args.bootstrap,
        "results_by_target": {},
    }

    plot_values = []
    for target in TARGETS:
        seed_results = []
        base_predictions = []
        augmented_predictions = []
        y_train = train_df[target].values
        y_test = test_df[target].values
        for seed in seeds:
            base = lightgbm_model(seed).fit(train_df[base_features], y_train)
            aug = lightgbm_model(seed).fit(train_df[augmented_features], y_train)
            base_pred = base.predict(test_df[base_features])
            aug_pred = aug.predict(test_df[augmented_features])
            base_m = metrics(y_test, base_pred)
            aug_m = metrics(y_test, aug_pred)
            seed_results.append({
                "seed": seed,
                "baseline": base_m,
                "augmented": aug_m,
                "delta_r2": float(aug_m["r2"] - base_m["r2"]),
                "delta_mae": float(base_m["mae"] - aug_m["mae"]),
            })
            base_predictions.append(base_pred)
            augmented_predictions.append(aug_pred)

        def aggregate(metric_path):
            values = [row[metric_path[0]][metric_path[1]] for row in seed_results]
            return {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1))}

        base_pred = np.mean(np.vstack(base_predictions), axis=0)
        aug_pred = np.mean(np.vstack(augmented_predictions), axis=0)
        bootstrap = bootstrap_delta(y_test, base_pred, aug_pred, args.bootstrap)
        output["results_by_target"][target] = {
            "per_seed": seed_results,
            "aggregate": {
                "baseline_r2": aggregate(("baseline", "r2")),
                "augmented_r2": aggregate(("augmented", "r2")),
                "delta_r2": {"mean": float(np.mean([x["delta_r2"] for x in seed_results])), "std": float(np.std([x["delta_r2"] for x in seed_results], ddof=1))},
                "delta_mae": {"mean": float(np.mean([x["delta_mae"] for x in seed_results])), "std": float(np.std([x["delta_mae"] for x in seed_results], ddof=1))},
            },
            "bootstrap_95_percent_intervals": bootstrap,
            "mean_prediction_metrics": {
                "baseline": metrics(y_test, base_pred),
                "augmented": metrics(y_test, aug_pred),
            },
            "subgroups": {
                "borough": subgroup_metrics(test_df, y_test, base_pred, aug_pred, "borough"),
                "service": subgroup_metrics(test_df, y_test, base_pred, aug_pred, "complaint_type_upper"),
            },
        }
        plot_values.append((target, output["results_by_target"][target]["aggregate"]["delta_r2"]))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    # The repeat-rate delta is much smaller in magnitude than the delay delta;
    # use outcome-specific panels so the smaller estimate remains visible.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), dpi=150)
    colors = ["#2563eb", "#059669"]
    titles = ["Mean resolution delay (hours)", "14-day repeat-request rate"]
    for index, ((target, result), ax) in enumerate(zip(plot_values, axes)):
        mean = result["mean"]
        std = result["std"]
        ax.bar(["Mean ΔR²"], [mean], yerr=[std], capsize=6,
               color=colors[index], width=0.55)
        ax.axhline(0, color="black", linewidth=0.8)
        pad = max(abs(mean) * 0.25, std * 2.5, 0.003)
        ax.set_ylim(min(0, mean - std - pad), max(0, mean + std + pad))
        ax.set_ylabel("ΔR² (augmented − baseline)" if index == 0 else "")
        ax.set_title(titles[index], fontsize=10)
        ax.text(0, mean, f"{mean:+.4f}", ha="center",
                va="bottom" if mean >= 0 else "top", fontsize=9)
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(axis="x", length=0)
    fig.suptitle("Multi-seed Robustness of NLP Incremental Gain", y=0.99)
    ax.set_ylabel("ΔR² (augmented − baseline)")
    axes[1].set_ylabel("")
    axes[0].set_ylabel("Delta R2 (augmented - baseline)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig("reports/figures/robustness_delta_r2.png", dpi=150)
    plt.close(fig)
    print(f"Wrote robustness metrics to {args.output}")


if __name__ == "__main__":
    main()
