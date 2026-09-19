from __future__ import annotations

from ai_research_department.agents.base import AgentResult, BaseAgent
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class ConsistencyCheckerAgent(BaseAgent):
    """Check report sections against estimate values."""

    def __init__(self) -> None:
        super().__init__("ConsistencyCheckerAgent", "Check report consistency", "checker")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        report = context.reports()[-1]
        text = "\n".join(section.body for section in report.sections)
        errors = []
        for estimate in context.estimates():
            if report.json_payload:
                snapshot = report.json_payload.get("financial_snapshot", {})
                if not self._payload_has_value(snapshot, estimate.revenue):
                    errors.append(f"{estimate.estimate_id} revenue missing from report JSON.")
                if not self._payload_has_value(snapshot, estimate.operating_profit):
                    errors.append(f"{estimate.estimate_id} operating profit missing from report JSON.")
                continue
            if f"{estimate.revenue:,.2f}" not in text or f"{estimate.operating_profit:,.2f}" not in text:
                errors.append(f"{estimate.estimate_id} values missing from report text.")
        status = "completed" if not errors else "revision_required"
        self.audit(context, "consistency_check", target=report.report_id, decision=status, reason="; ".join(errors) or None)
        return AgentResult(status=status, summary="Report and estimate values are consistent." if not errors else "; ".join(errors), confidence=0.9 if not errors else 0.4)

    def _payload_has_value(self, payload, expected: float, tolerance: float = 0.01) -> bool:
        if isinstance(payload, dict):
            return any(self._payload_has_value(value, expected, tolerance) for value in payload.values())
        if isinstance(payload, list):
            return any(self._payload_has_value(value, expected, tolerance) for value in payload)
        try:
            return abs(float(payload) - float(expected)) <= tolerance
        except (TypeError, ValueError):
            return False
