# IMPLEMENTATION PLAN v3 — Citizen Sentiment Analysis of Municipal Services
**Course:** BCSE316L Design of Smart Cities | Project 15, Team 15 | VIT Vellore  
**Guide:** Dr. Kalaavathi B, SCOPE  
**Plan version:** 3.0 — optimised for limited time, Antigravity execution, Review-2 rubric  
**Decisions locked:** CFPB external corpus · Kaggle GPU for Transformer training · ABSA = rule-baseline + classifier

---

## VERIFIED DATASET FACTS (do not change without re-querying)

| Fact | Value | Source |
|---|---|---|
| RSAT endpoint | `5ijn-vbdv` | Live Socrata query |
| RSAT rows (2022–2026 YTD) | **568,816** | Live count |
| RSAT columns | Exactly **11** | Live schema |
| RSAT free-text citizen narrative | **None** — suppressed for PII | Live inspection |
| RSAT `resolution_description` diversity | **17 unique strings** in 200-row sample (8.5%) — agency boilerplate | Live inspection |
| RSAT `overall_satisfaction` | 5-point Likert, used as **sentiment label** | Live schema |
| RSAT `dissatisfaction_reason` | **8 fixed strings**, used as **aspect label** | Live schema |
| RSAT time granularity | `year` + `month` only — no timestamps | Live schema |
| RSAT boroughs | BROOKLYN 193k · QUEENS 147k · MANHATTAN 108k · BRONX 84k · STATEN ISLAND 26k · null 9.6k | Live count |
| NYC 311 endpoint | `erm2-nwe9` | Live Socrata query |
| NYC 311 `closed_date` fill on closed records | **100%** | Live sample n=100 |
| NYC 311 `resolution_description` fill on closed records | **~92%** | Live sample n=100 |
| NYC 311 `resolution_description` diversity | **22 unique** in 50-row sample (44%) — more varied than RSAT | Live sample n=50 |
| NYC 311 `descriptor` mean length | ~17 chars — categorical label, not NLP text | Live sample |
| **⚠ Case mismatch on join key** | RSAT `"Heat/Hot Water"` vs 311 `"HEAT/HOT WATER"` — **must normalise to uppercase before joining** | Live comparison |
| Key packages already installed | torch 2.7.1 · transformers 4.53.0 · pandas 2.3.0 · datasets 5.0.1 · streamlit 1.46.1 · shap 0.52.0 · plotly 6.8.0 · pytest 9.1.1 · nltk 3.9.1 | Live pip list |
| Packages still needed | scikit-learn · gensim · sentence-transformers · bertopic · lightgbm · pyarrow | Verified gap |

---

## METHODOLOGY CORRECTIONS (canonical — supersedes all earlier plans)

| Earlier claim | Corrected fact |
|---|---|
| RSAT `resolution_description` usable as NLP training text | ❌ Only 17 distinct values — agency boilerplate |
| 311 `descriptor` usable for Transformer fine-tuning | ❌ ~17 chars average — categorical label |
| VADER applied to "citizen-written text" | ❌ No citizen text exists; VADER applied to 311 `resolution_description` (agency text) |
| RSAT and 311 share a row-level key | ❌ Join is **aggregate-only** at (complaint_type_upper, borough, year, month) |
| ABSA on citizen narratives | ❌ Reframed: predict `dissatisfaction_reason` (aspect label) from 311 `resolution_description` |
| Transformer fine-tuning on 311 text | ❌ Requires external corpus (CFPB); 311 text used only for inference |

**What the data CAN do — confirmed pipeline:**

```
RSAT overall_satisfaction  →  3-class sentiment label  (ground truth for classification metrics)
RSAT dissatisfaction_reason →  8-class aspect label    (ground truth for ABSA metrics)
311 resolution_description  →  NLP input text          (VADER score, topic model, ABSA classifier input)
CFPB narratives (external)  →  Transformer fine-tune   (then inference on 311 res. text)
(complaint_type_upper, borough, year, month)  →  join key for aggregate integration
```

---

## PHASE EXECUTION ORDER

```
P1 Environment  →  P2 Data Download  →  P3 EDA
                                          ├── P4 VADER baseline
                                          ├── P5 Topic models (LDA + BERTopic)
                                          └── P6 ABSA (rule + classifier)
P2  →  P7 Operational outcomes (delay + repeat rate)
P4 + P5 + P6 + P7  →  P8 Aggregate integration
P8  →  P9 Predictive models (structured vs augmented)  ←  core scientific result
P9  →  P10 Transformer (Kaggle)  →  re-run P9 with Transformer features
P9  →  P11 Dashboard
P11 + P10  →  P12 Tests  →  P13 Final report
```

---

## PHASE 1 — Environment Setup
**Review-2 criterion:** C1 (working environment, documented versions)  
**Status:** Most packages installed system-wide; venv needs creating.

