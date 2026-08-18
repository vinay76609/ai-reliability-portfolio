# Data Quality & Anomaly Detector

A **smoke detector for data**. Bad data breaks pipelines silently — no crash, no
error, just wrong results downstream that nobody notices for days. This tool
learns what clean data looks like, then checks each new batch and raises an alarm
when something is off.

## What it catches

- **Schema drift** — a column disappeared or an unexpected one appeared.
- **Null spike** — a column's blank rate jumped far above normal.
- **Distribution shift** — a numeric column's values moved far from their usual range (e.g. ages suddenly in months instead of years).
- **Duplicate flood** — far more repeated rows than normal.

## How it works

1. **Profile** a clean reference dataset — learn its statistical fingerprint
   (columns, null rates, numeric mean/std, duplicate rate).
2. **Check** each new batch against that profile using tunable thresholds
   (e.g. flag a mean that moves more than 3 standard deviations).
3. **Verdict** — PASS if clean, or a list of anomalies grouped by severity.

No LLM, no embeddings — this is core data-engineering: statistical profiling and
drift detection.

## Two parts

1. **`Data_Quality_Detector.ipynb`** — the core tool (runs in Google Colab).
   Profiles clean data, tests four broken batches, saves `dataquality_results.db`.
2. **This dashboard** (`app.py`) — reads that database and shows the health
   verdict plus every anomaly found.

## Setup

```bash
pip install -r requirements.txt
```

Put `dataquality_results.db` (from the notebook) in the `data/` folder:

```
dataquality-dashboard/
├── app.py
├── requirements.txt
└── data/
    └── dataquality_results.db
```

Or point to it: `export DQ_DB_PATH=/path/to/dataquality_results.db`

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## Why it matters (for interviews)

Data teams depend on early-warning systems exactly like this: catching silent
data corruption before it poisons dashboards, models, and reports. It rounds out
an AI/data-reliability portfolio — you monitor the models *and* the data feeding
them.

## Sample data

The included `data/dataquality_results.db` shows a FAIL batch (a missing column
plus a null spike). Replace it with your own runs from the notebook.
