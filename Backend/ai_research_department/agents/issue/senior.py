from __future__ import annotations

from ai_research_department.agents.base import AgentResult, SeniorAgent
from ai_research_department.enums import ReviewDecision
from ai_research_department.models import ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class IssueSeniorAgent(SeniorAgent):
    """Review issue candidates for importance and source support."""

    def __init__(self) -> None:
        super().__init__("SeniorIssueAnalyst", "Review issue quality")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        approved = []
        rejected = []
        for issue in context.issues():
            if issue.importance >= 0.75 and issue.evidence_ids:
                issue.approved = True
                context.save_issue(issue)
                approved.append(issue.issue_id)
                decision = ReviewDecision.APPROVED
                feedback = "중요도와 근거가 충분해요."
            else:
                rejected.append(issue.issue_id)
                decision = ReviewDecision.REJECTED
                feedback = "중요도 또는 근거가 부족해요."
            review = self.build_review(issue.issue_id, decision, feedback)
            context.save_review(review)
        self.audit(context, "review", target=task.task_id, decision="approved", reason=f"{len(approved)} approved")
        return AgentResult(
            status="completed",
            summary=f"{len(approved)} approved. {len(rejected)} rejected.",
            created_entities=approved,
            confidence=0.85,
        )