### Tasks
1. Create virtual environment.
2. Install missing packages into venv.
3. Verify every import needed for the pipeline.
4. Print and save versions to `reports/environment.txt`.

### Commands (run exactly in this order)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install scikit-learn>=1.4 gensim>=4.3 sentence-transformers>=2.6 bertopic>=0.16 pyarrow>=15 lightgbm>=4.3 pyyaml>=6.0 tqdm requests
pip install -r requirements.txt --quiet
python -c "import torch, transformers, sklearn, nltk, streamlit, bertopic, gensim, lightgbm, shap, datasets, sentence_transformers, plotly, pyarrow, lightgbm; print('ALL OK')"
python -c "import torch; print('torch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
pip list --format=freeze > reports/environment.txt
```

### If bertopic fails on Windows
```powershell
pip install hdbscan --prefer-binary
pip install bertopic
```

### Expected output
```
ALL OK
torch 2.7.1 | CUDA: False   # (False is fine — Transformer training is on Kaggle)
```

### Completion criteria
- [ ] `reports/environment.txt` exists and lists all packages with versions.
- [ ] All imports in the verification command succeed without error.

---

## PHASE 2 — Data Download
**Review-2 criterion:** C2 (dataset source, size, licence, splits documented)  
**Script:** `src/data/download_data.py`

### What to download
| Dataset | Filter | Expected rows | Output file |
|---|---|---|---|
| RSAT `5ijn-vbdv` | year IN (2023, 2024, 2025) | ~413,000 | `data/raw/rsat_raw.parquet` |
| NYC 311 `erm2-nwe9` | status='Closed', year IN (2023,2024,2025), complaint_type IN top-20 RSAT types | ~1–2M | `data/raw/nyc311_raw.parquet` |

### Key implementation notes for `src/data/download_data.py`
- Use `$limit=50000` + `$offset` loop until empty page.
- Add `time.sleep(0.5)` between pages to avoid rate-limiting.
- Save each page to a list then `pd.concat` → `.to_parquet()`.
- Filter 311 by `complaint_type IN (...)` using SoQL: `$where=status='Closed' AND complaint_type IN ('Illegal Parking','Noise - Residential',...)`.
- After download, assert: `rsat['borough'].notna().all()`, `rsat['complaint_type'].notna().all()`, `rsat['year'].between(2023,2025).all()`.
- Write `reports/data_quality_report.md` with row counts, null counts, date ranges.

### Also write `src/data/validator.py`
```python
def validate_rsat(df):
    assert set(df.columns) >= {'complaint_type','borough','year','month','overall_satisfaction','dissatisfaction_reason'}
    assert df['borough'].notna().all(), "Null boroughs in RSAT"
    assert df['overall_satisfaction'].isin(['Strongly Agree','Agree','Neutral','Disagree','Strongly Disagree']).all()

def validate_311(df):
    assert {'complaint_type','borough','created_date','closed_date','resolution_description'}.issubset(df.columns)
    assert df['closed_date'].notna().all(), "Open records slipped through filter"
    assert (df['created_date'] < df['closed_date']).all(), "Negative delay records exist — fix filter"
```

### Command
```powershell
python src/data/download_data.py --config configs/config.yaml
```

### Completion criteria
- [ ] `data/raw/rsat_raw.parquet` exists, row count 390,000–420,000.
- [ ] `data/raw/nyc311_raw.parquet` exists, row count >500,000.
- [ ] `reports/data_quality_report.md` documents counts, nulls, date ranges.
- [ ] `validate_rsat()` and `validate_311()` pass with zero assertion errors.

---

## PHASE 3 — EDA
**Review-2 criterion:** C2 (class distribution), C5 (labelled graphs)  
**Script:** `src/data/eda.py`

### Required outputs — every figure must have title, axis labels, legend, caption
| Figure | Content |
|---|---|
| `reports/figures/rsat_satisfaction_dist.png` | Bar chart of `overall_satisfaction` counts (5 classes) |
| `reports/figures/rsat_aspect_dist.png` | Horizontal bar of `dissatisfaction_reason` counts |
| `reports/figures/rsat_service_heatmap.png` | Heatmap: top-15 services × borough, coloured by negative-satisfaction rate |
| `reports/figures/nyc311_delay_hist.png` | Log-scale histogram of `delay_hours` per top-5 services |
| `reports/figures/nyc311_monthly_volume.png` | Line chart: monthly request count by borough (2023–2025) |
| `reports/figures/cell_coverage_heatmap.png` | Heatmap: number of RSAT responses per (service × borough) cell |

### Key EDA statistics to print and save in `reports/eda/eda_summary.md`
- RSAT class distribution (count + %) for `overall_satisfaction`.
- Top-5 and bottom-5 services by negative satisfaction rate.
- Number of (service × borough × month) cells with ≥10 RSAT responses (expected ≥1,000).
- 311 `resolution_description`: total rows, % with text, unique string count.
- Delay outlier thresholds (95th, 99th percentile in hours).

### Command
```powershell
python src/data/eda.py --config configs/config.yaml
```

### Completion criteria
- [ ] All 6 figures exist, saved at 150 DPI minimum.
- [ ] `eda_summary.md` documents all statistics above.
- [ ] Cell count ≥1,000 confirmed — if fewer, lower `min_cell_samples` in config.

---

## PHASE 4 — VADER Baseline
**Review-2 criterion:** C3 (baseline), C4 (measured parameters)  
**Script:** `src/sentiment/vader_baseline.py`

### Framing (important — document this in the report)
VADER is applied to **NYC 311 `resolution_description`** (agency closing text). This is the only text field with sufficient linguistic variety. VADER operates as:
1. A **feature engineer**: produces `vader_compound` per 311 record → aggregated to cell mean `mean_vader_score`.
2. A **classification baseline**: compound score mapped to {Negative, Neutral, Positive} and compared against RSAT `overall_satisfaction` labels at the cell level. This comparison is methodologically indirect (agency text vs. citizen label) — state this limitation explicitly.

### Implementation
```python
# src/sentiment/vader_baseline.py
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd, json, matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

