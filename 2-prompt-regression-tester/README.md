# Prompt Regression Tester

Catches when an edit to an AI app's prompt **quietly makes it worse**.

When you change a prompt, it's easy to fix one thing and break another without
noticing. This tool re-runs a fixed test set against a **baseline** prompt and a
**candidate** (edited) prompt, scores every answer with an LLM-as-judge, and
delivers a clear **PASS / FAIL** verdict — blocking the change if any answer
regressed beyond a set tolerance.

## The idea

- **Baseline prompt** — the current, trusted version.
- **Candidate prompt** — a proposed edit.
- Run both over the same questions, score faithfulness, compare.
- If any question drops beyond the tolerance → **FAIL** (don't ship).

Think of it as a spell-checker that runs before you ship a prompt change.

## Two parts

1. **`Prompt_Regression_Tester.ipynb`** — the core tool (runs in Google Colab).
   Scores the baseline and candidate prompts and saves the comparison to
   `regression_results.db`.
2. **This dashboard** (`app.py`) — reads that database and shows the verdict.

## Setup

```bash
pip install -r requirements.txt
```

Put `regression_results.db` (from the notebook) into the `data/` folder:

```
prompt-regression-dashboard/
├── app.py
├── requirements.txt
└── data/
    └── regression_results.db
```

Or point to it directly:

```bash
export REGRESSION_DB_PATH=/path/to/regression_results.db
```

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## What the dashboard shows

- A big **PASS / FAIL** verdict banner (green = safe, red = blocked).
- Average baseline vs. candidate scores and the overall change.
- A per-question table, worst first, with regressions highlighted in red.

## Why it matters (for interviews)

This isn't just measuring quality — it's a **safety gate for shipping AI
changes**. In a real workflow you'd wire it into CI (e.g. GitHub Actions) so it
runs automatically on every prompt edit and blocks changes that regress. That
framing — preventing silent quality loss before it reaches users — is what makes
it a strong portfolio piece.

## Sample data

The included `data/regression_results.db` shows a FAIL case (a "make it
friendlier" prompt edit that caused the assistant to add unsupported claims on
several questions). Replace it with your own runs from the notebook.
