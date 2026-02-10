"""Preprocess extracted PDF text: clean and chunk by section/exhibit (plan 3.1a)."""
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Chunk:
    """A labeled chunk of contract text."""
    label: str
    text: str


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace; preserve single newlines."""
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n", "\n\n", text)).strip()


def chunk_by_structure(text: str) -> List[Chunk]:
    """
    Split text into chunks by section and exhibit boundaries (plan 3.1a).
    Boundaries: main sections "1. ", "2. ", ... "21. "; Exhibits "Exhibit A —", ... "Exhibit H —";
    within Exhibit G: "G1.", "G2.", "G3A.", ... "G13.".
    Fallback: if no boundaries found, chunk by page marker "-- N of M --".
    """
    lines = text.split("\n")
    chunks: List[Chunk] = []
    current_label = "Preamble"
    current_lines: List[str] = []

    # Top-level section: "1. ", "2. ", ... "21. " at start of line (after optional whitespace)
    main_section_re = re.compile(r"^(\d{1,2})\.\s+[A-Z]")
    exhibit_re = re.compile(r"^Exhibit\s+([A-H])\s*[—\-]")
    exhibit_g_block_re = re.compile(r"^(G\d+A?\.)\s")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            current_lines.append(line)
            continue

        new_label = None

        if main_section_re.match(stripped):
            # e.g. "1. Order of Precedence", "6. Identity, Access..."
            num = main_section_re.match(stripped).group(1)
            new_label = f"Section {num}"
        elif exhibit_re.search(stripped):
            m = exhibit_re.search(stripped)
            if m:
                new_label = f"Exhibit {m.group(1)}"
        elif exhibit_g_block_re.match(stripped):
            m = exhibit_g_block_re.match(stripped)
            if m:
                new_label = f"Exhibit G ({m.group(1).rstrip('.')})"
        elif re.match(r"^--\s*\d+\s+of\s+\d+\s*--", stripped) and not chunks and not current_label.startswith("Section"):
            # Page marker as fallback when we haven't seen sections yet
            page_num = re.search(r"\d+", stripped)
            if page_num:
                new_label = f"Page {page_num.group()}"

        if new_label and (current_lines or current_label != "Preamble"):
            chunk_text = _normalize_whitespace("\n".join(current_lines))
            if chunk_text:
                chunks.append(Chunk(label=current_label, text=chunk_text))
            current_label = new_label
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        chunk_text = _normalize_whitespace("\n".join(current_lines))
        if chunk_text:
            chunks.append(Chunk(label=current_label, text=chunk_text))

    if not chunks and text.strip():
        # No structure detected: single chunk or page-based fallback
        parts = re.split(r"\n\s*--\s*\d+\s+of\s+\d+\s*--\s*\n", text)
        if len(parts) > 1:
            for idx, part in enumerate(parts):
                p = _normalize_whitespace(part)
                if p:
                    chunks.append(Chunk(label=f"Page {idx + 1}", text=p))
        else:
            chunks.append(Chunk(label="Full document", text=_normalize_whitespace(text)))
    return chunks


def prepare_for_analysis(text: str, max_tokens_approx: int = 100_000) -> str:
    """
    Prepare contract text for LLM: chunk by structure, then concatenate with labels
    if under token limit (approximate: 1 char ~ 0.25 tokens). Returns a single string
    with labeled sections for one LLM call.
    """
    chunks = chunk_by_structure(text)
    labeled = "\n\n".join(f"[{c.label}]\n{c.text}" for c in chunks)
    if len(labeled) * 0.25 > max_tokens_approx:
        # Truncate if extremely long (keep start + end)
        half = max_tokens_approx // 2
        labeled = labeled[: int(half * 4)] + "\n\n[... truncated ...]\n\n" + labeled[-int(half * 4) :]
    return labeled
