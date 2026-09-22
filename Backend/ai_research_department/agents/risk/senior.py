from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class RiskSeniorAgent(SeniorAgent):
    """Review risk assessments for evidence links and analytical completeness."""

    def __init__(self) -> None:
        super().__init__("SeniorRiskAnalyst", "Review risk impact and validation work")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        risks = context.risk_assessments()
        if not risks:
            return AgentResult(status="revision_required", summary="Risk assessments are missing.", confidence=0.3)

        valid_issue_ids = {item.issue_id for item in context.issues()}
        valid_hypothesis_ids = {item.hypothesis_id for item in context.hypotheses()}
        valid_evidence_ids = {item.evidence_id for item in context.evidence()}
        valid_estimate_ids = {item.estimate_id for item in context.estimates()}
        errors: list[str] = []

        for risk in risks:
            local_errors: list[str] = []
            if risk.issue_id not in valid_issue_ids:
                local_errors.append("invalid issue_id")
            invalid_hypotheses = [item for item in risk.hypothesis_ids if item not in valid_hypothesis_ids]
            invalid_evidence = [item for item in risk.evidence_ids if item not in valid_evidence_ids]
            invalid_estimates = [item for item in risk.estimate_ids if item not in valid_estimate_ids]
            if invalid_hypotheses:
                local_errors.append("invalid hypothesis_ids")
            if invalid_evidence:
                local_errors.append("invalid evidence_ids")
            if invalid_estimates:
                local_errors.append("invalid estimate_ids")
            if not risk.fundamental_impact.strip() or not risk.price_impact.strip() or not risk.verification_view.strip():
                local_errors.append("impact analysis is incomplete")
            if not risk.evidence_ids and not risk.estimate_ids:
                local_errors.append("risk has no evidence or estimate linkage")

            if local_errors:
                errors.append(f"{risk.risk_id}: {', '.join(local_errors)}")
                context.save_review(
                    self.build_review(
                        risk.risk_id,
                        ReviewDecision.REVISION_REQUIRED,
                        "리스크 영향 분석 보완이 필요해요.",
                        logical_issues=local_errors,
                    )
                )
                continue

            risk.approved = True
            context.save_risk_assessment(risk)
            context.save_review(
                self.build_review(
                    risk.risk_id,
                    ReviewDecision.APPROVED,
                    "리스크, 영향도, 펀더멘탈/주가 검증 연결이 확인됐어요.",
                )
            )

        if errors:
            self.audit(context, "review", target=task.task_id, decision="revision_required", reason="; ".join(errors))
            return AgentResult(status="revision_required", summary="Risk assessment review failed.", confidence=0.4)
        self.audit(context, "review", target=task.task_id, decision="approved")
        return AgentResult(status="completed", summary=f"{len(risks)} risk assessments approved.", confidence=0.86)
