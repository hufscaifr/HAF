from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class ReportSeniorAgent(SeniorAgent):
    """Review department-level section drafts before final merging."""

    def __init__(self) -> None:
        super().__init__("SeniorSectionEditor", "Review section drafts")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        drafts = context.section_drafts()
        valid_ids = (
            {item.evidence_id for item in context.evidence()}
            | {item.estimate_id for item in context.estimates()}
            | {item.hypothesis_id for item in context.hypotheses()}
            | {item.chart_id for item in context.charts()}
            | {item.table_id for item in context.tables()}
        )
        errors: list[str] = []
        for draft in drafts:
            referenced_ids = draft.citation_ids + draft.chart_ids + draft.table_ids
            invalid = [item for item in referenced_ids if item not in valid_ids]
            if invalid:
                draft.citation_ids = [item for item in draft.citation_ids if item in valid_ids]
                draft.chart_ids = [item for item in draft.chart_ids if item in valid_ids]
                draft.table_ids = [item for item in draft.table_ids if item in valid_ids]
                self.audit(context, "sanitize", target=draft.draft_id, reason=f"Removed invalid ids: {', '.join(invalid)}")
            if not draft.summary.strip():
                errors.append(f"{draft.draft_id} has empty summary")
                continue
            draft.approved = True
            context.save_section_draft(draft)
            context.save_review(
                self.build_review(
                    draft.draft_id,
                    ReviewDecision.APPROVED,
                    "섹션 draft lineage가 확인됐어요.",
                )
            )

        if errors:
            self.audit(context, "review", target=task.task_id, decision="revision_required", reason="; ".join(errors))
            return AgentResult(status="revision_required", summary="Section draft lineage errors found.", confidence=0.4)
        self.audit(context, "review", target=task.task_id, decision="approved")
        return AgentResult(status="completed", summary=f"{len(drafts)} section drafts approved.", confidence=0.86)
