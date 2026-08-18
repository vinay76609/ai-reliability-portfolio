# LLM Evaluation Dashboard — Phase 3

A dashboard that visualizes the output of the LLM evaluation framework: answer
quality (faithfulness, relevance, correctness), cost, and latency across runs —
so **quality drift surfaces before users find it**.

This is Phase 3 of the project. It reads the `eval_runs.db` database produced by
the Phase 2 notebook.

## What it shows

- **Summary cards** — the latest run's five metrics, each with a delta vs. the previous run.
- **Drift chart** — faithfulness, relevance, and correctness plotted over time. The centerpiece: when a change degrades quality, the line drops and you see it immediately.
- **Run history** — every run in a sortable table.
- **Weakest answers** — the lowest-scoring questions in the latest run, so you know what to inspect first.

## Setup

```bash
pip install -r requirements.txt
```

Place your `eval_runs.db` (from the Phase 2 notebook) into the `data/` folder:

```
llm-eval-dashboard/
├── app.py
├── requirements.txt
└── data/
    └── eval_runs.db      <- put it here
```

If your database lives elsewhere, point to it with an environment variable:

```bash
export EVAL_DB_PATH=/path/to/eval_runs.db
```

## Run locally

```bash
streamlit run app.py
```

It opens at http://localhost:8501.

## Deploy a live URL (recommended for your portfolio)

A live link beats a repo link when you're job hunting.

1. Push this folder to a public GitHub repo.
2. Go to share.streamlit.io, sign in with GitHub, and pick the repo.
3. Set the main file to `app.py`.
4. Commit a small sample `data/eval_runs.db` so the deployed app has data to show.

## How it connects to the rest of the project

- **Phase 1** — core loop: get an answer, judge faithfulness.
- **Phase 2** — adds relevance, correctness, cost, latency; saves every run to `eval_runs.db`.
- **Phase 3 (this)** — reads that database and visualizes it.

## Note on the sample database

The included `data/eval_runs.db` contains sample runs (three healthy, one
deliberately degraded) so the dashboard renders immediately — including the drift
drop. Replace it with your own real runs from Phase 2.
