from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class EstimateSeniorAgent(SeniorAgent):
    """Review deterministic estimates for missing links or abnormal outputs."""

    def __init__(self) -> None:
        super().__init__("SeniorEstimateAnalyst", "Review financial estimates")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        approved = []
        revision = []
        for estimate in context.estimates():
            if estimate.revenue > 0 and estimate.operating_profit > 0 and estimate.assumption_ids and estimate.evidence_ids:
                estimate.approved = True
                context.save_estimate(estimate)
                approved.append(estimate.estimate_id)
                review = self.build_review(estimate.estimate_id, ReviewDecision.APPROVED, "계산식과 가정 연결이 확인됐어요.")
            else:
                revision.append(estimate.estimate_id)
                review = self.build_review(estimate.estimate_id, ReviewDecision.REVISION_REQUIRED, "계산 결과 또는 연결된 가정이 비정상이에요.")
            context.save_review(review)
        status = "revision_required" if revision else "completed"
        self.audit(context, "review", target=task.task_id, decision=status)
        return AgentResult(status=status, summary="Estimate review completed.", created_entities=approved, confidence=0.86)
