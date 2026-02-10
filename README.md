# Contract Analyzer

End-to-end prototype: upload a PDF contract, get structured compliance analysis (5 questions from Table 1) and optional chat over the document.

## Requirements

- Python 3.10+
- API keys: **GOOGLE_API_KEY** (Gemini); optionally **OPENROUTER_API_KEY** for backup when primary hits rate limit. Default model: **Gemini 3 Flash Preview**.

## Quick start

### 1. Backend

```bash
cd "Contract Analyzer Assignment"
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
pip install --upgrade google-genai
```

Copy `.env.example` to `.env` and add your keys:

```bash
copy .env.example .env
# Edit .env: set GOOGLE_API_KEY=your_key_here (and optionally OPENROUTER_API_KEY)
```

Then run:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  
- Analyze: `POST /api/analyze` (multipart PDF)

### 2. Frontend

```bash
cd frontend
pip install -r requirements.txt
set BACKEND_URL=http://localhost:8000
streamlit run app.py
```

- Open the URL shown (e.g. http://localhost:8501).  
- Upload a PDF, click **Analyze**, view compliance results.  
- Chat (optional) is informational only; compliance decisions come from the structured analyzer.

## Environment variables

Set them in `.env` (copy from `.env.example`) or in your shell. Do not commit `.env` to git.

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key (AI Studio). Required for primary LLM. |
| `OPENROUTER_API_KEY` | Optional. Used when primary returns 429/quota. |
| `LLM_PRIMARY` | `google` (default) or `openrouter`. |
| `LLM_MODEL_GOOGLE` | Default: `gemini-3-flash-preview`. |
| `LLM_MODEL_OPENROUTER` | Default: `google/gemini-3-flash-preview`. |
| `BACKEND_URL` | Backend base URL for the Streamlit app (default `http://localhost:8000`). |

## Project structure

- `backend/` – FastAPI app, PDF parsing, compliance analyzer, LLM client (Gemini + OpenRouter).
- `frontend/` – Streamlit app (upload, analyze, results, chat).
- `eval/` – Evaluation script and reference JSON (Section 11 of plan).
- `DESIGN.md` – Design rationale and tradeoffs.

## Evaluation

Run evaluation on the sample contract (requires backend on `PYTHONPATH`):

```bash
set PYTHONPATH=.
python eval/run_eval.py
```

See `eval/README.md` and plan Section 11 for details.
