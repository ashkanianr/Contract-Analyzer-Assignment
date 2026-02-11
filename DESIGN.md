# Design Rationale

## Scope

This system checks **contract language** against five fixed compliance requirements (Table 1). It does not retrieve, rank, or interpret internal policy documents.

**The internal policy is already encoded in the compliance requirements. This system does not retrieve, rank, or interpret policy documents; it only checks for explicit contractual language.**

## Architecture

- **Per-requirement evaluation**: The core model is one requirement at a time. For demo simplicity we batch all five into one LLM call when the document fits the context window; that is a batching optimization, not a conceptual dependency. Implementing 5 separate calls (Option B) would give the same logical model and better failure isolation.
- **Pipeline**: PDF → parse (PyMuPDF) → preprocess (whitespace normalization) → one LLM call (Gemini Flash) → Pydantic validation → JSON response.

## LLM and hosting

- **Primary: Gemini Flash** (fast, long context). **Backup: OpenRouter** with the same model family. Provider choice is **abstracted behind an LLM client**; swapping or fallback does not change analyzer logic.
- We use the **google-genai** SDK (not the deprecated google-generativeai). Install with `pip install --upgrade google-genai`.

## PDF and preprocessing

- **Library**: PyMuPDF for text extraction. Tables are extracted as raw text.
- **Preprocessing**: Whitespace normalization only. Gemini 3 Flash has 1M input tokens (~2,500+ typical PDF pages); because the context window is that large, no sectionizing or chunking is needed. The full document is sent at once.

## Prompt and schema

- Prompts live in `backend/compliance/prompts.py` (Table 1 text + system/user builders).
- Output is validated with **Pydantic** only; schema in `backend/compliance/schema.py`. No other schema library.

## Chat

- **Chat is informational only. Compliance decisions always come from the structured analyzer.** This is important in regulated contexts and should be stated in review and interviews.

## Tradeoffs

- **Single batched call vs 5 calls**: We use one call for simplicity and lower latency; the mental model remains per-requirement. Five calls would improve isolation and per-question debugging.
- **Streamlit vs SPA**: Streamlit was chosen for a simple UI and fast iteration; the backend is framework-agnostic.