# Load
df311 = pd.read_parquet("data/raw/nyc311_raw.parquet")
rsat  = pd.read_parquet("data/raw/rsat_raw.parquet")

# VADER score every 311 resolution_description
sia = SentimentIntensityAnalyzer()
df311["vader_compound"] = df311["resolution_description"].fillna("").apply(lambda t: sia.polarity_scores(t)["compound"])

# Map to 3-class
def map_sentiment(score):
    if score >= 0.05:  return "Positive"
    if score <= -0.05: return "Negative"
    return "Neutral"
df311["vader_label"] = df311["vader_compound"].apply(map_sentiment)

# Save feature output
df311.to_parquet("data/processed/nyc311_with_vader.parquet", index=False)

# Aggregate to cell level
df311["complaint_type_upper"] = df311["complaint_type"].str.upper()
cell_vader = df311.groupby(["complaint_type_upper","borough","year","month"])["vader_compound"].mean().reset_index()
cell_vader.columns = ["complaint_type_upper","borough","year","month","mean_vader_score"]
cell_vader.to_parquet("data/processed/cell_vader_features.parquet", index=False)

# Classification eval against RSAT
rsat["complaint_type_upper"] = rsat["complaint_type"].str.upper()
rsat["sentiment_label"] = rsat["overall_satisfaction"].map({
    "Strongly Agree":"Positive","Agree":"Positive",
    "Neutral":"Neutral",
    "Disagree":"Negative","Strongly Disagree":"Negative"
})
# ... merge cell_vader with cell-level RSAT majority label, compute metrics
# Save metrics
metrics = {...}  # fill from classification_report
json.dump(metrics, open("reports/metrics/vader_metrics.json","w"), indent=2)
```

### Expected outputs
- `data/processed/nyc311_with_vader.parquet` — 311 rows + `vader_compound`, `vader_label`
- `data/processed/cell_vader_features.parquet` — cell-level `mean_vader_score`
- `reports/metrics/vader_metrics.json` — Accuracy, Macro-F1, per-class F1
- `reports/figures/vader_confusion_matrix.png`

### Completion criteria
- [ ] VADER score computed for all records (including empty → score=0.0).
- [ ] `vader_metrics.json` saved with Accuracy, Macro-F1, and per-class F1.
- [ ] Confusion matrix figure saved.
- [ ] Comment in report: "VADER operates on agency closing text; comparison to citizen satisfaction labels is methodologically indirect."

---

## PHASE 5 — Topic Modelling: LDA and BERTopic
**Review-2 criterion:** C3 (baseline + alternative), C5 (labelled results)  
**Scripts:** `src/topics/lda_model.py`, `src/topics/bertopic_model.py`, `src/topics/compare_topics.py`

### Input text construction
```python
df311["topic_text"] = (
    df311["complaint_type"].fillna("") + " " +
    df311["descriptor"].fillna("") + " " +
    df311["resolution_description"].fillna("")
)
```

### LDA implementation
- Preprocess: lowercase, remove stopwords (`nltk.corpus.stopwords`), tokenise.
- Grid search K ∈ {5, 8, 10, 15, 20} — compute `gensim.models.coherencemodel` Cv coherence.
- Pick K with highest Cv. Save top-10 keywords per topic.
- Generate `lda_topic_distribution` matrix (N_records × K) — save to parquet.

### BERTopic implementation
```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

model = BERTopic(embedding_model=SentenceTransformer("all-MiniLM-L6-v2"),
                 nr_topics="auto", calculate_probabilities=True)
