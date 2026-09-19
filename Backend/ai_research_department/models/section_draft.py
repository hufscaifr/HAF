from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class ReportSectionDraft(TimestampedModel):
    """Department-level report section draft for final merging."""

    draft_id: str = Field(default_factory=lambda: new_id("DRAFT"))
    department: str
    section_key: str
    title: str
    summary: str
    bullets: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    chart_ids: list[str] = Field(default_factory=list)
    table_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.75
    writer: str = "deterministic"
    model: Optional[str] = None
    approved: bool = False
