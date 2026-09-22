from __future__ import annotations

from ai_research_department.agents.base import AgentResult, BaseAgent
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.lineage import validate_claim_lineage
from ai_research_department.workspace.research_context import ResearchContext


class FactCheckerAgent(BaseAgent):
    """Verify that report claims have evidence lineage."""

    def __init__(self) -> None:
        super().__init__("FactCheckerAgent", "Check report facts", "checker")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        report = context.reports()[-1]
        errors = []
        for claim in report.claims:
            errors.extend(validate_claim_lineage(claim, context.evidence(), context.estimates(), context.hypotheses()))
        status = "completed" if not errors else "revision_required"
        self.audit(context, "fact_check", target=report.report_id, decision=status, reason="; ".join(errors) or None)
        return AgentResult(status=status, summary="All evidence links valid." if not errors else "; ".join(errors), confidence=0.9 if not errors else 0.3)
