"""Extract text and tables from PDF using PyMuPDF."""
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF


def parse_pdf(pdf_path: Path) -> Tuple[str, int]:
    """
    Extract full text from a PDF. Returns (full_text, page_count).
    Tables are extracted as raw text (PyMuPDF does not have table detection;
    for table-aware extraction we rely on layout order).
    """
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    blocks: List[str] = []
    for page in doc:
        text = page.get_text("text")
        blocks.append(text)
    doc.close()
    full_text = "\n".join(blocks)
    return full_text, page_count
