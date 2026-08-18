"""
Prompt Regression Tester — Dashboard

Reads regression_results.db (from the notebook) and shows a clear PASS/FAIL
verdict for a prompt change, plus a per-question breakdown of what regressed.

Run locally:  streamlit run app.py
"""

import os
import duckdb
import pandas as pd
import streamlit as st

DB_PATH = os.environ.get("REGRESSION_DB_PATH", "data/regression_results.db")

st.set_page_config(page_title="Prompt Regression Tester", page_icon="●", layout="wide")

# ---------------------------------------------------------------- styling
# A "test report" aesthetic: near-black, generous space, one big verdict.
# Green = safe to ship, red = blocked. Monospace for the data rows.
st.markdown(
    """
    <style>
      :root {
        --bg:#0c0f13; --panel:#141a21; --edge:#232d38;
        --ink:#e8eef3; --dim:#7b8a97;
        --pass:#4bd884; --fail:#ff5f6d; --pass-bg:#10251a; --fail-bg:#2a1216;
      }
      .stApp { background: var(--bg); }
      .block-container { padding-top: 2.4rem; max-width: 1080px; }
      h1,h2,h3,p,span,div,label { color: var(--ink); }

      .kicker { font-family: ui-monospace,Menlo,monospace; font-size:.74rem;
        letter-spacing:.26em; text-transform:uppercase; color:var(--dim); }
      .headline { font-size:1.9rem; font-weight:650; margin:.15rem 0 .3rem; }
      .sub { color:var(--dim); font-size:.93rem; margin-bottom:1.8rem; }

      .verdict { border-radius:14px; padding:1.8rem 2rem; margin-bottom:1.6rem;
        border:1px solid var(--edge); }
      .verdict.pass { background:var(--pass-bg); border-color:#1c4f36; }
      .verdict.fail { background:var(--fail-bg); border-color:#5c1f27; }
      .verdict .big { font-size:2.4rem; font-weight:750; letter-spacing:-.01em; }
      .verdict.pass .big { color:var(--pass); }
      .verdict.fail .big { color:var(--fail); }
      .verdict .expl { color:var(--ink); font-size:1rem; margin-top:.4rem; opacity:.9; }

      .stat { font-family:ui-monospace,Menlo,monospace; }
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
        return pd.DataFrame()
    con = duckdb.connect(db_path, read_only=True)
    try:
        df = con.execute("SELECT * FROM comparisons").df()
    except Exception:
        df = pd.DataFrame()
    finally:
        con.close()
    return df


st.markdown('<div class="kicker">Prompt Regression Tester</div>', unsafe_allow_html=True)
st.markdown('<div class="headline">Is this prompt change safe to ship?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Compares a candidate prompt against a trusted baseline across a fixed test set. '
    'If any answer got meaningfully worse, the change is blocked.</div>',
    unsafe_allow_html=True,
)

df = load(DB_PATH)

if df.empty:
    st.warning(
        f"No results found at `{DB_PATH}`. Run the notebook to generate "
        "`regression_results.db`, then place it in this app's `data/` folder "
        "(or set REGRESSION_DB_PATH)."
    )
    st.stop()

# ---------------------------------------------------------------- verdict
regressions = df[df["status"] == "REGRESSION"]
n_total = len(df)
n_reg = len(regressions)
passed = n_reg == 0

avg_baseline = df["baseline"].mean()
avg_candidate = df["candidate"].mean()

if passed:
    st.markdown(
        f"""
        <div class="verdict pass">
          <div class="big">✓ PASS — safe to ship</div>
          <div class="expl">All {n_total} test cases held up. No answer dropped beyond the tolerance
          when switching from the baseline prompt to the candidate.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    ids = ", ".join(regressions["question_id"].tolist())
    st.markdown(
        f"""
        <div class="verdict fail">
          <div class="big">✕ FAIL — do not ship</div>
          <div class="expl">{n_reg} of {n_total} test cases regressed ({ids}).
          The candidate prompt made these answers meaningfully worse. Fix before shipping.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- summary stats
c1, c2, c3 = st.columns(3)
c1.markdown(
    f'<div class="stat"><div style="color:#7b8a97;font-size:.72rem;letter-spacing:.14em;'
    f'text-transform:uppercase;">Avg baseline</div>'
    f'<div style="font-size:1.8rem;">{avg_baseline:.2f}</div></div>',
    unsafe_allow_html=True,
)
c2.markdown(
    f'<div class="stat"><div style="color:#7b8a97;font-size:.72rem;letter-spacing:.14em;'
    f'text-transform:uppercase;">Avg candidate</div>'
    f'<div style="font-size:1.8rem;">{avg_candidate:.2f}</div></div>',
    unsafe_allow_html=True,
)
delta = avg_candidate - avg_baseline
color = "#4bd884" if delta >= 0 else "#ff5f6d"
c3.markdown(
    f'<div class="stat"><div style="color:#7b8a97;font-size:.72rem;letter-spacing:.14em;'
    f'text-transform:uppercase;">Overall change</div>'
    f'<div style="font-size:1.8rem;color:{color};">{delta:+.2f}</div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- per-question
st.markdown('<div class="section">Per-question breakdown</div>', unsafe_allow_html=True)

show = df.copy().sort_values("delta")  # worst first
show = show.rename(columns={
    "question_id": "Question",
    "baseline": "Baseline",
    "candidate": "Candidate",
    "delta": "Change",
    "status": "Status",
})
show["Baseline"] = show["Baseline"].round(2)
show["Candidate"] = show["Candidate"].round(2)
show["Change"] = show["Change"].round(2)


def color_status(val):
    if val == "REGRESSION":
        return "color: #ff5f6d; font-weight: 600;"
    return "color: #4bd884;"


styled = show[["Question", "Baseline", "Candidate", "Change", "Status"]].style.map(
    color_status, subset=["Status"]
)
st.dataframe(styled, width="stretch", hide_index=True)

st.markdown(
    '<div style="margin-top:1.6rem;color:#7b8a97;font-size:.8rem;'
    'font-family:ui-monospace,Menlo,monospace;">'
    f'source: {DB_PATH} · {n_total} test cases · tolerance-based gate</div>',
    unsafe_allow_html=True,
)