topics, probs = model.fit_transform(texts)
```
- Save topic keywords to `reports/topics_summary.md`.
- Save per-record topic assignment + probability to parquet.
- **Memory note:** sample 100,000 records if full dataset causes OOM.

### Outputs
| File | Content |
|---|---|
| `reports/metrics/topic_coherence.json` | Cv score per K for LDA; BERTopic topic count + top coherence |
| `reports/figures/lda_coherence_curve.png` | Cv vs K line chart |
| `reports/figures/bertopic_visualisation.png` | BERTopic intertopic distance map or bar chart of top topics |
| `data/processed/nyc311_with_topics.parquet` | 311 rows + `lda_topic` (int) + `lda_probs` (array) + `bertopic_topic` (int) |
| `reports/topics_summary.md` | Top-10 words per topic for both models; human-assigned topic names |

### Completion criteria
- [ ] LDA Cv coherence curve saved for 5 K values.
- [ ] At least 5 interpretable topics identified and named in `topics_summary.md`.
- [ ] BERTopic topic count reported.
- [ ] Both models' topic distributions appended to 311 parquet.

---

## PHASE 6 — ABSA: Rule Baseline + Classifier
**Review-2 criterion:** C3 (baseline + alternative), C4 (measured parameters)  
**Scripts:** `src/absa/absa_rule_baseline.py`, `src/absa/absa_classifier.py`, `src/absa/evaluate_absa.py`

### Data: rows used
Filter RSAT to `overall_satisfaction` ∈ {Disagree, Strongly Disagree} **and** `dissatisfaction_reason` not null/blank and not "Other" → N ≈ **236,000 rows** (8 classes reduced to 7 interpretable ones; "Other" kept as class 8 but flagged).

Join with 311 on `(complaint_type_upper, borough, year, month)` to bring in `resolution_description` as text feature.

### Target label encoding
```python
ASPECT_MAP = {
    "The Agency did not correct the issue.": 0,
    "The Agency did not correct the issue and this Service Request should be reopened.": 1,
    "Status updates were unhelpful, inaccurate, incomplete, and/or confusing.": 2,
    "The Agency corrected the issue, but they took too long to respond.": 3,
    "The Agency said I did not provide complete or accurate information, but I did.": 4,
    "The Agency did not provide enough status updates.": 5,
    "The Agency corrected the issue, but the work they did was unsatisfactory.": 6,
    "Other": 7,
}
```

### Train/test split (chronological — mandatory)
- Train: `year` ∈ {2023, 2024}  
- Test: `year` = 2025

### Baseline A — Rule-based keyword mapping (`src/absa/absa_rule_baseline.py`)
```python
RULES = {
    0: ["not correct","did not fix","unresolved","not addressed"],
    1: ["reopen","still ongoing","not fixed","same problem"],
    2: ["confusing","inaccurate","unhelpful","incomplete update"],
    3: ["too long","slow","delayed","took long"],
    4: ["did not provide","incomplete information","wrong info"],
    5: ["not enough updates","no status","never heard"],
    6: ["unsatisfactory work","poor quality","bad repair"],
    7: [],  # catch-all
}
```
Map to first matching rule; if none → class 7. Evaluate on test set. Save Macro-F1 to metrics JSON.

### Alternative B — TF-IDF + Logistic Regression (`src/absa/absa_classifier.py`)
```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=20000, ngram_range=(1,2))),
    ("clf",   LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0))
])
pipe.fit(X_train, y_train)
```

### Alternative C — BERT fine-tune (run on Kaggle, checkpoint downloaded to `artifacts/models/bert_absa/`)
- Model: `bert-base-uncased`
- Tokenise `resolution_description` (max_len=128)
- 3 epochs, AdamW, lr=2e-5, batch=16, class-weighted CrossEntropyLoss
- Save `trainer.save_model("bert_absa_checkpoint")` → download to local `artifacts/models/bert_absa/`

### Evaluate all three on 2025 test set
```python
# Save to reports/metrics/absa_metrics.json
{
  "rule_based":      {"accuracy": ..., "macro_f1": ..., "per_class_f1": {...}},
  "tfidf_logreg":   {"accuracy": ..., "macro_f1": ..., "per_class_f1": {...}},
  "bert_fine_tuned": {"accuracy": ..., "macro_f1": ..., "per_class_f1": {...}}
}
```

### Outputs
- `reports/metrics/absa_metrics.json`
- `reports/figures/absa_confusion_matrix_tfidf.png`
- `reports/figures/absa_confusion_matrix_bert.png`
- `data/processed/rsat_with_absa_labels.parquet` — RSAT rows + `predicted_aspect` (int)

### Completion criteria
- [ ] Rule baseline Macro-F1 computed and saved.
- [ ] TF-IDF + LR Macro-F1 computed and saved.
- [ ] BERT Macro-F1 computed and saved (can be done after Kaggle training in Phase 10).
- [ ] All three results in single `absa_metrics.json`.
- [ ] Class-imbalance note written in report (class 0 has 135k rows vs. class 6 with 2.9k).

---

## PHASE 7 — Operational Outcomes
**Review-2 criterion:** C2 (dataset preprocessing), C4 (parameters measured)  
**Scripts:** `src/outcomes/calculate_outcomes.py`, `src/outcomes/repeat_detection.py`

### Resolution delay
```python
df = pd.read_parquet("data/raw/nyc311_raw.parquet")
df["created_date"] = pd.to_datetime(df["created_date"])
df["closed_date"]  = pd.to_datetime(df["closed_date"])
df["delay_hours"]  = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600

