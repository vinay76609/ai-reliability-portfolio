# Self-Correcting RAG Agent (with Guardrails)

An **agent** that fixes its own bad retrieval. A normal RAG system retrieves once
and answers even if it grabbed the wrong documents. This agent retrieves, judges
whether the results actually answer the question, and if not, rewrites the query
and tries again — all under guardrails that keep it safe and bounded.

## Why it's an "agent"

It works toward a goal over multiple steps, deciding what to do next and using
tools: **retrieve → judge → reformulate → retry**. That loop (think → act →
observe → repeat) is what separates an agent from a one-shot chatbot.

## The guardrails (the reliability part)

- **Tool allow-list** — may only call approved tools; anything else is refused.
- **Max-retries cap** — stops after N attempts instead of looping forever.
- **Relevance threshold** — only accepts an answer once retrieval clears a bar.
- **Decision log** — every tool call is recorded and auditable.

Making an agent work once is easy; making it *reliable* is the hard, hireable part.

## Two parts

1. **`RAG_Agent_Guardrails.ipynb`** — the agent (runs in Google Colab). Uses free
   local embeddings, self-corrects a weak query, saves `agent_results.db`.
2. **This dashboard** (`app.py`) — visualizes the run: outcome, the attempt-by-
   attempt loop, the guardrails, and the full decision log.

## Setup

```bash
pip install -r requirements.txt
```

Put `agent_results.db` (from the notebook) in the `data/` folder:

```
rag-agent-dashboard/
├── app.py
├── requirements.txt
└── data/
    └── agent_results.db
```

Or point to it: `export AGENT_DB_PATH=/path/to/agent_results.db`

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## Why it matters (for interviews)

Agents are the hottest area in AI, but the hard part isn't making one work once —
it's making it *reliable*. This agent fixes the exact RAG retrieval problem that
the Retrieval Quality Analyzer measures, and does it safely with guardrails. The
story: **"I built tools to measure RAG failures, then an agent that autonomously
and safely fixes them."**

## Sample data

The included `data/agent_results.db` shows a 2-attempt self-correction (weak first
query → reformulated → sufficient). Replace it with your own runs from the notebook.
