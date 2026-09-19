from __future__ import annotations

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.financial.calculations import (
    calculate_eps,
    calculate_gross_profit,
    calculate_operating_profit,
    calculate_revenue,
    calculate_revision_pct,
)
from ai_research_department.models import FinancialEstimate, ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class EstimateJuniorAgent(JuniorAgent):
    """Convert approved assumptions into deterministic financial estimates."""

    def __init__(self) -> None:
        super().__init__("EstimateJuniorAgent", "Calculate financial estimates")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        if context.project.request.data_mode == "real":
            return await self._execute_real(task, context)

        assumptions = {item.metric: item for item in context.assumptions()}
        volume = float(assumptions["shipment_volume"].value)
        asp = float(assumptions["asp"].value)
        gross_margin = float(assumptions["gross_margin"].value)
        revenue = calculate_revenue(volume, asp)
        gross_profit = calculate_gross_profit(revenue, gross_margin)
        operating_expenses = revenue * 0.18
        operating_profit = calculate_operating_profit(gross_profit, operating_expenses)
        net_income = operating_profit * 0.72
        shares_outstanding = 1.0
        eps = calculate_eps(net_income, shares_outstanding)
        previous_eps = 1600.0
        estimate = FinancialEstimate(
            period="2027E",
            revenue=round(revenue, 2),
            operating_profit=round(operating_profit, 2),
            eps=round(eps, 2),
            previous_eps=previous_eps,
            eps_revision_pct=round(calculate_revision_pct(eps, previous_eps) or 0, 2),
            assumption_ids=[item.assumption_id for item in assumptions.values()],
            evidence_ids=[eid for item in assumptions.values() for eid in item.evidence_ids],
        )
        context.save_estimate(estimate)
        self.audit(context, "execute", target=task.task_id, reason=f"2027E EPS calculated at {estimate.eps}")
        return AgentResult(
            status="completed",
            summary=f"2027E Operating Profit revised; EPS revision {estimate.eps_revision_pct}%.",
            created_entities=[estimate.estimate_id],
            confidence=0.86,
        )

    async def _execute_real(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        assumptions = {item.metric: item for item in context.assumptions()}
        revenue = self._float_assumption(assumptions, "revenue")
        operating_profit = self._float_assumption(assumptions, "operating_income")
        eps = self._float_assumption(assumptions, "eps")
        if revenue is None or operating_profit is None or eps is None:
            return AgentResult(
                status="revision_required",
                summary="Revenue, operating income, or EPS evidence is missing for real estimate.",
                confidence=0.35,
            )
        estimate = FinancialEstimate(
            period=str(context.project.request.as_of_date.year),
            revenue=round(revenue, 2),
            operating_profit=round(operating_profit, 2),
            eps=round(eps, 2),
            previous_eps=None,
            eps_revision_pct=None,
            assumption_ids=[item.assumption_id for item in assumptions.values()],
            evidence_ids=[eid for item in assumptions.values() for eid in item.evidence_ids],
        )
        context.save_estimate(estimate)
        self.audit(context, "execute", target=task.task_id, reason="Real estimate snapshot created from collected evidence")
        return AgentResult(
            status="completed",
            summary="Real estimate snapshot created from collected evidence.",
            created_entities=[estimate.estimate_id],
            confidence=0.82,
        )

    def _float_assumption(self, assumptions: dict, metric: str) -> float | None:
        assumption = assumptions.get(metric)
        if assumption is None:
            return None
        try:
            return float(assumption.value)
        except (TypeError, ValueError):
            return None