# Clean
df = df[df["delay_hours"] > 0]           # remove negative delays
p99 = df["delay_hours"].quantile(0.99)
df["delay_hours_w"] = df["delay_hours"].clip(upper=p99)  # winsorised
df["complaint_type_upper"] = df["complaint_type"].str.upper()
```

### Repeat request rate
```python
# src/outcomes/repeat_detection.py
# Sort by (incident_address, complaint_type_upper, created_date)
# Flag row j as repeat if prior row i at same address+type within W=14 days
WINDOW_DAYS = 14
df = df.sort_values(["incident_address","complaint_type_upper","created_date"])
df["is_repeat"] = False
for idx, grp in df.groupby(["incident_address","complaint_type_upper"]):
    dates = grp["created_date"].values
    repeats = [False] + [
        (dates[i] - dates[i-1]).astype("timedelta64[D]").astype(int) <= WINDOW_DAYS
        for i in range(1, len(dates))
    ]
    df.loc[grp.index, "is_repeat"] = repeats
```
> **Note:** The above logic runs in O(N) per group but may be slow for very large groups. If runtime exceeds 30 minutes, switch to a vectorised pandas `shift()` approach (documented in inline comments in the script).

### Aggregate to cell level
```python
cell_outcomes = df.groupby(["complaint_type_upper","borough","year","month"]).agg(
    request_count      = ("unique_key","count"),
    mean_delay_hours   = ("delay_hours_w","mean"),
    median_delay_hours = ("delay_hours_w","median"),
    closed_rate        = ("delay_hours","count"),   # proxy: all rows here are closed
    repeat_rate_14d    = ("is_repeat","mean"),
).reset_index()
cell_outcomes.to_parquet("data/processed/nyc311_outcomes.parquet", index=False)
```

### Outputs
- `data/processed/nyc311_outcomes.parquet`
- `reports/outcomes_summary.md` — delay stats per top-10 services, repeat rate per service
- `reports/figures/delay_by_service.png`
- `reports/figures/repeat_rate_by_borough.png`

### Completion criteria
- [ ] Zero NaN in `mean_delay_hours` and `repeat_rate_14d`.
- [ ] Winsorisation percentile and threshold documented in `outcomes_summary.md`.
- [ ] Both figures saved and labelled.

---

## PHASE 8 — Aggregate Integration
**Review-2 criterion:** C3 (methodology detail), C2 (documented splits)  
**Script:** `src/outcomes/aggregate_integration.py`

### Join key (mandatory normalisation step)
```python
# All datasets must use complaint_type_upper before joining
rsat["complaint_type_upper"] = rsat["complaint_type"].str.upper()
# 311 already normalised in Phases 7 and 4
```

### Features per cell
```python
# From RSAT
rsat["sentiment_3class"] = rsat["overall_satisfaction"].map({
    "Strongly Agree":"Positive","Agree":"Positive",
    "Neutral":"Neutral",
    "Disagree":"Negative","Strongly Disagree":"Negative"
})
cell_rsat = rsat.groupby(["complaint_type_upper","borough","year","month"]).agg(
    rsat_count            = ("unique_key","count"),
    neg_satisfaction_rate = ("sentiment_3class", lambda x: (x=="Negative").mean()),
    pos_satisfaction_rate = ("sentiment_3class", lambda x: (x=="Positive").mean()),
    **{f"pct_aspect_{i}": ("dissatisfaction_reason", lambda x,i=i: (x==label).mean())
       for i, label in enumerate(ASPECT_MAP)}
).reset_index()
```

### Join and filter
```python
cells = (cell_outcomes
    .merge(cell_rsat,        on=["complaint_type_upper","borough","year","month"], how="inner")
    .merge(cell_vader,       on=["complaint_type_upper","borough","year","month"], how="inner")
    .merge(cell_topics,      on=["complaint_type_upper","borough","year","month"], how="left")
)
cells = cells[cells["request_count"] >= 10]
cells = cells[cells["rsat_count"]    >= 10]
cells.to_parquet("data/processed/integrated_cells.parquet", index=False)
```

### Integration diagnostics (save to `reports/integration_diagnostics.md`)
- Total cells before and after filter.
- Coverage by service (top-20 rows).
- Coverage by borough.
- Missing rate per feature column.

### Completion criteria
- [ ] `integrated_cells.parquet` has ≥1,000 rows (if fewer: lower `min_cell_samples` to 5 in config).
- [ ] Zero NaN in outcome columns and core feature columns.
- [ ] Diagnostics file written.

---

## PHASE 9 — Predictive Modelling (Core Scientific Contribution)
**Review-2 criterion:** C3 (baseline + alternative), C4 (measured parameters), C5 (labelled graphs), C6 (conclusion)  
**Scripts:** `src/models/baseline_model.py`, `src/models/augmented_model.py`, `src/models/evaluate_models.py`

### Chronological split (no shuffling)
```python
train = cells[cells["year"] == 2023]
val   = cells[cells["year"] == 2024]
test  = cells[cells["year"] == 2025]
# If 2023 alone is too small, use train=2023+2024, test=2025 (2-split)
```

### Feature sets
```python
STRUCTURED_FEATURES = [
    "request_count", "closed_rate",
    # one-hot encoded complaint_type_upper, borough, month
]
SENTIMENT_FEATURES  = ["neg_satisfaction_rate","pos_satisfaction_rate","mean_vader_score"]
ASPECT_FEATURES     = [f"pct_aspect_{i}" for i in range(8)]
TOPIC_FEATURES      = [f"lda_topic_{i}" for i in range(best_k)]

