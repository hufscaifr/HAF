from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class ReportClaim(TimestampedModel):
    """A report sentence linked back to evidence, estimates, and hypotheses."""

    claim_id: str = Field(default_factory=lambda: new_id("CLAIM"))
    sentence: str
    evidence_ids: list[str] = Field(default_factory=list)
    estimate_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)


class ReportSection(TimestampedModel):
    """Named section in the final research report."""

    section_id: str = Field(default_factory=lambda: new_id("SECTION"))
    title: str
    body: str
    claim_ids: list[str] = Field(default_factory=list)


class Report(TimestampedModel):
    """Full report assembled only from approved workspace objects."""

    report_id: str = Field(default_factory=lambda: new_id("REPORT"))
    title: str
    sections: list[ReportSection] = Field(default_factory=list)
    claims: list[ReportClaim] = Field(default_factory=list)
    json_payload: dict[str, Any] = Field(default_factory=dict)
    writer: str = "deterministic"
    model: Optional[str] = None
    approved: bool = False
    verification_passed: bool = False
