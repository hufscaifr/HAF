from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class DataSeniorAgent(SeniorAgent):
    """Review collected evidence for source quality."""

    def __init__(self) -> None:
        super().__init__("SeniorDataAnalyst", "Review evidence quality")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        approved = 0
        revision = 0
        for evidence in context.evidence():
            if evidence.source_name and evidence.verified and evidence.confidence >= 0.7:
                approved += 1
                review = self.build_review(evidence.evidence_id, ReviewDecision.APPROVED, "출처와 검증 상태가 충분해요.")
            else:
                revision += 1
                review = self.build_review(evidence.evidence_id, ReviewDecision.REVISION_REQUIRED, "출처 확인이 더 필요해요.")
            context.save_review(review)
        status = "revision_required" if revision else "completed"
        artifact_count = len(context.charts()) + len(context.tables())
        self.audit(context, "review", target=task.task_id, decision=status)
        return AgentResult(
            status=status,
            summary=f"{approved} evidence approved. {artifact_count} visualization artifacts available.",
            confidence=0.84,
        )
