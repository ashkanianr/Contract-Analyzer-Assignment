"""Preprocess extracted PDF text: clean for LLM. No chunking; Gemini 3 Flash has 1M input tokens."""
import re


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace; preserve single newlines."""
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n", "\n\n", text)).strip()


def prepare_for_analysis(text: str, max_tokens_approx: int = 900_000) -> str:
    """Prepare contract text for LLM. Gemini 3 Flash has 1M input tokens (~2,500+ typical PDF pages); because the context window is that large, no sectionizing is needed."""
    cleaned = _normalize_whitespace(text)
    if len(cleaned) * 0.25 > max_tokens_approx:
        half = max_tokens_approx // 2
        cleaned = cleaned[: int(half * 4)] + "\n\n[... truncated ...]\n\n" + cleaned[-int(half * 4) :]
    return cleaned
