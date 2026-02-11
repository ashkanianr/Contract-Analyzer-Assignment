"""Preprocess extracted PDF text: clean for LLM. No chunking; Gemini 3 Flash has 1M input tokens."""
import re
from typing import Tuple


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace; preserve single newlines."""
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n", "\n\n", text)).strip()


def prepare_for_analysis(text: str, max_tokens_approx: int = 900_000) -> Tuple[str, bool]:
    """Prepare contract text for LLM. Returns (cleaned_text, was_truncated)."""
    cleaned = _normalize_whitespace(text)
    was_truncated = False
    if len(cleaned) * 0.25 > max_tokens_approx:
        half = max_tokens_approx // 2
        cleaned = cleaned[: int(half * 4)] + "\n\n[... truncated ...]\n\n" + cleaned[-int(half * 4) :]
        was_truncated = True
    return cleaned, was_truncated
