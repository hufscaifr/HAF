from __future__ import annotations

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class Hypothesis(TimestampedModel):
    """Causal explanation that links an issue to business or financial metrics."""

    hypothesis_id: str = Field(default_factory=lambda: new_id("HYP"))
    issue_id: str
    cause: str
    affected_metric: str
    direction: str
    time_horizon: str
    confidence: float
    required_data: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    approved: bool = False