F0 = STRUCTURED_FEATURES                                              # baseline
F1 = STRUCTURED_FEATURES + SENTIMENT_FEATURES + ASPECT_FEATURES + TOPIC_FEATURES  # augmented
```

### Models — fit one baseline and one augmented for each algorithm
```python
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb

ALGORITHMS = {
    "ridge":    Ridge(alpha=1.0),
    "rf":       RandomForestRegressor(n_estimators=200, random_state=42),
    "lgbm":     lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, random_state=42),
}
```
Train each on `(train+val)`, evaluate on `test`. **Never tune on test set.**

### Targets
- `mean_delay_hours` (regression)
- `repeat_rate_14d` (regression)

### Metrics
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

def evaluate(y_true, y_pred, name):
    return {
        "model": name,
        "MAE":  round(mean_absolute_error(y_true, y_pred), 4),
        "RMSE": round(np.sqrt(mean_squared_error(y_true, y_pred)), 4),
        "R2":   round(r2_score(y_true, y_pred), 4),
    }
```

### Delta calculation
```python
delta_mae = results["f0_lgbm"]["MAE"] - results["f1_lgbm"]["MAE"]
# Positive Δ means augmented model is better
```

### SHAP importance plot for best augmented model
```python
import shap
explainer = shap.TreeExplainer(best_lgbm_f1)
shap_values = explainer(X_test_f1)
shap.plots.beeswarm(shap_values, max_display=15, show=False)
plt.savefig("reports/figures/shap_summary_delay.png", dpi=150, bbox_inches="tight")
```

### Results file structure (`reports/metrics/predictive_modeling_results.json`)
```json
{
  "delay_hours": {
    "f0_ridge":  {"MAE": ..., "RMSE": ..., "R2": ...},
    "f0_rf":     {"MAE": ..., "RMSE": ..., "R2": ...},
    "f0_lgbm":   {"MAE": ..., "RMSE": ..., "R2": ...},
    "f1_ridge":  {"MAE": ..., "RMSE": ..., "R2": ...},
    "f1_rf":     {"MAE": ..., "RMSE": ..., "R2": ...},
    "f1_lgbm":   {"MAE": ..., "RMSE": ..., "R2": ...},
    "delta_mae_best": ...
  },
  "repeat_rate_14d": { ... }
}
```

### Figures required
- `reports/figures/model_comparison_bar.png` — grouped bar: MAE for f0 vs f1, 3 algorithms, 2 targets
- `reports/figures/shap_summary_delay.png`
- `reports/figures/shap_summary_repeat.png`

### Completion criteria
- [ ] 6 models (3 algorithms × f0/f1) evaluated on 2025 test set for both targets.
- [ ] `predictive_modeling_results.json` saved.
- [ ] Δ is computed and non-zero (direction doesn't matter — both outcomes are valid findings).
- [ ] SHAP plot for best augmented model saved.
- [ ] Zero 2025 data in training.

---

## PHASE 10 — Transformer Sentiment (Kaggle)
**Review-2 criterion:** C3 (methodology detail — Transformer alternative)  
**Scripts:** `src/sentiment/dataset.py`, `src/sentiment/train_transformer.py`, `src/sentiment/evaluate_sentiment.py`

### External corpus: CFPB Consumer Finance Complaints
```python
from datasets import load_dataset
ds = load_dataset("cfpb/consumer-finance-complaints")
# Fields: 'Consumer complaint narrative' (text), 'Timely response?' (Yes/No), 'Consumer disputed?' (Yes/No)
# Label mapping: Timely=Yes AND Disputed=No → Positive; Timely=No OR Disputed=Yes → Negative; else Neutral
# Filter: keep only rows where 'Consumer complaint narrative' is not empty
# Sample: 50,000 train rows (balanced 3-class) to keep Kaggle training time ≤2h per model
```

### Kaggle notebook setup
1. Create a new notebook at kaggle.com.
2. Upload `src/sentiment/dataset.py` and `src/sentiment/train_transformer.py` as dataset files or paste into cells.
3. Run training — checkpoint saves to `/kaggle/working/bert_sentiment_ckpt/`.
4. Download checkpoint zip → copy to `artifacts/models/bert_sentiment/` locally.

### Training script skeleton (`src/sentiment/train_transformer.py`)
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import torch
from datasets import Dataset

MODEL_NAME  = "bert-base-uncased"  # swap to "roberta-base" for second run
NUM_LABELS  = 3
LABEL_MAP   = {"Negative": 0, "Neutral": 1, "Positive": 2}

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model     = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=NUM_LABELS)

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, max_length=128, padding="max_length")

