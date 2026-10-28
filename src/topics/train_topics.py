"""
Phase 5: Topic Modeling Module (LDA & BERTopic).
Extracts latent municipal resolution themes from NYC 311 narrative texts.
Computes topic coherence (C_v), generates publication figures,
and extracts cell-level topic distribution features for downstream predictive modeling.
Satisfies VIT Review-2 criteria C3, C4, and C5.
"""

import os
import sys
import json
import argparse
import logging
import yaml
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import nltk
from nltk.corpus import stopwords
from gensim.corpora import Dictionary
from gensim.models import LdaModel, CoherenceModel
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def preprocess_text(text: str, stop_words: set) -> list:
    """Tokenizes and cleans text for LDA topic modeling."""
    text = text.lower()
    tokens = re.findall(r"\b[a-z]{3,}\b", text)
    # Filter stopwords and common generic administrative tokens
    custom_stops = {"department", "agency", "nyc", "service", "request", "action", "taken", "closed", "reported", "city"}
    return [t for t in tokens if t not in stop_words and t not in custom_stops]


def plot_lda_topics(lda_model, dictionary, num_topics: int, out_path: str):
    """Generates bar chart of top terms for LDA topics."""
    topics = lda_model.show_topics(num_topics=min(num_topics, 6), num_words=6, formatted=False)
    
    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(15, 8), dpi=150)
    axes = axes.flatten()

    for idx, (t_id, term_weights) in enumerate(topics):
        if idx >= len(axes):
            break
        terms, weights = zip(*term_weights)
        ax = axes[idx]
        ax.barh(terms, weights, color="#3498db")
        ax.set_title(f"Topic {t_id + 1}", fontsize=11, fontweight="bold")
        ax.invert_yaxis()
        ax.set_xlabel("Term Weight", fontsize=9)

    plt.suptitle("Top Term Distributions Across Latent LDA Topics", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    logger.info(f"Saved LDA topic visualization to {out_path}")


def plot_bertopic_themes(topic_info: pd.DataFrame, out_path: str):
    """Generates bar chart of top BERTopic thematic clusters."""
    # Filter out outlier cluster (-1)
    valid_topics = topic_info[topic_info["Topic"] >= 0].head(8)

    plt.figure(figsize=(10, 6), dpi=150)
    names = [n.replace("_", " ")[:35] for n in valid_topics["Name"]]
    sns.barplot(y=names, x=valid_topics["Count"], hue=names, palette="viridis", legend=False)
    plt.title("Dominant Semantic Themes Identified by BERTopic", fontsize=13, fontweight="bold", pad=15)
    plt.xlabel("Assigned Document Count", fontsize=11, labelpad=10)
    plt.ylabel("Extracted Theme Representation", fontsize=11, labelpad=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    logger.info(f"Saved BERTopic visualization to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Run topic modeling for Smart Cities project.")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to config file")
    parser.add_argument("--sample_size", type=int, default=30000, help="Sample size for topic models")
    args = parser.parse_args()

    config = load_config(args.config)
    raw_dir = config["data"]["raw_dir"]
    proc_dir = config["data"]["processed_dir"]
    metrics_dir = "reports/metrics"
    fig_dir = "reports/figures"

    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    nyc311_path = os.path.join(raw_dir, "nyc311_raw.parquet")
    logger.info(f"Loading NYC 311 data from {nyc311_path}...")
    # Load only the fields required for topic construction.  The operational
    # snapshot is now >4.2M rows; reading unused coordinates, agency, status,
    # and identifiers substantially increases memory pressure without adding
    # information to the topic model.
    topic_columns = [
        "created_date",
        "resolution_description",
        "complaint_type",
        "descriptor",
        "borough",
    ]
    df_311 = pd.read_parquet(nyc311_path, columns=topic_columns)

    # 1. Filter and prepare corpus
    df_valid = df_311[df_311["resolution_description"].notna() & (df_311["resolution_description"].str.len() > 10)].copy()
    logger.info(f"Found {len(df_valid):,} valid resolution narrative records")

    created_dt = pd.to_datetime(df_valid["created_date"], errors="coerce")
    df_valid["year"] = created_dt.dt.year
    df_valid["month"] = created_dt.dt.month

    # Composite text: includes complaint type, descriptor, and resolution narrative
    df_valid["composite_text"] = (
        df_valid["complaint_type"].fillna("") + " " +
        df_valid["descriptor"].fillna("") + ": " +
        df_valid["resolution_description"].fillna("")
    )

    # Fit topic models strictly on the lagged experiment's training-period
    # feature months.  Later records are transformed only; they never affect
    # the learned vocabulary, topics, embeddings, or clusters.
    train_year = config["models"]["temporal_split"].get("train_year", 2023)
    topic_train_end_month = config["nlp"]["topics"].get("train_end_month", 7)
    df_topic_train = df_valid[
        (df_valid["year"] == train_year) & (df_valid["month"] <= topic_train_end_month)
    ].copy()
    sample_n = min(args.sample_size, len(df_topic_train))
    df_sample = df_topic_train.sample(n=sample_n, random_state=42).copy()
    logger.info(
        "Sampled %s training-period documents for topic modeling (%d-01 through %d-%02d)",
        f"{sample_n:,}", train_year, train_year, topic_train_end_month,
    )

    # 2. Train LDA Model (Gensim)
    logger.info("Tokenizing texts for LDA...")
    stop_words = set(stopwords.words("english"))
    tokenized_docs = [preprocess_text(txt, stop_words) for txt in df_sample["composite_text"]]
    tokenized_docs = [doc for doc in tokenized_docs if len(doc) >= 3]

    dictionary = Dictionary(tokenized_docs)
    dictionary.filter_extremes(no_below=10, no_above=0.6, keep_n=10000)
    corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]

    num_topics_lda = config["nlp"]["topics"].get("num_topics_lda", 10)
    logger.info(f"Training Gensim LDA model with {num_topics_lda} topics...")
    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics_lda,
        random_state=42,
        passes=5,
        alpha="auto",
        per_word_topics=True,
    )

    # Compute Coherence Score (C_v)
    logger.info("Computing LDA topic coherence (C_v)...")
    coherence_model = CoherenceModel(
        model=lda_model,
        texts=tokenized_docs,
        dictionary=dictionary,
        coherence="c_v",
    )
    lda_coherence_cv = float(coherence_model.get_coherence())
    logger.info(f"LDA C_v Coherence Score: {lda_coherence_cv:.4f}")

    # Extract LDA Topic representations
    lda_topics_dict = {}
    for t_id in range(num_topics_lda):
        top_words = [w for w, _ in lda_model.show_topic(t_id, topn=8)]
        lda_topics_dict[f"Topic_{t_id + 1}"] = top_words

    # 3. Train BERTopic Model
    logger.info("Initializing SentenceTransformer and BERTopic...")
    embedding_model_name = config["nlp"]["topics"].get("bertopic_embedding_model", "all-MiniLM-L6-v2")
    embedding_model = SentenceTransformer(embedding_model_name)

    # Train BERTopic on subset for efficient CPU clustering
    bertopic_docs = df_sample["composite_text"].head(min(15000, len(df_sample))).tolist()
    topic_model = BERTopic(
        embedding_model=embedding_model,
        min_topic_size=30,
        nr_topics=15,
        verbose=True,
    )
    logger.info(f"Fitting BERTopic on {len(bertopic_docs):,} documents...")
    topics, probs = topic_model.fit_transform(bertopic_docs)

    topic_info = topic_model.get_topic_info()
    num_bertopic_clusters = int(len(topic_info[topic_info["Topic"] >= 0]))
    logger.info(f"BERTopic discovered {num_bertopic_clusters} semantic clusters")

    # Extract BERTopic top keywords
    bertopic_dict = {}
    for _, row in topic_info[topic_info["Topic"] >= 0].head(10).iterrows():
        t_id = int(row["Topic"])
        top_terms = [t for t, _ in topic_model.get_topic(t_id)[:6]]
        bertopic_dict[f"Theme_{t_id}"] = {
            "name": row["Name"],
            "count": int(row["Count"]),
            "top_terms": top_terms,
        }

    # 4. Save Metrics & Figures
    metrics_data = {
        "lda": {
            "num_topics": num_topics_lda,
            "coherence_c_v": round(lda_coherence_cv, 4),
            "topics": lda_topics_dict,
            "fit_period": f"{train_year}-01 through {train_year}-{topic_train_end_month:02d}",
            "fit_sample_records": int(sample_n),
            "test_period_text_used_for_fit": False,
        },
        "bertopic": {
            "embedding_model": embedding_model_name,
            "num_topics_discovered": num_bertopic_clusters,
            "themes": bertopic_dict,
            "fit_period": f"{train_year}-01 through {train_year}-{topic_train_end_month:02d}",
            "fit_sample_records": int(len(bertopic_docs)),
            "test_period_text_used_for_fit": False,
        },
    }

    metrics_path = os.path.join(metrics_dir, "topic_coherence.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    logger.info(f"Saved topic coherence metrics to {metrics_path}")

    # Plot LDA Topics
    lda_fig_path = os.path.join(fig_dir, "lda_topic_barchart.png")
    plot_lda_topics(lda_model, dictionary, num_topics=num_topics_lda, out_path=lda_fig_path)

    # Plot BERTopic Themes
    bertopic_fig_path = os.path.join(fig_dir, "bertopic_barchart.png")
    plot_bertopic_themes(topic_info, bertopic_fig_path)

    # 5. Transform all periods with the frozen training-only models.  The
    # repeated agency boilerplate is scored once per unique composite string.
    logger.info("Transforming all municipal cells with the frozen training-only topic models...")
    unique_texts = df_valid["composite_text"].drop_duplicates()

    def dominant_topic(text):
        tokens = preprocess_text(text, stop_words)
        if len(tokens) < 3:
            return 0
        distribution = lda_model.get_document_topics(dictionary.doc2bow(tokens))
        return int(max(distribution, key=lambda item: item[1])[0]) if distribution else 0

    topic_lookup = {text: dominant_topic(text) for text in unique_texts}
    df_valid["dominant_lda_topic"] = df_valid["composite_text"].map(topic_lookup).astype(int)
    bertopic_assignments, _ = topic_model.transform(unique_texts.tolist())
    bertopic_lookup = dict(zip(unique_texts.tolist(), map(int, bertopic_assignments)))
    df_valid["dominant_bertopic_topic"] = df_valid["composite_text"].map(bertopic_lookup).astype(int)
    df_valid["complaint_type_upper"] = df_valid["complaint_type"].str.upper()

    # Topic distribution by cell
    def lda_entropy(values):
        counts = np.bincount(values.astype(int))
        probabilities = counts[counts > 0] / len(values)
        return float(-(probabilities * np.log2(probabilities)).sum()) if len(values) > 1 else 0.0

    cell_topics = df_valid.groupby(["complaint_type_upper", "borough", "year", "month"]).agg(
        dominant_topic_mode=("dominant_lda_topic", lambda x: int(x.mode().iloc[0]) if not x.empty else 0),
        topic_entropy=("dominant_lda_topic", lda_entropy),
        dominant_bertopic_mode=("dominant_bertopic_topic", lambda x: int(x.mode().iloc[0]) if not x.empty else -1),
        bertopic_outlier_rate=("dominant_bertopic_topic", lambda x: float((x == -1).mean())),
    ).reset_index()

    out_cell_topics = os.path.join(proc_dir, "cell_topic_features.parquet")
    cell_topics.to_parquet(out_cell_topics, index=False)
    logger.info(f"Saved cell-level topic features to {out_cell_topics} ({len(cell_topics):,} cells)")

    logger.info("Phase 5 Topic Modeling completed successfully!")


if __name__ == "__main__":
    main()
