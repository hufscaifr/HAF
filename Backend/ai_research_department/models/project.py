from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import Field

from ai_research_department.enums import ResearchStage
from ai_research_department.models.base import TimestampedModel, new_id


class ResearchRequest(TimestampedModel):
    """Input handed from the Research Director to the organization."""

    company: str
    ticker: str = ""
    market: Optional[str] = None
    research_type: str = "earnings_preview"
    as_of_date: date = Field(default_factory=date.today)
    objective: str = "Build an evidence-linked equity research report."
    data_mode: Literal["mock", "real"] = "mock"
    price_period: str = "6mo"
    price_interval: str = "1d"
    refresh_krx_listings: bool = False


class ResearchProject(TimestampedModel):
    """Top-level research project state."""

    project_id: str = Field(default_factory=lambda: new_id("PROJECT"))
    request: ResearchRequest
    stage: ResearchStage = ResearchStage.ISSUE_DISCOVERY
    completed_departments: list[str] = Field(default_factory=list)
    rejected_tasks: list[str] = Field(default_factory=list)
    unresolved_hypotheses: list[str] = Field(default_factory=list)
    report_ready: bool = False
    final_report_id: Optional[str] = None
    requires_human_review: bool = False