args = TrainingArguments(
    output_dir="bert_sentiment_ckpt",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    learning_rate=2e-5,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    fp16=True,  # Kaggle T4 supports fp16
)
trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds)
trainer.train()
trainer.save_model("bert_sentiment_ckpt")
```

### Apply locally after checkpoint download
```python
# src/sentiment/evaluate_sentiment.py
from transformers import pipeline
clf = pipeline("text-classification", model="artifacts/models/bert_sentiment", device=-1)
df311["bert_sentiment"] = [clf(t[:512])[0]["label"] for t in df311["resolution_description"]]
```

### Metrics output (`reports/metrics/transformer_metrics.json`)
```json
{
  "dataset": "CFPB Consumer Finance Complaints (50k sample)",
  "test_split": "chronological 80/20",
  "vader":  {"accuracy": ..., "macro_f1": ...},
  "bert":   {"accuracy": ..., "macro_f1": ...},
  "roberta":{"accuracy": ..., "macro_f1": ...}
}
```

### Figure
- `reports/figures/transformer_vs_vader_comparison.png` — grouped bar: Accuracy + Macro-F1 for 3 models

### Completion criteria
- [ ] BERT checkpoint in `artifacts/models/bert_sentiment/`.
- [ ] RoBERTa checkpoint in `artifacts/models/roberta_sentiment/`.
- [ ] `transformer_metrics.json` saved with all 3 model scores.
- [ ] Inference applied to 311 `resolution_description` texts; `bert_sentiment` column added to 311 parquet.

---

## PHASE 11 — Dual Streamlit Dashboard
**Review-2 criterion:** C1 (live demo), C5 (labelled graphs)  
**Entry point:** `streamlit run dashboard/app.py`

### `dashboard/app.py` — structure
```python
import streamlit as st
st.set_page_config(page_title="NYC Municipal Sentiment Analyser", layout="wide")

page = st.sidebar.radio("View", ["📊 Government Dashboard", "🏙️ Citizen Dashboard"])
if page == "📊 Government Dashboard":
    from dashboard.views.government_view import render
    render()
else:
    from dashboard.views.citizen_view import render
    render()
