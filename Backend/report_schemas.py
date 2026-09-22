from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


ReportStatus = Literal["draft", "published", "rejected"]


class ReportCreate(BaseModel):
    external_id: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    summary: str = ""
    content: str | None = None
    thumbnail_url: HttpUrl | None = None
    file_url: HttpUrl | None = None
    created_by: str = Field(default="n8n", min_length=1, max_length=100)


class ReportUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    summary: str | None = None
    content: str | None = None
    thumbnail_url: HttpUrl | None = None
    file_url: HttpUrl | None = None
    status: ReportStatus | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str | None
    title: str
    summary: str
    content: str | None
    thumbnail_url: str | None
    file_url: str | None
    status: ReportStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    limit: int
    offset: int
