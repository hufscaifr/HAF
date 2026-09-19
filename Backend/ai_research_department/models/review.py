from __future__ import annotations

from pydantic import Field

from ai_research_department.enums import ReviewDecision
from ai_research_department.models.base import TimestampedModel, new_id


class Review(TimestampedModel):
    """Senior analyst review decision for a structured output."""

    review_id: str = Field(default_factory=lambda: new_id("REVIEW"))
    reviewer: str
    target_id: str
    decision: ReviewDecision
    feedback: str
    missing_evidence: list[str] = Field(default_factory=list)
    logical_issues: list[str] = Field(default_factory=list)
