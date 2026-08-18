"""
LLM Cost Router — Dashboard

Reads router_results.db (from the notebook) and shows how much a smart routing
policy saves versus sending every request to the expensive model.

Run locally:  streamlit run app.py
"""
import os
import duckdb
import pandas as pd
import altair as alt
import streamlit as st

DB_PATH = os.environ.get("ROUTER_DB_PATH", "data/router_results.db")

st.set_page_config(page_title="LLM Cost Router", page_icon="⇄", layout="wide")

# ---------------------------------------------------------------- styling
# "Finance / savings" aesthetic: deep green-black, gold accent for money,
# cheap tier in green, expensive tier in amber. Monospace numerals.
st.markdown(
    """
    <style>
      :root {
        --bg:#0a0f0d; --panel:#131b18; --edge:#233029;
        --ink:#e9f1ec; --dim:#7d9188;
        --save:#4ade80; --cheap:#4ade80; --exp:#f4b860;
        --gold:#ffd479;
      }
      .stApp { background:var(--bg); }
      .block-container { padding-top:2.4rem; max-width:1060px; }
      h1,h2,h3,p,span,div,label { color:var(--ink); }
      .kick { font-family:ui-monospace,Menlo,monospace; font-size:.74rem;
        letter-spacing:.26em; text-transform:uppercase; color:var(--dim); }
      .head { font-size:1.9rem; font-weight:650; margin:.15rem 0 .3rem; }
      .sub  { color:var(--dim); font-size:.93rem; margin-bottom:1.8rem; }

      .hero { background:linear-gradient(135deg,#10231a,#0d1c17);
        border:1px solid #1d4634; border-radius:16px; padding:2rem 2.2rem; margin-bottom:1.6rem; }
      .hero .pct { font-family:ui-monospace,Menlo,monospace; font-size:3.4rem;
        font-weight:750; color:var(--save); line-height:1; }
      .hero .cap { color:var(--ink); opacity:.9; margin-top:.4rem; font-size:1.05rem; }

      .cards { display:flex; gap:1rem; margin-bottom:1.4rem; }
      .card { flex:1; background:var(--panel); border:1px solid var(--edge);
        border-radius:12px; padding:1.2rem 1.3rem; }
      .card .l { font-family:ui-monospace,Menlo,monospace; font-size:.7rem;
        letter-spacing:.14em; text-transform:uppercase; color:var(--dim); margin-bottom:.5rem; }
      .card .v { font-family:ui-monospace,Menlo,monospace; font-size:1.7rem; font-weight:600; }

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
        routed = con.execute("SELECT * FROM routed").df()
        totals = con.execute("SELECT * FROM totals").df()
    except Exception:
        routed, totals = pd.DataFrame(), pd.DataFrame()
    finally:
        con.close()
    return routed, totals


st.markdown('<div class="kick">LLM Cost Router</div>', unsafe_allow_html=True)
st.markdown('<div class="head">Stop overpaying for easy questions</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Routes each request to the cheapest model that can handle it — '
    'easy questions to a small model, hard ones to the frontier model — and measures the savings.</div>',
    unsafe_allow_html=True,
)

routed, totals = load(DB_PATH)

if totals.empty:
    st.warning(
        f"No results found at `{DB_PATH}`. Run the notebook to generate "
        "`router_results.db`, then place it in this app's `data/` folder "
        "(or set ROUTER_DB_PATH)."
    )
    st.stop()

t = totals.iloc[0]
pct = float(t["savings_pct"])
routed_cost = float(t["routed_cost"])
baseline_cost = float(t["baseline_cost"])
savings = float(t["savings"])
n = int(t["n"]); n_cheap = int(t["n_cheap"]); n_exp = int(t["n_expensive"])

# ---------------------------------------------------------------- hero savings
st.markdown(
    f"""
    <div class="hero">
      <div class="pct">{pct:.0f}% cheaper</div>
      <div class="cap">Routing this workload cost <b>${routed_cost:.4f}</b> instead of
      <b>${baseline_cost:.4f}</b> — saving <b>${savings:.4f}</b> per batch by not sending
      easy questions to the expensive model.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- cards
st.markdown(
    f"""
    <div class="cards">
      <div class="card"><div class="l">Requests</div><div class="v">{n}</div></div>
      <div class="card"><div class="l">To cheap model</div><div class="v" style="color:#4ade80">{n_cheap}</div></div>
      <div class="card"><div class="l">To expensive model</div><div class="v" style="color:#f4b860">{n_exp}</div></div>
      <div class="card"><div class="l">Saved / batch</div><div class="v" style="color:#ffd479">${savings:.4f}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- cost comparison bar
st.markdown('<div class="section">Cost: routed vs. all-expensive</div>', unsafe_allow_html=True)
comp = pd.DataFrame({
    "policy": ["Smart routing", "All expensive"],
    "cost": [routed_cost, baseline_cost],
})
bar = (
    alt.Chart(comp)
    .mark_bar(size=60)
    .encode(
        x=alt.X("policy:N", title=None, axis=alt.Axis(labelColor="#7d9188", labelAngle=0)),
        y=alt.Y("cost:Q", title="cost per batch ($)",
                axis=alt.Axis(labelColor="#7d9188", titleColor="#7d9188", gridColor="#1a2721")),
        color=alt.Color("policy:N",
                        scale=alt.Scale(domain=["Smart routing","All expensive"], range=["#4ade80","#f4b860"]),
                        legend=None),
        tooltip=["policy:N", alt.Tooltip("cost:Q", format="$.5f")],
    )
    .properties(height=300, background="#131b18",
                padding={"left":16,"right":16,"top":16,"bottom":16})
    .configure_view(strokeWidth=0)
)
st.altair_chart(bar, width="stretch")

# ---------------------------------------------------------------- per-question routing
st.markdown('<div class="section">How each request was routed</div>', unsafe_allow_html=True)
show = routed.copy()
def tier_label(model):
    return "cheap" if "haiku" in model.lower() or "small" in model.lower() else "expensive"
show["tier"] = show["model"].map(tier_label)
show = show.rename(columns={
    "question": "Question", "difficulty": "Difficulty", "tier": "Routed to",
    "reasons": "Why", "routed_cost": "Cost",
})
show["Cost"] = show["Cost"].map(lambda x: f"${x:.5f}")
show = show[["Question", "Difficulty", "Routed to", "Why", "Cost"]]

def color_tier(val):
    if val == "cheap": return "color:#4ade80;font-weight:600;"
    if val == "expensive": return "color:#f4b860;font-weight:600;"
    return ""
styled = show.style.map(color_tier, subset=["Routed to"])
st.dataframe(styled, width="stretch", hide_index=True)

st.markdown(
    '<div style="margin-top:1.6rem;color:#7d9188;font-size:.8rem;'
    f'font-family:ui-monospace,Menlo,monospace;">source: {DB_PATH} · '
    'difficulty-based model routing</div>',
    unsafe_allow_html=True,
)
