from __future__ import annotations

from typing import Optional, Union

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id


class FundamentalAssumption(TimestampedModel):
    """Business assumption approved before numerical estimation."""

    assumption_id: str = Field(default_factory=lambda: new_id("ASSUMPTION"))
    metric: str
    value: Union[float, str]
    unit: Optional[str] = None
    period: Optional[str] = None
    reasoning: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.7


class Forecast(TimestampedModel):
    """Directional change in a business driver."""

    forecast_id: str = Field(default_factory=lambda: new_id("FORECAST"))
    metric: str
    previous_assumption: Optional[float] = None
    new_assumption: Optional[float] = None
    unit: Optional[str] = None
    direction: str
    reasoning: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.7
    approved: bool = False
