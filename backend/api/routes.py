"""API routes: POST /analyze, GET /health, POST /chat (bonus)."""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend import config
from backend.compliance.analyzer import run_compliance_analysis
from backend.compliance.schema import ComplianceResult
from backend.parsing import parse_pdf, prepare_for_analysis

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    messages: list[dict] | None = None


class ChatResponse(BaseModel):
    reply: str


# In-memory store for uploaded document per session (demo only). Key = session_id or "default"
_document_store: dict[str, str] = {}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """Accept PDF upload, parse, run compliance analysis, return structured JSON."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF file required")
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)
    try:
        full_text, page_count = parse_pdf(tmp_path)
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"PDF parsing failed: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="PDF produced no text")

    prepared, was_truncated = prepare_for_analysis(full_text)
    try:
        result = run_compliance_analysis(prepared)
    except Exception as e:
        logger.exception("Compliance analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Store for optional chat (same document)
    _document_store["default"] = full_text

    response = {
        "page_count": page_count,
        "compliance": result.model_dump(),
    }
    if was_truncated:
        response["truncation_warning"] = {
            "message": (
                "Your contract together with the analysis prompt exceeds the model's context limit (~1M tokens). "
                "The document has been truncated: only the beginning and end were sent to the LLM. "
                "Results may miss content in the middle."
            ),
            "recommendations": [
                "Split the document into sections (e.g. by clauses) and analyze each section separately.",
                "Chunk the contract into smaller parts and run analysis per chunk, then combine results.",
                "Use a batch workflow: analyze chunks in parallel or sequence and merge compliance findings.",
            ],
        }
    return response


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Chat over the uploaded document. Informational only; compliance comes from /analyze."""
    doc = _document_store.get("default", "")
    if not doc:
        return ChatResponse(reply="No document has been analyzed yet. Please upload and analyze a PDF first.")
    from backend.compliance.llm_client import generate_chat
    from backend.compliance.prompts import CHAT_SYSTEM_TEMPLATE

    system = f"{CHAT_SYSTEM_TEMPLATE}\n\n## Contract text (excerpt)\n{doc[:30000]}"
    full_messages = list(body.messages or []) + [{"role": "user", "content": body.message}]
    try:
        reply = generate_chat(full_messages, system=system)
    except Exception as e:
        logger.exception("Chat failed")
        return ChatResponse(reply=f"Sorry, I could not process your question: {e}")
    return ChatResponse(reply=reply)
