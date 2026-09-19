from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.utcnow()


def new_id(prefix: str) -> str:
    """Create a readable unique identifier with a domain prefix."""
    return f"{prefix}_{uuid4().hex[:12].upper()}"


class CAMBaseModel(BaseModel):
    """Compatibility base model for Pydantic v1 and v2 style serialization."""

    def to_payload(self) -> dict[str, Any]:
        """Serialize the model to a JSON-friendly dict."""
        return self.dict()


class TimestampedModel(CAMBaseModel):
    created_at: datetime = Field(default_factory=utc_now)
