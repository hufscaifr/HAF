from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import Field

from ai_research_department.models.base import TimestampedModel, new_id, utc_now


class Evidence(TimestampedModel):
    """A source-backed fact used by downstream analysis."""

    evidence_id: str = Field(default_factory=lambda: new_id("EVIDENCE"))
    company: str
    fact: str
    metric: Optional[str] = None
    value: Optional[Union[float, str]] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    comparison: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    source_type: str
    published_at: Optional[datetime] = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    confidence: float = 0.7
    verified: bool = False
    raw_text: Optional[str] = None
