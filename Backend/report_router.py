from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from report_models import Report
from report_schemas import (
    ReportCreate,
    ReportListResponse,
    ReportResponse,
    ReportUpdate,
)


router = APIRouter(tags=["reports"])
DbSession = Annotated[Session, Depends(get_db)]


def require_reports_admin(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected_token = os.getenv("REPORTS_ADMIN_TOKEN", "").strip()
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="REPORTS_ADMIN_TOKEN is not configured.",
        )

    scheme, _, supplied_token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(
        supplied_token,
        expected_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reports admin token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


ReportsAdmin = Annotated[None, Depends(require_reports_admin)]


@router.get("/api/reports", response_model=ReportListResponse)
def list_published_reports(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReportListResponse:
    condition = Report.status == "published"
    total = db.scalar(select(func.count()).select_from(Report).where(condition)) or 0
    reports = db.scalars(
        select(Report)
        .where(condition)
        .order_by(Report.published_at.desc(), Report.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return ReportListResponse(items=list(reports), total=total, limit=limit, offset=offset)


@router.get("/api/reports/{report_id}", response_model=ReportResponse)
def get_published_report(report_id: str, db: DbSession) -> Report:
    report = db.scalar(
        select(Report).where(Report.id == report_id, Report.status == "published")
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("/api/admin/reports", response_model=ReportListResponse)
def list_admin_reports(
    db: DbSession,
    _: ReportsAdmin,
    report_status: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReportListResponse:
    query = select(Report)
    count_query = select(func.count()).select_from(Report)
    if report_status:
        query = query.where(Report.status == report_status)
        count_query = count_query.where(Report.status == report_status)

    total = db.scalar(count_query) or 0
    reports = db.scalars(
        query.order_by(Report.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return ReportListResponse(items=list(reports), total=total, limit=limit, offset=offset)


@router.post(
    "/api/internal/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report_from_n8n(
    payload: ReportCreate,
    db: DbSession,
    _: ReportsAdmin,
) -> Report:
    if payload.external_id:
        existing = db.scalar(
            select(Report).where(Report.external_id == payload.external_id)
        )
        if existing is not None:
            return existing

    report = Report(
        **payload.model_dump(mode="json"),
        status="draft",
    )
    db.add(report)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Report already exists.") from exc
    db.refresh(report)
    return report


@router.patch("/api/admin/reports/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: str,
    payload: ReportUpdate,
    db: DbSession,
    _: ReportsAdmin,
) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    updates = payload.model_dump(exclude_unset=True, mode="json")
    for field, value in updates.items():
        setattr(report, field, value)

    if updates.get("status") == "published" and report.published_at is None:
        report.published_at = datetime.now(timezone.utc)
    elif updates.get("status") in {"draft", "rejected"}:
        report.published_at = None

    db.commit()
    db.refresh(report)
    return report


@router.post("/api/admin/reports/{report_id}/publish", response_model=ReportResponse)
def publish_report(report_id: str, db: DbSession, _: ReportsAdmin) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    report.status = "published"
    report.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report
