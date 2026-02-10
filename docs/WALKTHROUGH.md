# Walkthrough (5–10 min)

Use this outline for the interview slide deck or verbal walkthrough.

1. **Architecture** – Upload → API → Parse → Preprocess → LLM (Gemini Flash) → Validate → JSON. Diagram: frontend (Streamlit), backend (FastAPI), pipeline stages.
2. **Data flow** – PDF bytes → PyMuPDF text → section/exhibit chunking (or page fallback) → single batched compliance prompt → Pydantic-validated JSON → UI.
3. **Per-requirement model** – Core architecture is one requirement at a time; we batch into one call for demo simplicity when the document fits context.
4. **LLM** – Primary: Gemini Flash (fast, long context). Backup: OpenRouter, same model family. Provider abstracted behind client.
5. **Not policy matching** – Policy is encoded in the five requirements; we only check contract language against them.
6. **Chat** – Informational only; compliance decisions always from the structured analyzer.
7. **Evaluation** – Golden PDF + reference JSON; script reports schema pass and state match count (Section 11).
