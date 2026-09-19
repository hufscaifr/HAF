from __future__ import annotations

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class RiskAssessment(TimestampedModel):
    """Issue-level risk assessment linking events to price and fundamentals."""

    risk_id: str = Field(default_factory=lambda: new_id("RISK"))
    issue_id: str
    hypothesis_ids: list[str] = Field(default_factory=list)
    title: str
    risk_type: str
    description: str
    likelihood: str = "medium"
    severity: str = "medium"
    affected_metrics: list[str] = Field(default_factory=list)
    fundamental_impact: str
    price_impact: str
    verification_view: str
    mitigation_or_monitoring: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    estimate_ids: list[str] = Field(default_factory=list)
    approved: bool = False
    confidence: float = 0.7
