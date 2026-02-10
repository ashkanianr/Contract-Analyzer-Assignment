"""Compliance analyzer: run LLM on contract text, return validated ComplianceResult."""
import json
import logging
from typing import List

from backend.compliance.llm_client import generate
from backend.compliance.prompts import COMPLIANCE_SYSTEM_PROMPT, build_compliance_user_prompt
from backend.compliance.schema import ComplianceResult, ComplianceState

logger = logging.getLogger(__name__)


def _parse_llm_json(raw: str) -> List[dict]:
    """Parse LLM output as JSON array. Accept either a bare array or object with 'items' key."""
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM output was not valid JSON, attempting to extract array")
        # Try to find [...]
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            raise
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    raise ValueError("Expected JSON array or object with 'items' key")


def _normalize_state(s: str) -> ComplianceState:
    """Map model output to ComplianceState enum."""
    s = (s or "").strip()
    for state in ComplianceState:
        if state.value.lower() == s.lower():
            return state
    if "fully" in s.lower() and "compliant" in s.lower():
        return ComplianceState.FULLY_COMPLIANT
    if "partially" in s.lower():
        return ComplianceState.PARTIALLY_COMPLIANT
    if "non" in s.lower() or "not" in s.lower():
        return ComplianceState.NON_COMPLIANT
    return ComplianceState.PARTIALLY_COMPLIANT  # fallback


def run_compliance_analysis(contract_text: str) -> ComplianceResult:
    """
    Run compliance analysis on contract text (batched: one LLM call for all 5 requirements).
    Returns validated Pydantic ComplianceResult.
    """
    user_prompt = build_compliance_user_prompt(contract_text)
    raw = generate(user_prompt, system=COMPLIANCE_SYSTEM_PROMPT, json_mode=True)
    items_data = _parse_llm_json(raw)
    if len(items_data) != 5:
        raise ValueError(f"Expected 5 compliance items, got {len(items_data)}")
    normalized = []
    for i, item in enumerate(items_data):
        if not isinstance(item, dict):
            item = {"compliance_question": f"Question {i+1}", "compliance_state": "Partially Compliant", "relevant_quotes": "", "rationale": str(item)}
        state_val = item.get("compliance_state")
        if isinstance(state_val, str):
            item = {**item, "compliance_state": _normalize_state(state_val).value}
        normalized.append(item)
    return ComplianceResult.from_llm_list(normalized)
