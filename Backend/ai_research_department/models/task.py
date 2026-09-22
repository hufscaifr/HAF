from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from ai_research_department.enums import ResearchStage, TaskStatus
from ai_research_department.models.base import TimestampedModel, new_id


class ResearchTask(TimestampedModel):
    """A structured unit of work assigned to an agent."""

    task_id: str = Field(default_factory=lambda: new_id("TASK"))
    project_id: str
    stage: ResearchStage
    description: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    iteration: int = 0
    feedback: Optional[str] = None
