from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class FinancialEstimate(TimestampedModel):
    """Deterministically calculated financial estimate."""

    estimate_id: str = Field(default_factory=lambda: new_id("EST"))
    period: str
    revenue: float
    operating_profit: float
    eps: float
    previous_eps: Optional[float] = None
    eps_revision_pct: Optional[float] = None
    assumption_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    approved: bool = False


class Consensus(TimestampedModel):
    """Optional market consensus data, never fabricated by the workflow."""

    consensus_id: str = Field(default_factory=lambda: new_id("CONSENSUS"))
    metric: str
    period: str
    value: Optional[float] = None
    available: bool = False
    source_name: Optional[str] = None
