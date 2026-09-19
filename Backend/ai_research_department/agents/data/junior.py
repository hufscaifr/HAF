from __future__ import annotations

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.datasource.base import DataSourceConnector
from ai_research_department.datasource.mock import MockDataSourceConnector
from ai_research_department.models import Evidence, ResearchTask
from ai_research_department.services.visualization_service import VisualizationService
from ai_research_department.workspace.research_context import ResearchContext


class DataJuniorAgent(JuniorAgent):
    """Collect evidence for explicit data requests."""

    def __init__(self, connector: DataSourceConnector | None = None) -> None:
        super().__init__("DataJuniorAgent", "Collect requested source evidence")
        self.connector = connector or MockDataSourceConnector()
        self.visualization_service = VisualizationService()

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        created: list[str] = []
        for request in context.data_requests():
            if request.fulfilled:
                continue
            results = await self.connector.search(request.metric)
            for result in results[:1]:
                raw = await self.connector.fetch(result["source_id"])
                extracted = await self.connector.extract(raw)
                for item in extracted:
                    evidence = Evidence(
                        company=context.project.request.company,
                        fact=item["fact"],
                        metric=item.get("metric"),
                        value=item.get("value"),
                        unit=item.get("unit"),
                        period=item.get("period"),
                        source_name=item["source_name"],
                        source_url=item.get("source_url"),
                        source_type=item["source_type"],
                        confidence=0.82,
                        verified=True,
                        raw_text=item["fact"],
                    )
                    context.save_evidence(evidence)
                    request.evidence_ids.append(evidence.evidence_id)
                    created.append(evidence.evidence_id)
            request.fulfilled = bool(request.evidence_ids)
            context.save_data_request(request)
        charts, tables = self.visualization_service.build_from_evidence(context.evidence())
        artifact_ids: list[str] = []
        for chart in charts:
            context.save_chart(chart)
            artifact_ids.append(chart.chart_id)
        for table in tables:
            context.save_table(table)
            artifact_ids.append(table.table_id)
        self.audit(
            context,
            "execute",
            target=task.task_id,
            reason=f"{len(created)} evidence collected, {len(artifact_ids)} visualization artifacts created",
        )
        return AgentResult(
            status="completed",
            summary=f"{len(created)} evidence collected. {len(artifact_ids)} visualization artifacts created.",
            created_entities=[*created, *artifact_ids],
            confidence=0.82,
        )
