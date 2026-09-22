from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai_research_department.enums import Priority
from ai_research_department.models.base import TimestampedModel, new_id


class DataRequest(TimestampedModel):
    """Request for the data department to collect source-backed evidence."""

    request_id: str = Field(default_factory=lambda: new_id("REQ"))
    requested_by: str
    metric: str
    period: Optional[str] = None
    reason: str
    priority: Priority = Priority.MEDIUM
    fulfilled: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
