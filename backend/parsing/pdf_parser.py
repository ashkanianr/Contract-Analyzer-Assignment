"""Extract text and tables from PDF using pdfplumber."""
from pathlib import Path
from typing import Tuple

import pdfplumber


def parse_pdf(pdf_path: Path) -> Tuple[str, int]:
    """
    Extract full text from a PDF. Returns (full_text, page_count).
    pdfplumber provides better layout analysis and table handling than raw text extraction.
    """
    blocks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                blocks.append(text)
        page_count = len(pdf.pages)
    full_text = "\n".join(blocks) if blocks else ""
    return full_text, page_count
