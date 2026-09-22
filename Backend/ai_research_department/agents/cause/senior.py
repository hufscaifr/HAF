from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class CauseSeniorAgent(SeniorAgent):
    """Review causal hypotheses and data requirements."""

    def __init__(self) -> None:
        super().__init__("SeniorCauseAnalyst", "Review causal logic")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        approved: list[str] = []
        revision_required: list[str] = []
        for hypothesis in context.hypotheses():
            if hypothesis.required_data and hypothesis.evidence_ids:
                hypothesis.approved = True
                context.save_hypothesis(hypothesis)
                approved.append(hypothesis.hypothesis_id)
                review = self.build_review(hypothesis.hypothesis_id, ReviewDecision.APPROVED, "인과 가설과 필요 데이터가 명확해요.")
            else:
                revision_required.append(hypothesis.hypothesis_id)
                review = self.build_review(
                    hypothesis.hypothesis_id,
                    ReviewDecision.REVISION_REQUIRED,
                    "필요 데이터 또는 근거 연결이 부족해요.",
                    missing_evidence=["supporting evidence"],
                )
            context.save_review(review)
        status = "revision_required" if revision_required else "completed"
        self.audit(context, "review", target=task.task_id, decision=status)
        return AgentResult(
            status=status,
            summary=f"{len(approved)} approved. {len(revision_required)} require revision.",
            created_entities=approved,
            confidence=0.8,
        )
