"""Role-based Streamlit dashboard for municipal operations and residents."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "integrated_cell_dataset.parquet"
PRIORITY_QUEUE_PATH = ROOT / "data" / "processed" / "heldout_priority_queue.parquet"
METRICS_DIR = ROOT / "reports" / "metrics"

st.set_page_config(page_title="NYC Civic Insight Hub", page_icon="🏙️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.stApp { background:#0b1220; color:#e7eef7; }
.block-container { max-width:1450px; padding-top:2rem; padding-bottom:3rem; }
.hero { padding:1.5rem 1.7rem; border-radius:18px; background:linear-gradient(115deg,#102a43 0%,#14566b 100%); color:#f4fbff; margin-bottom:1rem; box-shadow:0 8px 24px rgba(0,0,0,.28); }
.hero .eyebrow { text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; font-weight:700; color:#8ee6ff; margin-bottom:.35rem; }
.hero h1 { margin:0; font-size:2.2rem; line-height:1.1; } .hero p { margin:.5rem 0 0; color:#d6eff7; font-size:1rem; }
.notice { padding:.85rem 1rem; border-radius:12px; background:#122a39; border:1px solid #28516a; border-left:5px solid #4cc9f0; color:#d9f3fb; margin-bottom:1.1rem; }
.section-note { color:#a9bbca; font-size:.9rem; margin-top:-.45rem; margin-bottom:.8rem; }
.section-title { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-top:1.25rem; margin-bottom:.35rem; }
.section-title h2 { margin:0; color:#f1f7fb; font-size:1.25rem; }
.pill { display:inline-block; padding:.28rem .65rem; border-radius:999px; background:#17364a; border:1px solid #2c6680; color:#8ee6ff; font-size:.75rem; font-weight:700; letter-spacing:.03em; }
section[data-testid="stSidebar"] { background:#0f1a2a; border-right:1px solid #263b52; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * { color:#e7eef7 !important; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color:#c3d2df !important; }
div[data-baseweb="select"] > div { background:#172335 !important; border-color:#38536b !important; color:#e7eef7 !important; }
div[data-baseweb="select"] span, div[data-baseweb="select"] input { color:#e7eef7 !important; }
div[data-baseweb="popover"] { background:#172335 !important; border-color:#38536b !important; }
div[data-baseweb="popover"] * { color:#e7eef7 !important; }
div[data-testid="stMetric"] { background:#111c2c; border:1px solid #294158; border-radius:14px; padding:.85rem 1rem; box-shadow:0 4px 14px rgba(0,0,0,.22); }
div[data-testid="stMetric"]:hover { border-color:#4cc9f0; transform:translateY(-1px); transition:all .15s ease; }
div[data-testid="stMetricLabel"] p, div[data-testid="stMetricLabel"] * { color:#a9bbca !important; font-size:.82rem; }
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * { color:#f1f7fb !important; }
div[data-testid="stDataFrame"] { border:1px solid #294158; border-radius:12px; overflow:hidden; }
div.stDownloadButton > button { background:#17364a; color:#e7f8ff; border:1px solid #2c6680; border-radius:10px; font-weight:700; }
div.stDownloadButton > button:hover { background:#21526b; border-color:#8ee6ff; color:white; }
button[data-baseweb="tab"] { color:#a9bbca !important; }
button[data-baseweb="tab"][aria-selected="true"] { color:#4cc9f0 !important; }
button[data-baseweb="tab"] { font-weight:600; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_cells():
    if not DATA_PATH.exists():
        return pd.DataFrame()
    df = pd.read_parquet(DATA_PATH)
    df["period"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return df


@st.cache_data
def load_priority_queue():
    if not PRIORITY_QUEUE_PATH.exists():
        return pd.DataFrame()
    queue = pd.read_parquet(PRIORITY_QUEUE_PATH)
    queue["period"] = pd.to_datetime(
        dict(year=queue["target_year"], month=queue["target_month"], day=1)
    )
    return queue


@st.cache_data
def load_json(name):
    path = METRICS_DIR / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def corrected_finding(review_metrics):
    naive = review_metrics.get("naive_baselines", {})
    delay = naive.get("mean_resolution_delay_hours", {}).get("last_value", {}).get("r2")
    repeat = naive.get("repeat_request_rate_14d", {}).get("last_value", {}).get("r2")
    if delay is None or repeat is None:
        return None
    return f"Research finding: the previous-month persistence baseline is stronger than the augmented model (delay R2 {delay:.3f}; repeat-rate R2 {repeat:.3f})."


def style_chart(fig, height=320):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=12, r=12, t=42, b=12),
        colorway=["#4cc9f0", "#f6bd60", "#ef6f6c", "#9b8afb"],
        font=dict(family="Arial", color="#d8e6f0", size=12),
        title_font=dict(color="#f1f7fb", size=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color="#c3d2df")),
    )
    fig.update_xaxes(showgrid=False, linecolor="#38536b", tickfont=dict(color="#a9bbca"), title_font=dict(color="#c3d2df"))
    fig.update_yaxes(gridcolor="#263b52", zeroline=False, tickfont=dict(color="#a9bbca"), title_font=dict(color="#c3d2df"))
    return fig


def weighted_mean(df, value, weight="total_request_volume"):
    if df.empty or value not in df:
        return np.nan
    values = pd.to_numeric(df[value], errors="coerce")
    weights = pd.to_numeric(df[weight], errors="coerce").fillna(0) if weight in df else pd.Series(1, index=df.index)
    mask = values.notna() & (weights > 0)
    return float(np.average(values[mask], weights=weights[mask])) if mask.any() else float(values.mean())


def percent(value):
    return "—" if pd.isna(value) else f"{value * 100:.1f}%"


def add_kpis(df):
    volume = int(df["total_request_volume"].sum()) if not df.empty else 0
    delay = weighted_mean(df, "mean_resolution_delay_hours")
    repeat = weighted_mean(df, "repeat_request_rate_14d")
    dissat = weighted_mean(df, "citizen_dissatisfaction_rate", "rsat_response_count")
    cols = st.columns(4)
    cols[0].metric("Requests represented", f"{volume:,}", help="Total 311 requests represented by the current filters.")
    cols[1].metric("Typical delay", "—" if pd.isna(delay) else f"{delay:.1f} h")
    cols[2].metric("Repeat within 14 days", percent(repeat), help="Share of requests followed by another request within 14 days.")
    cols[3].metric("Survey dissatisfaction", percent(dissat), help="Share of RSAT responses indicating dissatisfaction.")


def render_filters(df, prefix):
    boroughs = ["All boroughs"] + sorted(df["borough"].dropna().unique().tolist())
    services = ["All services"] + sorted(df["complaint_type_upper"].dropna().unique().tolist())
    c1, c2 = st.columns(2)
    borough = c1.selectbox("Borough", boroughs, key=f"{prefix}_borough")
    service = c2.selectbox("Service", services, key=f"{prefix}_service")
    start, end = df["period"].min().date(), df["period"].max().date()
    dates = st.slider("Analysis period", start, end, (start, end), format="MMM YYYY", key=f"{prefix}_dates")
    out = df[df["period"].between(pd.Timestamp(dates[0].year, dates[0].month, 1), pd.Timestamp(dates[1].year, dates[1].month, 1))]
    if borough != "All boroughs":
        out = out[out["borough"] == borough]
    if service != "All services":
        out = out[out["complaint_type_upper"] == service]
    return out


def add_risk(df):
    out = df.copy()
    for col in ["mean_resolution_delay_hours", "repeat_request_rate_14d", "citizen_dissatisfaction_rate"]:
        out[f"{col}_rank"] = out[col].rank(pct=True).fillna(0)
    out["risk_score"] = 100 * (0.45 * out["mean_resolution_delay_hours_rank"] + 0.35 * out["repeat_request_rate_14d_rank"] + 0.20 * out["citizen_dissatisfaction_rate_rank"])
    out["risk"] = pd.cut(out["risk_score"], [-1, 40, 70, 101], labels=["Monitor", "Elevated", "Priority"])
    return out


def render_trends(df):
    """Show each measure on its own scale so the story is easy to read."""
    if df.empty:
        st.info("No cells match the selected filters.")
        return
    trend = df.groupby("period", as_index=False).agg(
        requests=("total_request_volume", "sum"),
        delay=("mean_resolution_delay_hours", "mean"),
        repeat=("repeat_request_rate_14d", "mean"),
        dissatisfaction=("citizen_dissatisfaction_rate", "mean"),
    )
    st.markdown("**Service outcomes over time**")
    c1, c2 = st.columns(2)
    with c1:
        delay_fig = px.line(trend, x="period", y="delay", markers=True, labels={"period": "Month", "delay": "Hours"}, title="Average resolution delay")
        st.plotly_chart(style_chart(delay_fig, 300), use_container_width=True)
    with c2:
        repeat_fig = px.line(trend, x="period", y="repeat", markers=True, labels={"period": "Month", "repeat": "Repeat rate"}, title="Repeat requests within 14 days")
        repeat_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_chart(repeat_fig, 300), use_container_width=True)
    st.markdown("**Demand and satisfaction**")
    demand_fig = px.bar(trend, x="period", y="requests", labels={"period": "Month", "requests": "Requests"}, title="Monthly request volume", text_auto=True)
    demand_fig.update_traces(marker_color="#4cc9f0", textposition="outside", texttemplate="%{y:,.0f}")
    st.plotly_chart(style_chart(demand_fig, 300), use_container_width=True)
    st.caption("The charts use separate units: hours for delay, percentage for repeat rate, and request count for demand.")


def about_view():
    st.subheader("How this dashboard works")
    st.markdown("""
    - **Unit of analysis:** service × borough × month cells built from NYC 311 operational records and RSAT survey aggregates.
    - **Operations signals:** request volume, resolution delay, repeat-request rates, and survey dissatisfaction.
    - **NLP signals:** sentiment, topics, and grievance aspects extracted from public resolution narratives; the RSAT source does not provide unrestricted citizen comments.
    - **Model evaluation:** chronological evaluation on 994 untouched 2024 cells, with LightGBM as the primary model and last-value persistence as the strongest benchmark.
    - **Research finding:** the all-family bundle worsened delay prediction. An exploratory validation-selected ABSA + RSAT model improved over structured LightGBM, but neither beat the previous-month baseline on NYC's 2024 test period.
    - **Interpretation:** the model results show predictive association at aggregate level. They do not establish causality and should not be used to make decisions about individual residents.
    """)
    st.info("Updated project finding: the previous-month persistence baseline is stronger than the augmented NLP model on the held-out horizon. The dashboard is a prioritisation aid, not an automatic decision system.")


def municipal_view(df, predictions, robustness, ranking_metrics, review_metrics, predictive_queue):
    st.markdown('<div class="hero"><div class="eyebrow">Municipal operations</div><h1>Find what needs attention first</h1><p>Use the priority queue to focus limited staff time on service areas with the strongest combined warning signals.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="notice"><strong>Start here:</strong> choose a borough, service, or time period below. Then read the priority queue from top to bottom. A higher score means more attention is warranted across predicted delay, repeat requests, and dissatisfaction.</div>', unsafe_allow_html=True)
    finding = corrected_finding(review_metrics)
    if finding:
        delay_r2 = review_metrics["naive_baselines"]["mean_resolution_delay_hours"]["last_value"]["r2"]
        repeat_r2 = review_metrics["naive_baselines"]["repeat_request_rate_14d"]["last_value"]["r2"]
        st.markdown(f'<div class="notice" style="border-left-color:#f6bd60;background:#211d15;border-color:#5f4b28;"><strong>Research finding:</strong> language and satisfaction features are useful context, but they did not beat the previous-month persistence benchmark in the held-out test (delay R2 {delay_r2:.3f}; repeat-rate R2 {repeat_r2:.3f}). Use this queue as review support, not as an automatic decision.</div>', unsafe_allow_html=True)
    selected = render_filters(df, "municipal")
    if selected.empty:
        st.warning("No service cells match the selected filters.")
        return
    st.markdown('<div class="section-title"><h2>Current operating picture</h2><span class="pill">Filtered view</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">The cards summarize the selected area and period. Hover over a card for the definition.</div>', unsafe_allow_html=True)
    add_kpis(selected)

    selected_keys = selected[["complaint_type_upper", "borough", "year", "month"]].drop_duplicates()
    filtered_queue = predictive_queue.merge(
        selected_keys,
        on=["complaint_type_upper", "borough", "year", "month"],
        how="inner",
    ) if not predictive_queue.empty else pd.DataFrame()
    predictive_mode = not filtered_queue.empty
    if predictive_mode:
        ranked = filtered_queue.rename(columns={"predicted_priority_score": "risk_score"}).copy()
        ranked["risk"] = pd.cut(
            ranked["risk_score"], [-1, 40, 70, 101], labels=["Monitor", "Elevated", "Priority"]
        )
        ranked = ranked.sort_values("risk_score", ascending=False).head(10)
        ranked["display_delay"] = ranked["predicted_delay"]
        ranked["display_repeat"] = ranked["predicted_repeat"]
    else:
        ranked = add_risk(selected).sort_values("risk_score", ascending=False).head(10).copy()
        ranked["display_delay"] = ranked["mean_resolution_delay_hours"]
        ranked["display_repeat"] = ranked["repeat_request_rate_14d"]
    top = ranked.iloc[0]
    queue_label = "one-month-ahead predicted" if predictive_mode else "historical monitoring"
    st.info(f"**First place to look:** {top['complaint_type_upper']} in {top['borough']} ({top['period']:%b %Y}) has the highest {queue_label} priority score in the current selection.")

    st.markdown('<div class="section-title"><h2>Priority queue</h2><span class="pill">Review first</span></div>', unsafe_allow_html=True)
    chart_data = ranked.sort_values("risk_score")
    priority_fig = px.bar(chart_data, x="risk_score", y="complaint_type_upper", color="risk", orientation="h", text="risk_score", color_discrete_map={"Monitor": "#52b788", "Elevated": "#f6bd60", "Priority": "#ff6b6b"}, labels={"risk_score": "Priority score (0-100)", "complaint_type_upper": "Service", "risk": "Attention level"}, title="Highest-priority service cells")
    priority_fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    st.plotly_chart(style_chart(priority_fig, 380), use_container_width=True)

    table = ranked.copy()
    table["period"] = table["period"].dt.strftime("%b %Y")
    table = table.rename(columns={
        "complaint_type_upper": "Service", "borough": "Borough", "period": "Period",
        "risk": "Attention", "risk_score": "Score", "display_delay": "Delay (h)",
        "display_repeat": "Repeat 14d", "citizen_dissatisfaction_rate": "Dissatisfaction",
        "total_request_volume": "Requests",
    })[["Service", "Borough", "Period", "Attention", "Score", "Delay (h)", "Repeat 14d", "Dissatisfaction", "Requests"]]
    table["Score"] = table["Score"].round(1)
    table["Delay (h)"] = table["Delay (h)"].round(1)
    table["Repeat 14d"] = table["Repeat 14d"].map(percent)
    table["Dissatisfaction"] = table["Dissatisfaction"].map(percent)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download this queue", table.to_csv(index=False).encode("utf-8"), "municipal_priority_queue.csv", "text/csv")

    st.markdown('<div class="section-title"><h2>Supporting views</h2><span class="pill">Explore</span></div>', unsafe_allow_html=True)
    trend_tab, borough_tab, evidence_tab = st.tabs(["How performance changed", "Compare boroughs", "Model evidence"])
    with trend_tab:
        render_trends(selected)
    with borough_tab:
        borough_summary = selected.groupby("borough", as_index=False).agg(
            delay=("mean_resolution_delay_hours", "mean"),
            dissatisfaction=("citizen_dissatisfaction_rate", "mean"),
            requests=("total_request_volume", "sum"),
        )
        b1, b2 = st.columns(2)
        with b1:
            delay_fig = px.bar(borough_summary.sort_values("delay"), x="delay", y="borough", orientation="h", labels={"delay": "Average delay (hours)", "borough": "Borough"}, title="Average resolution delay")
            st.plotly_chart(style_chart(delay_fig, 320), use_container_width=True)
        with b2:
            dissat_fig = px.bar(borough_summary.sort_values("dissatisfaction"), x="dissatisfaction", y="borough", orientation="h", labels={"dissatisfaction": "Dissatisfaction", "borough": "Borough"}, title="Survey dissatisfaction")
            dissat_fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(style_chart(dissat_fig, 320), use_container_width=True)
    with evidence_tab:
        delay_result = predictions.get("results_by_target", {}).get("mean_resolution_delay_hours", {}).get("algorithms", {}).get("LightGBM", {})
        repeat_result = predictions.get("results_by_target", {}).get("repeat_request_rate_14d", {}).get("algorithms", {}).get("LightGBM", {})
        ranking = ranking_metrics.get("metrics_by_k", {})
        available_k = sorted(int(k) for k in ranking)
        preferred_k = 10 if "10" in ranking else (available_k[0] if available_k else None)
        precision = ranking.get(str(preferred_k), {}).get("precision_at_k") if preferred_k else None
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Delay feature change (Delta R2)", f"{delay_result.get('delta_r2', np.nan):+.3f}" if delay_result else "-")
        e2.metric("Repeat feature change (Delta R2)", f"{repeat_result.get('delta_r2', np.nan):+.3f}" if repeat_result else "-")
        e3.metric("Robustness runs", f"{len(robustness.get('seeds', [])) or '-'} seeds")
        e4.metric(
            f"Priority Precision@{preferred_k} (strict overlap)" if preferred_k else "Priority Precision@k",
            f"{precision:.1%}" if precision is not None else "-",
            help="Share of the dashboard's top-ranked held-out cells that were also in the observed top-k burden set.",
        )
        st.caption("Primary evidence uses month-t information to forecast month t+1 on the held-out 2024 horizon. Results are aggregate service-borough-month predictions, not causal effects or individual-ticket forecasts.")
        if preferred_k:
            hits = ranking[str(preferred_k)].get("hits", round(precision * preferred_k))
            st.warning(f"Strict top-{preferred_k} overlap: {hits}/{preferred_k} predicted cells were also in the observed top-{preferred_k}. Here relevance prevalence is k/N, so the original lift is only Precision@k × N/k, not independent evidence of queue quality.")
        fixed = ranking_metrics.get("fixed_threshold", {})
        if fixed:
            st.markdown("**Separate fixed-cutoff burden evaluation**")
            st.caption(f"The burden transform and cutoff were fitted on February–August 2023 training outcomes only and are frozen across k. {fixed['relevant_cells']}/{fixed['test_cells']} NYC-2024 cells qualify ({fixed['relevance_prevalence']:.1%}). This exploratory cutoff is not a validated municipal standard and is not the same relevance definition as strict top-k overlap.")
            fixed_rows = [
                {"Queue size": int(k), "Relevant hits": f"{m['hits']}/{k}",
                 "Precision": f"{m['precision_at_k']:.1%}", "Recall": f"{m['recall_at_k']:.1%}",
                 "Lift vs fixed prevalence": round(m['lift_over_random'], 2)}
                for k, m in fixed["metrics_by_k"].items()
            ]
            st.dataframe(pd.DataFrame(fixed_rows), use_container_width=True, hide_index=True)
        st.markdown("**Primary LightGBM comparison**")
        evidence_rows = []
        for target_label, target_key in [("Delay (hours)", "mean_resolution_delay_hours"), ("Repeat rate (14d)", "repeat_request_rate_14d")]:
            result = review_metrics.get("feature_family_ablations", {}).get(target_key, {})
            structured = result.get("structured_only", {})
            augmented = result.get("all_augmented", {})
            last_value = review_metrics.get("naive_baselines", {}).get(target_key, {}).get("last_value", {})
            evidence_rows.append({
                "Target": target_label,
                "Structured R2": structured.get("r2", np.nan),
                "All features R2": augmented.get("r2", np.nan),
                "Delta R2": augmented.get("r2", np.nan) - structured.get("r2", np.nan),
                "Last-value R2": last_value.get("r2", np.nan),
            })
        evidence_df = pd.DataFrame(evidence_rows)
        for col in ["Structured R2", "All features R2", "Delta R2", "Last-value R2"]:
            evidence_df[col] = evidence_df[col].map(lambda x: f"{x:+.4f}" if col == "Delta R2" else f"{x:.4f}")
        st.dataframe(evidence_df, use_container_width=True, hide_index=True)

        selected_metrics = load_json("selected_feature_results.json")
        if selected_metrics:
            st.markdown("**Exploratory validation-selected features**")
            selected_rows = []
            for target_label, target_key in [("Delay (hours)", "mean_resolution_delay_hours"), ("Repeat rate (14d)", "repeat_request_rate_14d")]:
                result = selected_metrics["results_by_target"][target_key]
                primary = result["primary_seed_42"]
                selected_rows.append({"Target": target_label,
                    "Added families": " + ".join(result["selected_families"]) or "None (structured only)",
                    "Selected R2": round(primary["selected"]["r2"], 4),
                    "Delta vs structured": round(primary["delta_r2"], 4)})
            st.dataframe(pd.DataFrame(selected_rows), use_container_width=True, hide_index=True)
            st.caption("Families were selected using 2023 validation R², not 2024 scores. This is a post-review exploratory refinement on a previously examined test year. The selected delay gain has a bootstrap interval spanning zero, and persistence remains stronger for both outcomes.")

        ablation_rows = []
        for target_label, target_key in [("Delay", "mean_resolution_delay_hours"), ("Repeat rate", "repeat_request_rate_14d")]:
            families = review_metrics.get("feature_family_ablations", {}).get(target_key, {}).get("families", {})
            for family, result in families.items():
                ablation_rows.append({"Target": target_label, "Feature family": family, "Delta R2": result.get("delta_r2_vs_structured", np.nan)})
        if ablation_rows:
            ablation_df = pd.DataFrame(ablation_rows)
            ablation_fig = px.bar(ablation_df, x="Feature family", y="Delta R2", color="Target", barmode="group", title="Incremental effect by feature family", labels={"Delta R2": "Change from structured LightGBM"}, color_discrete_sequence=["#4cc9f0", "#f6bd60"])
            ablation_fig.add_hline(y=0, line_color="#a9bbca", line_width=1)
            st.plotly_chart(style_chart(ablation_fig, 330), use_container_width=True)
            st.caption("Positive values indicate improvement over the structured model. The strongest benchmark remains the previous-month persistence baseline.")
        shap_path = ROOT / "reports" / "figures" / "lagged_shap_feature_importance.png"
        if shap_path.exists():
            with st.expander("View global feature importance"):
                st.image(str(shap_path), caption="Which feature groups influenced the model most.", use_container_width=True)


def resident_view(df):
    st.markdown('<div class="hero"><div class="eyebrow">Resident view</div><h1>Understand service performance</h1><p>See how quickly services are resolved and how often requests repeat, using simple historical summaries.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="notice"><strong>Privacy note:</strong> this view contains only aggregate service statistics. It does not show names, addresses, complaint descriptions, or individual requests.</div>', unsafe_allow_html=True)
    st.markdown('<div class="notice" style="border-left-color:#9b8afb;background:#19172a;border-color:#443d70;"><strong>How to read this:</strong> these are historical service patterns, not a prediction about one person or one ticket. Faster or slower averages can reflect service mix, season, and reporting volume.</div>', unsafe_allow_html=True)
    selected = render_filters(df, "resident")
    if selected.empty:
        st.info("No service cells match the selected filters.")
        return
    st.markdown('<div class="section-title"><h2>At a glance</h2><span class="pill">Selected history</span></div>', unsafe_allow_html=True)
    add_kpis(selected)
    city_delay = weighted_mean(df, "mean_resolution_delay_hours")
    selected_delay = weighted_mean(selected, "mean_resolution_delay_hours")
    city_repeat = weighted_mean(df, "repeat_request_rate_14d")
    selected_repeat = weighted_mean(selected, "repeat_request_rate_14d")
    delay_direction = "lower" if selected_delay <= city_delay else "higher"
    repeat_direction = "lower" if selected_repeat <= city_repeat else "higher"
    st.info(f"In the selected view, the average resolution delay is **{selected_delay:.1f} hours** ({delay_direction} than the citywide {city_delay:.1f} hours). **{percent(selected_repeat)}** of requests repeat within 14 days ({repeat_direction} than the citywide {percent(city_repeat)}).")

    st.markdown("### What changed over time?")
    render_trends(selected)

    st.markdown("### Service comparison")
    st.markdown('<div class="section-note">Citywide comparison for the selected time period. Use the filters above to narrow the time window.</div>', unsafe_allow_html=True)
    comparison = df[df["period"].between(selected["period"].min(), selected["period"].max())]
    service_summary = comparison.groupby("complaint_type_upper", as_index=False).agg(
        delay=("mean_resolution_delay_hours", "mean"),
        repeat=("repeat_request_rate_14d", "mean"),
        requests=("total_request_volume", "sum"),
    ).sort_values("requests", ascending=False).head(15)
    service_summary = service_summary.rename(columns={"complaint_type_upper": "Service", "delay": "Average delay (h)", "repeat": "Repeat within 14 days", "requests": "Requests"})
    service_summary["Average delay (h)"] = service_summary["Average delay (h)"].round(1)
    service_summary["Repeat within 14 days"] = service_summary["Repeat within 14 days"].map(percent)
    st.dataframe(service_summary, use_container_width=True, hide_index=True)
    st.caption("These are historical averages across service cells, not guarantees for any individual request.")


if __name__ == "__main__":
    cells = load_cells()
    predictive_queue = load_priority_queue()
    predictions = load_json("lagged_predictive_modeling_results.json")
    robustness = load_json("robustness_results.json")
    ranking_metrics = load_json("priority_ranking_metrics.json")
    review_metrics = load_json("review_corrections_results.json")
    st.sidebar.title("Civic Insight Hub")
    st.sidebar.caption("NYC 311 · corrected research dashboard")
    role = st.sidebar.radio("Choose workspace", ["Municipal Operations", "Resident View"])
    st.sidebar.markdown("""
    **Municipal Operations**

    Find priority service cells, compare boroughs, and inspect model evidence.

    **Resident View**

    Read historical service performance in plain language.
    """)
    st.sidebar.caption("All values are aggregate NYC civic-service statistics.")
    if cells.empty:
        st.error(f"Integrated dataset not found: {DATA_PATH}")
    else:
        test_year = predictions.get("test_horizon_year", 2024)
        st.sidebar.success(f"Data ready · out-of-time test horizon: {test_year}")
        if role == "Municipal Operations":
            municipal_view(cells, predictions, robustness, ranking_metrics, review_metrics, predictive_queue)
        else:
            resident_view(cells)
        with st.expander("Methodology and limitations"):
            about_view()
