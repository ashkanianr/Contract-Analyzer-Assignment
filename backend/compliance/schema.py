"""Pydantic models for compliance analysis output."""
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ComplianceState(str, Enum):
    FULLY_COMPLIANT = "Fully Compliant"
    PARTIALLY_COMPLIANT = "Partially Compliant"
    NON_COMPLIANT = "Non-Compliant"


class ComplianceItem(BaseModel):
    """One compliance question result."""

    compliance_question: str = Field(..., description="Short label or requirement text for the question")
    compliance_state: ComplianceState = Field(
        ...,
        description="Fully Compliant | Partially Compliant | Non-Compliant",
    )
    relevant_quotes: Union[str, List[str]] = Field(
        ...,
        description="Sections/phrases from the contract that address this requirement",
    )
    rationale: str = Field(..., description="Model's reasoning for the compliance state")
    confidence: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Optional confidence 0-100",
    )


class ComplianceResult(BaseModel):
    """Full compliance analysis result: 5 items, one per Table 1 question."""

    items: List[ComplianceItem] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Exactly 5 compliance results in Table 1 order",
    )

    @classmethod
    def from_llm_list(cls, data: List[dict]) -> "ComplianceResult":
        """Build from list of dicts (e.g. parsed LLM JSON)."""
        items = [ComplianceItem(**item) for item in data]
        return cls(items=items)
