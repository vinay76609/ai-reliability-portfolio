# AI Reliability Portfolio

Six tools for making AI and data systems **trustworthy, affordable, and self-correcting**.

Modern teams ship AI features that fail *silently* — answers degrade, retrieval grabs the wrong document, data breaks upstream, costs balloon. These six projects measure those failures, and one agent acts to fix them. Each project has a Google Colab notebook (the core logic) and a Streamlit dashboard (the visual result).

## The projects

**1. LLM Evaluation Framework** — scores an LLM's answers on faithfulness, relevance, correctness, cost, and latency using an LLM-as-judge, and tracks quality drift over time.

**2. Prompt Regression Tester** — compares a candidate prompt against a trusted baseline and blocks the change if any answer regressed. A safety gate for prompt edits.

**3. Retrieval Quality Analyzer** — measures RAG retrieval quality (Hit@k, MRR) and A/B-tests chunking strategies, showing small focused chunks beat large multi-topic ones.

**4. Data Quality & Anomaly Detector** — learns a profile of clean data, then flags schema drift, null spikes, distribution shifts, and duplicate floods in new batches.

**5. LLM Cost Router** — routes easy questions to a cheap model and hard ones to the expensive model, cutting spend with no quality loss on easy traffic.

**6. Self-Correcting RAG Agent** — an agent that retrieves, judges its own results, and reformulates weak queries until retrieval is good enough, under guardrails (tool allow-list, retry caps, relevance thresholds, audit logging).

## The theme

Projects 1-5 measure where AI and data systems fail. Project 6 is an agent that acts on those failures. Together: evaluation, regression testing, retrieval, data quality, cost optimization, and agents.

## Tech

Python · Anthropic API · sentence-transformers · DuckDB · Streamlit · pandas

## Running any project
cd <project-folder>/<dashboard-folder>
pip install -r requirements.txt
streamlit run app.py
A sample database is included in each data/ folder so the dashboard renders immediately.
