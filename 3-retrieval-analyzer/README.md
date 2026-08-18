## Retrieval Quality Analyzer

Diagnoses **why a RAG system retrieves the wrong document** — the most common,
most invisible failure in AI apps that answer from your own documents.

Most RAG systems fail at *retrieval*, not generation: the AI writes a fluent,
confident answer from the wrong source because the search step fetched the wrong
document. This tool measures retrieval quality directly and experiments to
improve it.

### How it works

- **Embeddings** convert every document and question into meaning-vectors (using
  a small, free local model — no API key needed).
- **Retrieval** returns the documents whose vectors are closest to the question.
- **Metrics** grade it against known-correct answers:
  - **Hit@k** — how often the correct document is retrieved at all.
  - **MRR** — how highly the correct document is ranked.
- **A/B experiment** — compares **big chunks vs. small chunks** and shows which
  retrieves better. (Spoiler: small chunks usually win, often dramatically — one
  of the biggest and most overlooked levers in RAG.)

### Two parts

1. **`Retrieval_Quality_Analyzer.ipynb`** — the core tool (runs in Google Colab).
   Builds the search index, runs the experiment, saves `retrieval_results.db`.
2. **This dashboard** (`app.py`) — reads that database and shows the head-to-head
   comparison, a metrics bar chart, and a per-question ✓/✗ grid.

### Setup

```bash
pip install -r requirements.txt
```

Put `retrieval_results.db` (from the notebook) in the `data/` folder:

```
retrieval-analyzer-dashboard/
├── app.py
├── requirements.txt
└── data/
    └── retrieval_results.db
```

Or point to it: `export RETRIEVAL_DB_PATH=/path/to/retrieval_results.db`

### Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

### Why it matters (for interviews)

Everyone builds "a RAG chatbot." Far fewer can *measure and diagnose* why one
retrieves badly. Building the diagnostic — and showing that chunk size alone
swings retrieval quality by a large margin — demonstrates you understand *why*
RAG fails, not just how to wire it up. That's the more senior skill.

### Sample data

The included `data/retrieval_results.db` shows small chunks beating big chunks
(MRR 0.88 vs 0.55). Replace it with your own runs from the notebook.
