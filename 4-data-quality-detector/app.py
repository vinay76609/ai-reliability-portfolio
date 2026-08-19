"""
Data Quality & Anomaly Detector — Dashboard

Reads dataquality_results.db (from the notebook) and shows a data-health verdict
for the latest batch, plus every anomaly found, grouped by severity.

Run locally:  streamlit run app.py
"""
import os
import duckdb
import pandas as pd
import streamlit as st
_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DQ_DB_PATH", os.path.join(_HERE, "data", "dataquality_results.db"))
st.set_page_config(page_title="Data Quality Monitor", page_icon="▣", layout="wide")

# ---------------------------------------------------------------- styling
# "Control room" aesthetic: near-black, a single status color (green healthy /
# red alarm), monospace for the data facts. Feels like an ops monitor.
st.markdown(
    """
    <style>
      :root {
        --bg:#0a0e12; --panel:#141b22; --edge:#243039;
        --ink:#e7eef4; --dim:#7c8b98;
        --ok:#39d98a; --ok-bg:#0e2419;
        --alarm:#ff5470; --alarm-bg:#2a1017;
        --high:#ff5470; --med:#e8a44d;
      }
      .stApp { background:var(--bg); }
      .block-container { padding-top:2.4rem; max-width:1040px; }
      h1,h2,h3,p,span,div,label { color:var(--ink); }
      .kick { font-family:ui-monospace,Menlo,monospace; font-size:.74rem;
        letter-spacing:.26em; text-transform:uppercase; color:var(--dim); }
      .head { font-size:1.9rem; font-weight:650; margin:.15rem 0 .3rem; }
      .sub  { color:var(--dim); font-size:.93rem; margin-bottom:1.8rem; }

      .verdict { border-radius:14px; padding:1.8rem 2rem; margin-bottom:1.6rem;
        border:1px solid var(--edge); }
      .verdict.ok    { background:var(--ok-bg);    border-color:#1c5138; }
      .verdict.alarm { background:var(--alarm-bg); border-color:#5c1f2c; }
      .verdict .big { font-size:2.3rem; font-weight:750; }
      .verdict.ok .big    { color:var(--ok); }
      .verdict.alarm .big { color:var(--alarm); }
      .verdict .expl { color:var(--ink); opacity:.9; margin-top:.35rem; font-size:1rem; }

      .stat { font-family:ui-monospace,Menlo,monospace; }
      .stat .l { color:var(--dim); font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; }
      .stat .v { font-size:1.8rem; font-weight:600; }

      .section { font-family:ui-monospace,Menlo,monospace; font-size:.72rem;
        letter-spacing:.18em; text-transform:uppercase; color:var(--dim);
        margin:2rem 0 .7rem; border-top:1px solid var(--edge); padding-top:1.1rem; }

      .anom { background:var(--panel); border:1px solid var(--edge);
        border-left:3px solid var(--dim); border-radius:8px;
        padding:.9rem 1.1rem; margin-bottom:.7rem; }
      .anom.high { border-left-color:var(--high); }
      .anom.medium { border-left-color:#e8a44d; }
      .anom .t { font-weight:650; font-size:.95rem; }
      .anom .tag { font-family:ui-monospace,Menlo,monospace; font-size:.66rem;
        letter-spacing:.12em; text-transform:uppercase; color:var(--dim); }
      .anom .d { color:var(--ink); opacity:.85; font-size:.9rem; margin-top:.25rem; }
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
        anomalies = con.execute("SELECT * FROM anomalies").df()
        meta = con.execute("SELECT * FROM meta").df()
    except Exception:
        anomalies, meta = pd.DataFrame(), pd.DataFrame()
    finally:
        con.close()
    return anomalies, meta


st.markdown('<div class="kick">Data Quality &amp; Anomaly Detector</div>', unsafe_allow_html=True)
st.markdown('<div class="head">Did the data silently break?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Checks each incoming batch against a learned profile of clean data — '
    'catching schema drift, null spikes, distribution shifts, and duplicate floods before they reach downstream systems.</div>',
    unsafe_allow_html=True,
)

anomalies, meta = load(DB_PATH)

if meta.empty:
    st.warning(
        f"No results found at `{DB_PATH}`. Run the notebook to generate "
        "`dataquality_results.db`, then place it in this app's `data/` folder "
        "(or set DQ_DB_PATH)."
    )
    st.stop()

m = meta.iloc[0]
passed = bool(m["passed"])
n_anom = int(m["anomaly_count"])
n_high = int(m["high_count"])
rows = int(m["batch_rows"])

# ---------------------------------------------------------------- verdict
if passed:
    st.markdown(
        f"""
        <div class="verdict ok">
          <div class="big">✓ HEALTHY</div>
          <div class="expl">The latest batch ({rows:,} rows) matched the expected profile. No anomalies detected.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="verdict alarm">
          <div class="big">⚠ {n_anom} ANOMAL{"Y" if n_anom == 1 else "IES"} DETECTED</div>
          <div class="expl">The latest batch ({rows:,} rows) deviated from the expected profile —
          {n_high} high-severity. Investigate before this data flows downstream.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- stats
c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="stat"><div class="l">Batch size</div><div class="v">{rows:,}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat"><div class="l">Anomalies</div><div class="v">{n_anom}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat"><div class="l">High severity</div><div class="v" style="color:{"#ff5470" if n_high else "#39d98a"}">{n_high}</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- anomaly list
if not anomalies.empty:
    st.markdown('<div class="section">What went wrong</div>', unsafe_allow_html=True)
    # high severity first
    order = {"high": 0, "medium": 1, "low": 2}
    anomalies = anomalies.copy()
    anomalies["_o"] = anomalies["severity"].map(lambda s: order.get(s, 3))
    anomalies = anomalies.sort_values("_o")
    for _, a in anomalies.iterrows():
        sev = a["severity"]
        st.markdown(
            f"""
            <div class="anom {sev}">
              <div class="tag">{sev} · {a['column_name']}</div>
              <div class="t">{a['type']}</div>
              <div class="d">{a['detail']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="section">The four checks</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#7c8b98;font-size:.9rem;line-height:1.7;">'
    '<b style="color:#e7eef4;">Schema drift</b> — a column disappeared or an unexpected one appeared.<br>'
    '<b style="color:#e7eef4;">Null spike</b> — a column\'s blank rate jumped far above normal.<br>'
    '<b style="color:#e7eef4;">Distribution shift</b> — a numeric column\'s values moved far from their usual range.<br>'
    '<b style="color:#e7eef4;">Duplicate flood</b> — far more repeated rows than normal.'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div style="margin-top:1.6rem;color:#7c8b98;font-size:.8rem;'
    f'font-family:ui-monospace,Menlo,monospace;">source: {DB_PATH} · profile-based anomaly detection</div>',
    unsafe_allow_html=True,
)
