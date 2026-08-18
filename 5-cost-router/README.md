# LLM Cost Router

Stop overpaying for easy questions. Not every request needs your most expensive
AI model — this router sends easy questions to a cheap small model and only the
hard ones to the expensive frontier model, then measures the savings.

## The idea

- A **classifier** judges each question's difficulty (transparent rules, or an
  optional LLM-judge).
- **Easy** → cheap model. **Hard** → expensive model.
- Compare total cost **with routing** vs. **all-expensive**, and report the savings.

Since cost is the #1 barrier to deploying AI at scale, a router that cuts spend
with no quality loss on easy traffic is genuinely valuable — and unlike a pure
monitoring tool, it *acts* to save money.

## Two parts

1. **`LLM_Cost_Router.ipynb`** — the core tool (runs in Google Colab). Routes a
   mixed workload, measures savings, saves `router_results.db`.
2. **This dashboard** (`app.py`) — reads that database and shows the savings, a
   cost comparison chart, and how each request was routed.

## Setup

```bash
pip install -r requirements.txt
```

Put `router_results.db` (from the notebook) in the `data/` folder:

```
cost-router-dashboard/
├── app.py
├── requirements.txt
└── data/
    └── router_results.db
```

Or point to it: `export ROUTER_DB_PATH=/path/to/router_results.db`

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## Why it matters (for interviews)

The biggest barrier to deploying AI at scale is cost. This shows you can cut LLM
spend substantially — in the sample workload, ~46% — with no quality loss on easy
traffic, by routing intelligently. It adds an efficiency/cost angle to a
reliability portfolio: you don't just measure systems, you make them cheaper.

## Note on pricing

The model prices in the notebook are placeholders (per 1M tokens). Update them
from the provider's pricing page for real dollar figures. The savings *percentage*
holds regardless, since it depends on the price ratio, not absolute prices.

## Sample data

The included `data/router_results.db` shows a 12-question workload split 6 cheap /
6 expensive for ~46% savings. Replace it with your own runs from the notebook.
