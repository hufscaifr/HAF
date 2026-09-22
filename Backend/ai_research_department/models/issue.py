from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class Issue(TimestampedModel):
    """Potentially valuation-relevant event discovered by the issue department."""

    issue_id: str = Field(default_factory=lambda: new_id("ISSUE"))
    company: str
    issue_type: str
    event: str
    event_date: Optional[date] = None
    importance: float = 0.5
    potential_impacts: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    approved: bool = False
