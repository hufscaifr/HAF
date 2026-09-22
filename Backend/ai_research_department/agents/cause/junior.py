from __future__ import annotations

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.models import DataRequest, Hypothesis, ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class CauseJuniorAgent(JuniorAgent):
    """Generate causal hypotheses from approved issues."""

    def __init__(self) -> None:
        super().__init__("CauseJuniorAgent", "Create causal hypotheses")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        created: list[str] = []
        requests: list[str] = []
        requested_metrics: set[str] = set()
        for issue in [item for item in context.issues() if item.approved]:
            metric = issue.potential_impacts[0] if issue.potential_impacts else "revenue"
            hypothesis = Hypothesis(
                issue_id=issue.issue_id,
                cause=issue.event,
                affected_metric=metric,
                direction="positive",
                time_horizon="12m",
                confidence=0.76,
                required_data=[metric, "revenue sensitivity"],
                evidence_ids=issue.evidence_ids,
            )
            context.save_hypothesis(hypothesis)
            created.append(hypothesis.hypothesis_id)
            metrics = issue.potential_impacts if context.project.request.data_mode == "real" else [metric]
            for requested_metric in metrics:
                if requested_metric in requested_metrics:
                    continue
                requested_metrics.add(requested_metric)
                data_request = DataRequest(
                    requested_by="cause_analysis",
                    metric=requested_metric,
                    period="2027E",
                    reason=f"{issue.event}이 {requested_metric}에 미치는 영향을 검증",
                    priority="HIGH",
                )
                context.save_data_request(data_request)
                requests.append(data_request.request_id)
        self.audit(context, "execute", target=task.task_id, reason=f"{len(created)} hypotheses created")
        return AgentResult(
            status="completed",
            summary=f"{len(created)} hypotheses created.",
            created_entities=created,
            requested_data=requests,
            confidence=0.76,
        )
