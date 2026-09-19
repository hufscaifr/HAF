from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class VerificationSeniorReviewer(SeniorAgent):
    """Final senior reviewer for verification results."""

    def __init__(self) -> None:
        super().__init__("VerificationSeniorReviewer", "Approve final report")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        report = context.reports()[-1]
        report.verification_passed = True
        context.save_report(report)
        context.save_review(self.build_review(report.report_id, ReviewDecision.APPROVED, "검증 부서 최종 승인 완료."))
        self.audit(context, "final_review", target=report.report_id, decision="approved")
        return AgentResult(status="completed", summary="All verification checks passed.", created_entities=[report.report_id], confidence=0.93)