```

### Government view (`dashboard/views/government_view.py`)
| Component | Description |
|---|---|
| KPI cards (row 1) | Top-3 services by mean delay / top-3 by negative satisfaction rate |
| Ranked table | Top-20 cells by predicted delay (LightGBM f1), with borough, service, delay, RSAT neg rate |
| Aspect breakdown chart | Horizontal stacked bar: aspect proportions per top-10 services |
| SHAP chart | Bar chart of top-15 SHAP feature importances (loaded from saved values) |
| Data caveat | `st.info()` box: "RSAT is an opt-in survey (~1.7% of 311 requests). Results reflect respondents, not all NYC residents." |

### Citizen view (`dashboard/views/citizen_view.py`)
| Component | Description |
|---|---|
| Borough selector | `st.selectbox` for borough |
| Service selector | `st.selectbox` filtered by available services in selected borough |
| Satisfaction gauge | `plotly.graph_objects.Indicator` showing % dissatisfied |
| Resolution time trend | Line chart: `mean_delay_hours` over months (2023–2025) |
| Top dissatisfaction reason | Bar chart of aspect proportions for selected service+borough |
| Data caveat banner | Same as above |

### Completion criteria
- [ ] `streamlit run dashboard/app.py` launches without error.
- [ ] Both views render with data from `data/processed/integrated_cells.parquet`.
- [ ] All charts have titles, axis labels, and legends.
- [ ] No hardcoded dummy data.

---

## PHASE 12 — Tests
**Review-2 criterion:** C1 (reproducibility)  
**Command:** `pytest tests/ -v --tb=short`

### `tests/test_data.py`
- Test delay calculation: 2-row synthetic df → verify `delay_hours` correct.
- Test winsorisation: check 99th percentile clipping.
- Test case normalisation: `"Heat/Hot Water".upper() == "HEAT/HOT WATER"`.
- Test RSAT validator: assert fails on null borough.

### `tests/test_models.py`
- Test VADER scoring: known positive text → compound > 0.
- Test Ridge regression: synthetic 10-row data → fit and predict without error.
- Test cell aggregation: 20-row synthetic RSAT → correct neg_satisfaction_rate.

### `tests/test_pipeline.py`
- Load `integrated_cells.parquet` → verify shape, no NaN in key columns.
- Fit LightGBM f0 and f1 on first 50 rows → predict on next 10 → verify output is numeric.

### Completion criteria
- [ ] All tests pass: `pytest tests/ -v` shows 0 failures.
- [ ] Output saved: `pytest tests/ -v > reports/test_results.txt`.

---

## PHASE 13 — Final Report
**Review-2 criterion:** C5 (results + graphs), C6 (conclusions), C7 (publication status)

### `reports/FINAL_PROJECT_REPORT.md` — required sections
1. **Abstract** (150 words max)
2. **Dataset summary table** — sources, rows, columns, licence, class distribution
3. **Method diagram** — text-based or embedded figure
4. **Results: Sentiment classification** — table from `vader_metrics.json` and `transformer_metrics.json`
5. **Results: ABSA** — table from `absa_metrics.json`
6. **Results: Topic modelling** — coherence table from `topic_coherence.json`
7. **Results: Predictive modelling** — table from `predictive_modeling_results.json`; Δ values highlighted
8. **SHAP interpretation** — embed `shap_summary_delay.png`; discuss top-3 features
9. **Limitations** — must include: opt-in bias, agency text not citizen text, predictive association not causality
10. **Conclusion** — answers research question with actual Δ value
11. **Future work** — 3 specific technically grounded items

### `RUBRIC_EVIDENCE_CHECKLIST.md` — update all C1–C7 rows
Each row must link to a specific file in `reports/metrics/` or `reports/figures/`.

### Completion criteria
- [ ] Every number in the report is traceable to a JSON file in `reports/metrics/`.
- [ ] Every figure caption describes what is shown and cites the data source.
- [ ] Conclusion contains the actual Δ value from `predictive_modeling_results.json`.
- [ ] Limitations section explicitly states "predictive association, not causality."

---

## RUBRIC-TO-PHASE MAPPING (Review-2, 60 marks)

| Criterion | Marks | Primary Phase | Evidence File |
|---|:---:|---|---|
| C1: Working environment + reproducibility | 8 | P1, P12 | `reports/environment.txt`, `pytest` output |
| C2: Dataset justified + documented | 6 | P2, P3 | `reports/data_quality_report.md`, `eda_summary.md` |
| C3: Methodology detail (baseline + alt) | 12 | P4–P10 | `src/` scripts, `configs/config.yaml` |
| C4: Parameters measured with units | 8 | P4, P5, P6, P7, P9 | All JSON files in `reports/metrics/` |
| C5: Labelled graphs + tables | 12 | P3, P5, P9, P11 | All PNG files in `reports/figures/` |
| C6: Conclusion answers research Q | 6 | P13 | `FINAL_PROJECT_REPORT.md` §10 |
| C7: Publication status | 8 | P13 | Manuscript updated with actual results |

---

## FIRST STEPS FOR GEMINI PRO TO EXECUTE IMMEDIATELY

Run these commands in order. Do not proceed to Phase 2 until all Phase 1 checks pass.

```powershell
# Step 1 — Create and activate venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Step 2 — Install missing packages (most are already installed system-wide but need to be in venv)
pip install --upgrade pip
pip install scikit-learn pyarrow gensim sentence-transformers bertopic lightgbm pyyaml tqdm requests
pip install -r requirements.txt --quiet

# Step 3 — Verify all imports
python -c "
import torch, transformers, sklearn, nltk, streamlit
import bertopic, gensim, lightgbm, shap, datasets
import sentence_transformers, plotly, pyarrow
print('ALL IMPORTS OK')
print('torch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
import sklearn; print('sklearn:', sklearn.__version__)
import lightgbm; print('lightgbm:', lightgbm.__version__)
import bertopic; print('bertopic:', bertopic.__version__)
"

# Step 4 — Save environment snapshot
pip list --format=freeze > reports/environment.txt
python -c "print(open('reports/environment.txt').read()[:500])"

# Step 5 — Download NLTK VADER lexicon (needed for Phase 4)
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('stopwords')"
```

**Expected Phase 1 completion output:**
```
ALL IMPORTS OK
torch: 2.7.1 | CUDA: False
sklearn: 1.x.x
lightgbm: 4.x.x
bertopic: 0.16.x
[nltk_data] Downloading package vader_lexicon ... Done
[nltk_data] Downloading package stopwords ... Done
```

After Phase 1 completes, move directly to writing and running `src/data/download_data.py`.
