from __future__ import annotations

from enum import Enum


class ResearchStage(str, Enum):
    ISSUE_DISCOVERY = "issue_discovery"
    CAUSE_ANALYSIS = "cause_analysis"
    DATA_COLLECTION = "data_collection"
    FUNDAMENTAL_FORECAST = "fundamental_forecast"
    ESTIMATION = "estimation"
    RISK_ANALYSIS = "risk_analysis"
    REPORT_WRITING = "report_writing"
    MERGING = "merging"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
