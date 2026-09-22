from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from ai_research_department.enums import ReviewDecision
from ai_research_department.models import AuditLog, ResearchTask, Review
from ai_research_department.workspace.research_context import ResearchContext


class AgentResult(BaseModel):
    """Structured output returned by every agent."""

    status: str
    summary: str
    created_entities: list[str] = Field(default_factory=list)
    requested_data: list[str] = Field(default_factory=list)
    confidence: float = 0.7
    payload: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Common interface for all research agents."""

    name: str
    role: str
    seniority: str

    def __init__(self, name: str, role: str, seniority: str) -> None:
        self.name = name
        self.role = role
        self.seniority = seniority

    @abstractmethod
    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        """Run the agent against a task and shared research context."""

    def audit(
        self,
        context: ResearchContext,
        action: str,
        target: str | None = None,
        decision: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Append an audit log entry."""
        context.add_audit(
            AuditLog(
                project_id=context.project_id,
                agent=self.name,
                action=action,
                target=target,
                decision=decision,
                reason=reason,
            )
        )


class JuniorAgent(BaseAgent):
    """Base class for junior analyst agents."""

    def __init__(self, name: str, role: str) -> None:
        super().__init__(name=name, role=role, seniority="junior")


class SeniorAgent(BaseAgent):
    """Base class for senior analyst review agents."""

    def __init__(self, name: str, role: str) -> None:
        super().__init__(name=name, role=role, seniority="senior")

    def build_review(
        self,
        target_id: str,
        decision: ReviewDecision,
        feedback: str,
        missing_evidence: list[str] | None = None,
        logical_issues: list[str] | None = None,
    ) -> Review:
        """Create a standardized review object."""
        return Review(
            reviewer=self.name,
            target_id=target_id,
            decision=decision,
            feedback=feedback,
            missing_evidence=missing_evidence or [],
            logical_issues=logical_issues or [],
        )
