"""
LLM Evaluation Framework — Phase 3: Dashboard

Reads the eval_runs.db produced by Phase 2 and visualizes:
  - summary cards for the latest run
  - a faithfulness-over-time line chart (the drift chart)
  - per-run comparison table
  - the worst-scoring questions to inspect failures

Run locally:   streamlit run app.py
"""

import os
import duckdb
import pandas as pd
import altair as alt
import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
DB_PATH = os.environ.get("EVAL_DB_PATH", "data/eval_runs.db")

st.set_page_config(
    page_title="LLM Eval Dashboard",
    page_icon="◆",
    layout="wide",
)

# --------------------------------------------------------------------------
# Styling — a calm, technical "instrument panel" look.
# Deep slate background, one cyan signal color for the metric that matters,
# a warm amber only for warnings (drops/regressions). Monospace for numbers
# so the dashboard reads like a measurement tool, not a marketing page.
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
      :root {
        --bg: #0e1418;
        --panel: #151d23;
        --panel-edge: #223039;
        --ink: #e6edf1;
        --ink-dim: #7d8f9a;
        --signal: #3fd0c9;      /* cyan — the "is it healthy" color */
        --warn: #e0a04d;        /* amber — regressions / low scores */
        --good: #6fcf97;
      }
      .stApp { background: var(--bg); }
      .block-container { padding-top: 2.2rem; max-width: 1200px; }

      h1, h2, h3, h4, p, span, label, div { color: var(--ink); }

      .dash-title {
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: 0.78rem; letter-spacing: 0.28em; text-transform: uppercase;
        color: var(--signal); margin-bottom: 0.1rem;
      }
      .dash-head {
        font-size: 2.0rem; font-weight: 650; letter-spacing: -0.01em;
        margin: 0 0 0.2rem 0;
      }
      .dash-sub { color: var(--ink-dim); font-size: 0.92rem; margin-bottom: 1.6rem; }

      .card {
        background: var(--panel);
        border: 1px solid var(--panel-edge);
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        height: 100%;
      }
      .card .label {
        font-family: ui-monospace, Menlo, monospace;
        font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase;
        color: var(--ink-dim); margin-bottom: 0.5rem;
      }
      .card .value {
        font-family: ui-monospace, Menlo, monospace;
        font-size: 2.1rem; font-weight: 600; line-height: 1;
      }
      .card .delta { font-size: 0.82rem; margin-top: 0.45rem; }
      .up   { color: var(--good); }
      .down { color: var(--warn); }
      .muted { color: var(--ink-dim); }

      .section-label {
        font-family: ui-monospace, Menlo, monospace;
        font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase;
        color: var(--ink-dim); margin: 2.2rem 0 0.7rem 0;
        border-top: 1px solid var(--panel-edge); padding-top: 1.1rem;
      }
      [data-testid="stDataFrame"] { border: 1px solid var(--panel-edge); border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
@st.cache_data(ttl=10)
def load_results(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()
    con = duckdb.connect(db_path, read_only=True)
    try:
        df = con.execute("SELECT * FROM results").df()
    except Exception:
        df = pd.DataFrame()
    finally:
        con.close()
    return df


def run_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-question rows into one row per run."""
    g = (
        df.groupby("run_id")
        .agg(
            run_time=("timestamp", "max"),
            avg_faithfulness=("faithfulness", "mean"),
            avg_relevance=("relevance", "mean"),
            avg_correctness=("correctness", "mean"),
            total_cost=("cost_usd", "sum"),
            avg_latency=("latency_sec", "mean"),
            n=("question_id", "count"),
        )
        .reset_index()
        .sort_values("run_time")
    )
    return g


def fmt_delta(curr, prev, higher_is_better=True, pct=False, money=False):
    """Return (text, css_class) describing the change from prev to curr."""
    if prev is None or pd.isna(prev):
        return ("no prior run", "muted")
    diff = curr - prev
    if money:
        txt = f"{'+' if diff >= 0 else '−'}${abs(diff):.4f}"
    elif pct:
        txt = f"{'+' if diff >= 0 else '−'}{abs(diff)*100:.1f} pts"
    else:
        txt = f"{'+' if diff >= 0 else '−'}{abs(diff):.2f}s"
    improving = diff >= 0 if higher_is_better else diff <= 0
    return (txt + " vs prev", "up" if improving else "down")


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown('<div class="dash-title">LLM Evaluation Framework</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-head">Answer Quality &amp; Cost Monitor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dash-sub">Tracks faithfulness, relevance, correctness, cost, and latency across evaluation runs — so quality drift surfaces before users find it.</div>',
    unsafe_allow_html=True,
)

df = load_results(DB_PATH)

if df.empty:
    st.warning(
        f"No results found at `{DB_PATH}`. "
        "Run the Phase 2 notebook to generate `eval_runs.db`, then place it in the `data/` folder "
        "(or set the EVAL_DB_PATH environment variable to point at it)."
    )
    st.stop()

summary = run_summary(df)
latest = summary.iloc[-1]
prev = summary.iloc[-2] if len(summary) >= 2 else None


# --------------------------------------------------------------------------
# Summary cards
# --------------------------------------------------------------------------
def card(col, label, value, delta_txt, delta_cls):
    col.markdown(
        f"""
        <div class="card">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="delta {delta_cls}">{delta_txt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


c1, c2, c3, c4, c5 = st.columns(5)

d_txt, d_cls = fmt_delta(latest.avg_faithfulness, None if prev is None else prev.avg_faithfulness, pct=True)
card(c1, "Faithfulness", f"{latest.avg_faithfulness:.2f}", d_txt, d_cls)

d_txt, d_cls = fmt_delta(latest.avg_relevance, None if prev is None else prev.avg_relevance, pct=True)
card(c2, "Relevance", f"{latest.avg_relevance:.2f}", d_txt, d_cls)

d_txt, d_cls = fmt_delta(latest.avg_correctness, None if prev is None else prev.avg_correctness, pct=True)
card(c3, "Correctness", f"{latest.avg_correctness:.2f}", d_txt, d_cls)

d_txt, d_cls = fmt_delta(latest.total_cost, None if prev is None else prev.total_cost,
                         higher_is_better=False, money=True)
card(c4, "Cost / run", f"${latest.total_cost:.4f}", d_txt, d_cls)

d_txt, d_cls = fmt_delta(latest.avg_latency, None if prev is None else prev.avg_latency,
                         higher_is_better=False)
card(c5, "Avg latency", f"{latest.avg_latency:.2f}s", d_txt, d_cls)


# --------------------------------------------------------------------------
# Drift chart — the centerpiece
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">Quality over time — drift detection</div>', unsafe_allow_html=True)

if len(summary) < 2:
    st.info("Only one run so far. Run the evaluation again (or the sabotage demo) to see the trend line move.")

trend = summary.copy()
trend["run_time"] = pd.to_datetime(trend["run_time"])
melted = trend.melt(
    id_vars=["run_time"],
    value_vars=["avg_faithfulness", "avg_relevance", "avg_correctness"],
    var_name="metric",
    value_name="score",
)
label_map = {
    "avg_faithfulness": "Faithfulness",
    "avg_relevance": "Relevance",
    "avg_correctness": "Correctness",
}
melted["metric"] = melted["metric"].map(label_map)

color_scale = alt.Scale(
    domain=["Faithfulness", "Relevance", "Correctness"],
    range=["#3fd0c9", "#7aa2f7", "#bb9af7"],
)

line = (
    alt.Chart(melted)
    .mark_line(point=True, strokeWidth=2.5)
    .encode(
        x=alt.X("run_time:T", title=None, axis=alt.Axis(format="%H:%M:%S", labelColor="#7d8f9a", gridColor="#223039")),
        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 1]), title="score",
                axis=alt.Axis(labelColor="#7d8f9a", titleColor="#7d8f9a", gridColor="#1b262d")),
        color=alt.Color("metric:N", scale=color_scale,
                        legend=alt.Legend(title=None, labelColor="#e6edf1", orient="top")),
        tooltip=["run_time:T", "metric:N", alt.Tooltip("score:Q", format=".3f")],
    )
    .properties(height=340, background="#151d23", padding={"left": 18, "right": 18, "top": 18, "bottom": 18})
    .configure_view(strokeWidth=0)
)
st.altair_chart(line, width="stretch")


