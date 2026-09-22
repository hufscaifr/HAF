from __future__ import annotations

from ai_research_department.agents.base import AgentResult, BaseAgent
from ai_research_department.financial.calculations import calculate_revision_pct
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class NumericalCheckerAgent(BaseAgent):
    """Recalculate numerical relationships in estimates."""

    def __init__(self) -> None:
        super().__init__("NumericalCheckerAgent", "Check deterministic calculations", "checker")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        errors: list[str] = []
        for estimate in context.estimates():
            expected = calculate_revision_pct(estimate.eps, estimate.previous_eps)
            if expected is not None and round(expected, 2) != round(estimate.eps_revision_pct or 0, 2):
                errors.append(f"{estimate.estimate_id} EPS revision mismatch.")
        status = "completed" if not errors else "revision_required"
        self.audit(context, "numerical_check", target=task.task_id, decision=status, reason="; ".join(errors) or None)
        return AgentResult(status=status, summary="All calculations verified." if not errors else "; ".join(errors), confidence=0.92 if not errors else 0.3)
