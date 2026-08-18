"""
Retrieval Quality Analyzer — Dashboard

Reads retrieval_results.db (from the notebook) and shows a head-to-head
comparison of retrieval strategies: which chunking approach finds the right
document more often, and where each one fails.

Run locally:  streamlit run app.py
"""

import os
import duckdb
import pandas as pd
import altair as alt
import streamlit as st

DB_PATH = os.environ.get("RETRIEVAL_DB_PATH", "data/retrieval_results.db")

st.set_page_config(page_title="Retrieval Quality Analyzer", page_icon="◈", layout="wide")

# ---------------------------------------------------------------- styling
# "Lab comparison" aesthetic: deep indigo-black, two accent colors for the two
# strategies being compared (violet vs. teal), monospace numerals.
st.markdown(
    """
    <style>
      :root {
        --bg:#0b0d14; --panel:#161a26; --edge:#262c3d;
        --ink:#e9ecf5; --dim:#828aa3;
        --a:#a78bfa;   /* strategy A - violet */
        --b:#2dd4bf;   /* strategy B - teal   */
        --win:#2dd4bf; --warn:#f0a860;
      }
      .stApp { background: var(--bg); }
      .block-container { padding-top:2.4rem; max-width:1100px; }
      h1,h2,h3,p,span,div,label { color:var(--ink); }
      .kick { font-family:ui-monospace,Menlo,monospace; font-size:.74rem;
        letter-spacing:.26em; text-transform:uppercase; color:var(--dim); }
      .head { font-size:1.9rem; font-weight:650; margin:.15rem 0 .3rem; }
      .sub  { color:var(--dim); font-size:.93rem; margin-bottom:1.8rem; }

      .cmp { display:flex; gap:1rem; margin-bottom:1.4rem; }
      .col { flex:1; background:var(--panel); border:1px solid var(--edge);
        border-radius:12px; padding:1.3rem 1.4rem; }
      .col.a { border-top:3px solid var(--a); }
      .col.b { border-top:3px solid var(--b); }
      .col .name { font-family:ui-monospace,Menlo,monospace; font-size:.72rem;
        letter-spacing:.16em; text-transform:uppercase; color:var(--dim); margin-bottom:.7rem; }
      .col .metric { display:flex; justify-content:space-between; align-items:baseline;
        margin:.35rem 0; }
      .col .mlabel { color:var(--dim); font-size:.85rem; }
      .col .mval { font-family:ui-monospace,Menlo,monospace; font-size:1.5rem; font-weight:600; }
      .col.a .mval { color:var(--a); }
      .col.b .mval { color:var(--b); }

      .banner { background:#0f1a1c; border:1px solid #1c4b46; border-radius:12px;
        padding:1.2rem 1.5rem; margin-bottom:1.6rem; }
      .banner .t { font-size:1.15rem; font-weight:650; color:var(--b); }
      .banner .d { color:var(--ink); opacity:.9; margin-top:.3rem; font-size:.95rem; }

      .section { font-family:ui-monospace,Menlo,monospace; font-size:.72rem;
        letter-spacing:.18em; text-transform:uppercase; color:var(--dim);
        margin:2rem 0 .7rem; border-top:1px solid var(--edge); padding-top:1.1rem; }
      [data-testid="stDataFrame"] { border:1px solid var(--edge); border-radius:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=5)
def load(db_path):
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
    con = duckdb.connect(db_path, read_only=True)
    try:
        summary = con.execute("SELECT * FROM summary").df()
        per_q = con.execute("SELECT * FROM per_question").df()
    except Exception:
        summary, per_q = pd.DataFrame(), pd.DataFrame()
    finally:
        con.close()
    return summary, per_q


st.markdown('<div class="kick">Retrieval Quality Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="head">Does the search find the right document?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Compares retrieval strategies on a labeled question set. '
    'Hit@k = how often the correct document is retrieved; MRR = how highly it ranks.</div>',
    unsafe_allow_html=True,
)

summary, per_q = load(DB_PATH)

if summary.empty:
    st.warning(
        f"No results found at `{DB_PATH}`. Run the notebook to generate "
        "`retrieval_results.db`, then place it in this app's `data/` folder "
        "(or set RETRIEVAL_DB_PATH)."
    )
    st.stop()

# Identify the two strategies (order as stored)
strategies = summary["strategy"].tolist()
top_k = int(summary["top_k"].iloc[0]) if "top_k" in summary.columns else 3


def metrics_for(name):
    row = summary[summary["strategy"] == name].iloc[0]
    return float(row["hit_rate"]), float(row["mrr"])


# ---------------------------------------------------------------- comparison cards
if len(strategies) >= 2:
    a_name, b_name = strategies[0], strategies[1]
    a_hit, a_mrr = metrics_for(a_name)
    b_hit, b_mrr = metrics_for(b_name)

    st.markdown(
        f"""
        <div class="cmp">
          <div class="col a">
            <div class="name">{a_name}</div>
            <div class="metric"><span class="mlabel">Hit@{top_k}</span><span class="mval">{a_hit:.2f}</span></div>
            <div class="metric"><span class="mlabel">MRR</span><span class="mval">{a_mrr:.2f}</span></div>
          </div>
          <div class="col b">
            <div class="name">{b_name}</div>
            <div class="metric"><span class="mlabel">Hit@{top_k}</span><span class="mval">{b_hit:.2f}</span></div>
            <div class="metric"><span class="mlabel">MRR</span><span class="mval">{b_mrr:.2f}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # verdict banner
    if b_mrr > a_mrr:
        winner, w_mrr, l_mrr = b_name, b_mrr, a_mrr
    else:
        winner, w_mrr, l_mrr = a_name, a_mrr, b_mrr
    lift = ((w_mrr - l_mrr) / l_mrr * 100) if l_mrr > 0 else 0
    st.markdown(
        f"""
        <div class="banner">
          <div class="t">Winner: {winner}</div>
          <div class="d">{winner} ranks the correct document higher — MRR {w_mrr:.2f} vs {l_mrr:.2f}
          ({lift:+.0f}% better). Chunking strategy alone changed retrieval quality this much.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- bar chart
st.markdown('<div class="section">Metrics side by side</div>', unsafe_allow_html=True)

chart_df = summary.melt(
    id_vars=["strategy"], value_vars=["hit_rate", "mrr"],
    var_name="metric", value_name="score",
)
chart_df["metric"] = chart_df["metric"].map({"hit_rate": f"Hit@{top_k}", "mrr": "MRR"})

bars = (
    alt.Chart(chart_df)
    .mark_bar()
    .encode(
        x=alt.X("metric:N", title=None, axis=alt.Axis(labelColor="#828aa3", labelAngle=0)),
        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 1]), title="score",
                axis=alt.Axis(labelColor="#828aa3", titleColor="#828aa3", gridColor="#1b2130")),
        color=alt.Color("strategy:N",
                        scale=alt.Scale(domain=strategies, range=["#a78bfa", "#2dd4bf"]),
                        legend=alt.Legend(title=None, labelColor="#e9ecf5", orient="top")),
        xOffset="strategy:N",
        tooltip=["strategy:N", "metric:N", alt.Tooltip("score:Q", format=".2f")],
    )
    .properties(height=300, background="#161a26",
                padding={"left": 16, "right": 16, "top": 16, "bottom": 16})
    .configure_view(strokeWidth=0)
)
st.altair_chart(bars, width="stretch")

# ---------------------------------------------------------------- per-question
st.markdown('<div class="section">Per-question — who found the right doc?</div>', unsafe_allow_html=True)
st.caption("A ✓ means the correct document was retrieved. Look for questions one strategy caught and the other missed.")

if not per_q.empty:
    # pivot: one row per question, a column per strategy showing found (✓/✗)
    piv = per_q.pivot_table(index="q_id", columns="strategy", values="found", aggfunc="first")
    piv = piv.map(lambda x: "✓" if x else "✗")
    piv = piv.reset_index().rename(columns={"q_id": "Question"})
    st.dataframe(piv, width="stretch", hide_index=True)

st.markdown(
    '<div style="margin-top:1.6rem;color:#828aa3;font-size:.8rem;'
    f'font-family:ui-monospace,Menlo,monospace;">source: {DB_PATH} · '
    f'top_k={top_k} · embeddings-based retrieval</div>',
    unsafe_allow_html=True,
)