# --------------------------------------------------------------------------
# Per-run comparison table
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">Run history</div>', unsafe_allow_html=True)

table = summary.copy()
table["run_time"] = pd.to_datetime(table["run_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
table = table.rename(columns={
    "run_id": "Run",
    "run_time": "Time",
    "avg_faithfulness": "Faithful",
    "avg_relevance": "Relevant",
    "avg_correctness": "Correct",
    "total_cost": "Cost ($)",
    "avg_latency": "Latency (s)",
    "n": "Items",
})
for col in ["Faithful", "Relevant", "Correct"]:
    table[col] = table[col].round(3)
table["Cost ($)"] = table["Cost ($)"].round(5)
table["Latency (s)"] = table["Latency (s)"].round(2)
st.dataframe(table.iloc[::-1], width="stretch", hide_index=True)


# --------------------------------------------------------------------------
# Worst questions in the latest run
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">Weakest answers — latest run</div>', unsafe_allow_html=True)
st.caption("Lowest faithfulness in the most recent run. These are the failures worth inspecting first.")

latest_run_id = latest.run_id
worst = (
    df[df["run_id"] == latest_run_id]
    .sort_values("faithfulness")
    .head(5)[["question_id", "faithfulness", "relevance", "correctness", "cost_usd", "latency_sec"]]
    .rename(columns={
        "question_id": "Question",
        "faithfulness": "Faithful",
        "relevance": "Relevant",
        "correctness": "Correct",
        "cost_usd": "Cost ($)",
        "latency_sec": "Latency (s)",
    })
)
for col in ["Faithful", "Relevant", "Correct"]:
    worst[col] = worst[col].round(3)
worst["Cost ($)"] = worst["Cost ($)"].round(6)
worst["Latency (s)"] = worst["Latency (s)"].round(2)
st.dataframe(worst, width="stretch", hide_index=True)

st.markdown(
    '<div style="margin-top:2rem; color:#7d8f9a; font-size:0.8rem; font-family:ui-monospace,Menlo,monospace;">'
    f'source: {DB_PATH} &nbsp;·&nbsp; {len(summary)} runs &nbsp;·&nbsp; {len(df)} graded answers</div>',
    unsafe_allow_html=True,
)
