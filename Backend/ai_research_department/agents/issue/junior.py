from __future__ import annotations

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.models import Evidence, Issue, ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class IssueJuniorAgent(JuniorAgent):
    """Discover initial issue candidates."""

    def __init__(self) -> None:
        super().__init__("IssueJuniorAgent", "Discover valuation-relevant company issues")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        request = context.project.request
        if request.data_mode == "real":
            return await self._execute_real(task, context)
        seed_evidence = Evidence(
            company=request.company,
            fact=f"{request.company}의 신규 반도체 공장 가동과 DRAM 가격 상승이 동시에 관찰됐다.",
            metric=None,
            source_name="Mock News Wire",
            source_url="mock://news/example-electronics-fab",
            source_type="news",
            confidence=0.82,
            verified=True,
            raw_text="신규 반도체 공장 가동, DRAM 가격 상승, 출하량 증가",
        )
        context.save_evidence(seed_evidence)
        issues = [
            Issue(
                company=request.company,
                issue_type="capacity_expansion",
                event="신규 반도체 공장 가동",
                event_date=request.as_of_date,
                importance=0.88,
                potential_impacts=["production_volume", "revenue", "operating_margin"],
                evidence_ids=[seed_evidence.evidence_id],
            ),
            Issue(
                company=request.company,
                issue_type="price_increase",
                event="DRAM 가격 상승",
                event_date=request.as_of_date,
                importance=0.84,
                potential_impacts=["asp", "revenue", "gross_margin"],
                evidence_ids=[seed_evidence.evidence_id],
            ),
            Issue(
                company=request.company,
                issue_type="demand_growth",
                event="AI 서버향 출하량 증가",
                event_date=request.as_of_date,
                importance=0.79,
                potential_impacts=["shipment_volume", "revenue"],
                evidence_ids=[seed_evidence.evidence_id],
            ),
        ]
        for issue in issues:
            context.save_issue(issue)
        self.audit(context, "execute", target=task.task_id, reason="3 issues discovered")
        return AgentResult(
            status="completed",
            summary="3 issues discovered.",
            created_entities=[issue.issue_id for issue in issues],
            confidence=0.82,
        )

    async def _execute_real(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        request = context.project.request
        seed_evidence = Evidence(
            company=request.company,
            fact=f"{request.company}({request.ticker})에 대해 시장 데이터와 공시 재무 데이터를 수집해 분석한다.",
            metric=None,
            source_name="Research Request",
            source_url=None,
            source_type="manual_input",
            confidence=0.7,
            verified=True,
            raw_text=request.objective,
        )
        context.save_evidence(seed_evidence)
        issues = [
            Issue(
                company=request.company,
                issue_type="market_data_review",
                event="최근 주가 및 거래량 변화 점검",
                event_date=request.as_of_date,
                importance=0.78,
                potential_impacts=["latest_close", "latest_volume"],
                evidence_ids=[seed_evidence.evidence_id],
            ),
            Issue(
                company=request.company,
                issue_type="fundamental_review",
                event="최근 공시 기반 재무지표 및 밸류에이션 점검",
                event_date=request.as_of_date,
                importance=0.84,
                potential_impacts=["revenue", "operating_income", "eps", "per", "pbr"],
                evidence_ids=[seed_evidence.evidence_id],
            ),
            Issue(
                company=request.company,
                issue_type="profitability_review",
                event="수익성 및 재무 안정성 점검",
                event_date=request.as_of_date,
                importance=0.8,
                potential_impacts=["roe", "operating_margin", "debt_ratio"],
                evidence_ids=[seed_evidence.evidence_id],
            ),
        ]
        for issue in issues:
            context.save_issue(issue)
        self.audit(context, "execute", target=task.task_id, reason="3 real-data issues discovered")
        return AgentResult(
            status="completed",
            summary="3 real-data issues discovered.",
            created_entities=[issue.issue_id for issue in issues],
            confidence=0.78,
        )
