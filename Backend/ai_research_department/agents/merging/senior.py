from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.lineage import validate_claim_lineage
from ai_research_department.workspace.research_context import ResearchContext


class MergingSeniorAgent(SeniorAgent):
    """Review the merged final report before verification."""

    def __init__(self) -> None:
        super().__init__("SeniorMergingEditor", "Review merged final report")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        report = context.reports()[-1]
        errors = []
        for claim in report.claims:
            errors.extend(validate_claim_lineage(claim, context.evidence(), context.estimates(), context.hypotheses()))
        if errors:
            context.save_review(self.build_review(report.report_id, ReviewDecision.REVISION_REQUIRED, "근거 없는 Claim이 있어요.", logical_issues=errors))
            self.audit(context, "review", target=report.report_id, decision="revision_required", reason="; ".join(errors))
            return AgentResult(status="revision_required", summary="Unsupported merged report claims found.", confidence=0.4)
        report.approved = True
        context.save_report(report)
        context.save_review(self.build_review(report.report_id, ReviewDecision.APPROVED, "Merged report lineage가 확인됐어요."))
        self.audit(context, "review", target=report.report_id, decision="approved")
        return AgentResult(status="completed", summary="Merged report approved.", created_entities=[report.report_id], confidence=0.9)
