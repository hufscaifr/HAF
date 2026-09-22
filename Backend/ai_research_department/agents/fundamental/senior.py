from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class FundamentalSeniorAgent(SeniorAgent):
    """Review assumptions before financial modeling."""

    def __init__(self) -> None:
        super().__init__("SeniorFundamentalAnalyst", "Review business assumptions")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        approved = []
        revision = []
        for forecast in context.forecasts():
            if forecast.evidence_ids and forecast.confidence >= 0.7:
                forecast.approved = True
                context.save_forecast(forecast)
                approved.append(forecast.forecast_id)
                review = self.build_review(forecast.forecast_id, ReviewDecision.APPROVED, "사업 방향성 가정이 근거와 연결돼 있어요.")
            else:
                revision.append(forecast.forecast_id)
                review = self.build_review(forecast.forecast_id, ReviewDecision.REVISION_REQUIRED, "Forecast 근거가 부족해요.")
            context.save_review(review)
        status = "revision_required" if revision else "completed"
        self.audit(context, "review", target=task.task_id, decision=status)
        return AgentResult(status=status, summary="Fundamental review completed.", created_entities=approved, confidence=0.82)
