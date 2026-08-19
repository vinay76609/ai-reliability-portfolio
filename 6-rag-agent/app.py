"""
Self-Correcting RAG Agent — Dashboard

Reads agent_results.db (from the notebook) and visualizes the agent's run:
the outcome, each retrieve->judge->reformulate attempt, and the full decision log.

Run locally:  streamlit run app.py
"""
import os
import duckdb
import pandas as pd
import streamlit as st
_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("AGENT_DB_PATH", os.path.join(_HERE, "data", "agent_results.db"))
st.set_page_config(page_title="RAG Agent", page_icon="◎", layout="wide")

# ---------------------------------------------------------------- styling
# "Agent trace" aesthetic: deep indigo-black, a violet accent for the agent,
# green when a step succeeds, amber for weak/retry, mono for the log.
st.markdown(
    """
    <style>
      :root {
        --bg:#0b0c14; --panel:#161826; --edge:#262a3f;
        --ink:#e9ebf5; --dim:#828aa8;
        --agent:#a78bfa; --ok:#4ade80; --weak:#f4b860; --stop:#ff6b81;
      }
      .stApp { background:var(--bg); }
      .block-container { padding-top:2.4rem; max-width:1040px; }
      h1,h2,h3,p,span,div,label { color:var(--ink); }
      .kick { font-family:ui-monospace,Menlo,monospace; font-size:.74rem;
        letter-spacing:.26em; text-transform:uppercase; color:var(--dim); }
      .head { font-size:1.9rem; font-weight:650; margin:.15rem 0 .3rem; }
      .sub  { color:var(--dim); font-size:.93rem; margin-bottom:1.8rem; }

      .outcome { border-radius:14px; padding:1.6rem 1.9rem; margin-bottom:1.6rem;
        border:1px solid var(--edge); }
      .outcome.ok   { background:#0f2418; border-color:#1d5138; }
      .outcome.stop { background:#231018; border-color:#5c2130; }
      .outcome .big { font-size:1.7rem; font-weight:700; }
      .outcome.ok .big   { color:var(--ok); }
      .outcome.stop .big { color:var(--stop); }
      .outcome .d { color:var(--ink); opacity:.9; margin-top:.35rem; }

      .section { font-family:ui-monospace,Menlo,monospace; font-size:.72rem;
        letter-spacing:.18em; text-transform:uppercase; color:var(--dim);
        margin:2rem 0 .8rem; border-top:1px solid var(--edge); padding-top:1.1rem; }

      .attempt { display:flex; align-items:flex-start; gap:1rem; margin-bottom:.8rem; }
      .anum { font-family:ui-monospace,Menlo,monospace; width:2.2rem; height:2.2rem;
        flex:none; border-radius:50%; display:flex; align-items:center; justify-content:center;
        background:#20233a; color:var(--agent); font-weight:700; border:1px solid #333858; }
      .abody { flex:1; background:var(--panel); border:1px solid var(--edge);
        border-radius:10px; padding:.8rem 1rem; border-left:3px solid var(--weak); }
      .abody.ok { border-left-color:var(--ok); }
      .abody .q { font-family:ui-monospace,Menlo,monospace; font-size:.85rem; color:var(--ink); }
      .abody .m { color:var(--dim); font-size:.82rem; margin-top:.3rem; }
      .pill { font-family:ui-monospace,Menlo,monospace; font-size:.66rem; padding:.1rem .5rem;
        border-radius:5px; letter-spacing:.05em; }
      .pill.ok   { background:#123524; color:var(--ok); }
      .pill.weak { background:#332411; color:var(--weak); }

      .log { background:var(--panel); border:1px solid var(--edge); border-radius:10px;
        padding:1rem 1.2rem; font-family:ui-monospace,Menlo,monospace; font-size:.82rem; }
      .log .row { padding:.28rem 0; border-bottom:1px solid #1f2338; }
      .log .row:last-child { border-bottom:none; }
      .log .tool { color:var(--agent); }
      .log .step { color:var(--dim); }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=5)
def load(db_path):
    if not os.path.exists(db_path):
        return None, None, None
    con = duckdb.connect(db_path, read_only=True)
    try:
        runs = con.execute("SELECT * FROM runs").df()
        attempts = con.execute("SELECT * FROM attempts").df()
        decisions = con.execute("SELECT * FROM decisions").df()
    except Exception:
        runs = attempts = decisions = None
    finally:
        con.close()
    return runs, attempts, decisions


st.markdown('<div class="kick">Self-Correcting RAG Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="head">An agent that fixes its own bad retrieval</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Retrieves, judges whether the results actually answer the question, and if not, '
    'rewrites the query and tries again — all under guardrails that keep it safe and bounded.</div>',
    unsafe_allow_html=True,
)

runs, attempts, decisions = load(DB_PATH)

if runs is None or runs.empty:
    st.warning(
        f"No results found at `{DB_PATH}`. Run the notebook to generate "
        "`agent_results.db`, then place it in this app's `data/` folder "
        "(or set AGENT_DB_PATH)."
    )
    st.stop()

r = runs.iloc[0]
answered = r["status"] == "answered"

# ---------------------------------------------------------------- outcome
if answered:
    st.markdown(
        f"""
        <div class="outcome ok">
          <div class="big">✓ Answered in {int(r['attempts_used'])} attempt(s)</div>
          <div class="d">Question: <i>"{r['question']}"</i> — the agent self-corrected until retrieval was
          strong enough (final relevance {r['final_score']:.2f}), landing on <b>{r['context_title']}</b>.
          Stopped by: {r['stopped_by']}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="outcome stop">
          <div class="big">⚠ Gave up after {int(r['attempts_used'])} attempts</div>
          <div class="d">Question: <i>"{r['question']}"</i> — retrieval never cleared the relevance bar.
          The agent stopped safely rather than looping forever. Stopped by: {r['stopped_by']}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- attempts
st.markdown('<div class="section">The self-correction loop</div>', unsafe_allow_html=True)
for _, a in attempts.iterrows():
    ok = a["verdict"] == "sufficient"
    pill_cls = "ok" if ok else "weak"
    body_cls = "ok" if ok else ""
    st.markdown(
        f"""
        <div class="attempt">
          <div class="anum">{int(a['attempt'])}</div>
          <div class="abody {body_cls}">
            <div class="q">query: "{a['query']}"</div>
            <div class="m">retrieved <b>{a['title']}</b> ·
              relevance {a['score']:.2f} ·
              <span class="pill {pill_cls}">{a['verdict']}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- guardrails
st.markdown('<div class="section">Guardrails enforced</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#828aa8;font-size:.9rem;line-height:1.8;">'
    '<b style="color:#e9ebf5;">Tool allow-list</b> — the agent may only call retrieve, judge, reformulate. Anything else is refused.<br>'
    '<b style="color:#e9ebf5;">Max-retries cap</b> — it stops after a set number of attempts instead of looping forever.<br>'
    '<b style="color:#e9ebf5;">Relevance threshold</b> — it only accepts an answer once retrieval clears a quality bar.<br>'
    '<b style="color:#e9ebf5;">Decision log</b> — every tool call is recorded and auditable (below).'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- decision log
st.markdown('<div class="section">Full decision log</div>', unsafe_allow_html=True)
rows_html = ""
for _, d in decisions.iterrows():
    rows_html += (f'<div class="row"><span class="step">[{d["step"]}]</span> '
                  f'<span class="tool">{d["tool"]}</span> — {d["detail"]}</div>')
st.markdown(f'<div class="log">{rows_html}</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="margin-top:1.6rem;color:#828aa8;font-size:.8rem;'
    f'font-family:ui-monospace,Menlo,monospace;">source: {DB_PATH} · agentic RAG with guardrails</div>',
    unsafe_allow_html=True,
)
