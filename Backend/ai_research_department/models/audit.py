from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class AuditLog(TimestampedModel):
    """Trace of an agent action or workflow decision."""

    audit_id: str = Field(default_factory=lambda: new_id("AUDIT"))
    project_id: str
    agent: str
    action: str
    target: Optional[str] = None
    decision: Optional[str] = None
    reason: Optional[str] = None
