from __future__ import annotations

import asyncio
import json
import os

from pydantic import BaseModel, Field

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.config import load_backend_env
from ai_research_department.llm.openai_provider import OpenAIProvider
from ai_research_department.models import ReportSectionDraft, ResearchTask
from ai_research_department.repositories.sqlite_repository import dump_model
from ai_research_department.services.prompt_loader import PromptLoader
from ai_research_department.utils.number_format import format_korean_number
from ai_research_department.workspace.research_context import ResearchContext


class SectionDraftOutput(BaseModel):
    title: str
    summary: str
    bullets: list[str] = Field(default_factory=list)
    logic_chain: list[dict] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    chart_ids: list[str] = Field(default_factory=list)
    table_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.75


SECTION_SPECS = [
    ("Issue Department", "key_issues", "Key Issues"),
    ("Data Department", "data_snapshot", "Data Snapshot"),
    ("Fundamental Department", "fundamental_view", "Fundamental View"),
    ("Estimate Department", "earnings_outlook", "Earnings Outlook"),
    ("Valuation Department", "valuation", "Valuation"),
    ("Risk Department", "risks", "Risks"),
    ("Conclusion Desk", "conclusion", "Conclusion"),
]


class ReportJuniorAgent(JuniorAgent):
    """Create department-level report section drafts in parallel."""

    def __init__(self) -> None:
        super().__init__("ReportSectionDraftingDesk", "Draft department-level report sections")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        load_backend_env()
        if not [item for item in context.estimates() if item.approved]:
            return AgentResult(status="revision_required", summary="Approved estimate is missing.", confidence=0.3)

        drafts = await asyncio.gather(
            *(self._build_section_draft(context, *spec) for spec in SECTION_SPECS)
        )
        for draft in drafts:
            context.save_section_draft(draft)

        self.audit(context, "execute", target=task.task_id, reason=f"{len(drafts)} section drafts created in parallel")
        return AgentResult(
            status="completed",
            summary=f"{len(drafts)} section drafts created in parallel.",
            created_entities=[draft.draft_id for draft in drafts],
            confidence=0.84,
        )

    async def _build_section_draft(
        self,
        context: ResearchContext,
        department: str,
        section_key: str,
        title: str,
    ) -> ReportSectionDraft:
        if context.project.request.data_mode == "real" and os.getenv("OPENAI_API_KEY", "").strip():
            try:
                provider = OpenAIProvider()
                output = await provider.generate_structured(
                    system_prompt=self._system_prompt(department, title),
                    user_prompt=json.dumps(
                        self._writer_input(context, section_key),
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    output_schema=SectionDraftOutput,
                )
                return ReportSectionDraft(
                    department=department,
                    section_key=section_key,
                    title=output.title,
                    summary=output.summary,
                    bullets=output.bullets,
                    logic_chain=output.logic_chain,
                    citation_ids=output.citation_ids,
                    chart_ids=output.chart_ids,
                    table_ids=output.table_ids,
                    confidence=output.confidence,
                    writer="openai",
                    model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
                )
            except Exception as exc:
                self.audit(context, "section_draft_fallback", target=section_key, reason=str(exc))

        return self._fallback_draft(context, department, section_key, title)

    def _system_prompt(self, department: str, title: str) -> str:
        loader = PromptLoader()
        contract = loader.load("common/research_reasoning_contract.md")
        report_prompt = loader.load("report/junior.md")
        return "\n\n".join(
            [
                contract,
                report_prompt,
                f"You are currently acting as the {department}.",
                f"Write only the {title} section draft as structured JSON in Korean.",
                "Do not invent target prices, ratings, consensus, management guidance, or unsupported facts.",
                "Use citation_ids only from supplied evidence_ids, estimate_ids, hypothesis_ids, chart_ids, and table_ids.",
                "Populate logic_chain whenever possible with claim, evidence_ids, interpretation, financial_implication, counterargument, and confidence.",
            ]
        )

    def _writer_input(self, context: ResearchContext, section_key: str) -> dict:
        return {
            "section_key": section_key,
            "request": dump_model(context.project.request),
            "issues": [dump_model(item) for item in context.issues() if item.approved],
            "hypotheses": [dump_model(item) for item in context.hypotheses() if item.approved],
            "evidence": [dump_model(item) for item in context.evidence() if item.verified],
            "assumptions": [dump_model(item) for item in context.assumptions()],
            "forecasts": [dump_model(item) for item in context.forecasts() if item.approved],
            "estimates": [dump_model(item) for item in context.estimates() if item.approved],
            "risk_assessments": [dump_model(item) for item in context.risk_assessments() if item.approved],
            "charts": [dump_model(item) for item in context.charts()],
            "tables": [dump_model(item) for item in context.tables()],
        }

    def _fallback_draft(
        self,
        context: ResearchContext,
        department: str,
        section_key: str,
        title: str,
    ) -> ReportSectionDraft:
        estimate = [item for item in context.estimates() if item.approved][-1]
        evidence_ids = list(dict.fromkeys(estimate.evidence_ids))
        chart_ids = [chart.chart_id for chart in context.charts()]
        table_ids = [table.table_id for table in context.tables()]
        issues = ", ".join(issue.event for issue in context.issues() if issue.approved)
        revenue = format_korean_number(estimate.revenue, "KRW")
        operating_profit = format_korean_number(estimate.operating_profit, "KRW")
        eps = format_korean_number(estimate.eps, "KRW/share")
        risks = [item for item in context.risk_assessments() if item.approved]
        risk_summary = "; ".join(f"{item.title}: {item.severity}" for item in risks[:3])
        summary_by_key = {
            "key_issues": f"핵심 이슈는 {issues}예요.",
            "data_snapshot": "Data Department가 수집한 evidence, chart, table을 기반으로 분석 데이터를 정리했어요.",
            "fundamental_view": "수집된 fundamental assumption과 forecast를 바탕으로 사업 체력을 점검했어요.",
            "earnings_outlook": f"{estimate.period} 매출 {revenue}, 영업이익 {operating_profit}, EPS {eps}예요.",
            "valuation": "PER, PBR, ROE, 영업이익률 등 valuation/profitability 지표를 함께 확인해야 해요.",
            "risks": risk_summary or "공시 시차, 가격 변동성, 추정치 부재가 주요 리스크예요.",
            "conclusion": "현재 리포트는 검증된 evidence와 estimate snapshot 기반의 리서치 초안이에요.",
        }
        return ReportSectionDraft(
            department=department,
            section_key=section_key,
            title=title,
            summary=summary_by_key.get(section_key, title),
            bullets=[],
            logic_chain=[
                {
                    "claim": summary_by_key.get(section_key, title),
                    "evidence_ids": evidence_ids,
                    "interpretation": "Deterministic fallback section based on approved workspace objects.",
                    "financial_implication": "Refer to approved estimate snapshot.",
                    "counterargument": "Forward-looking evidence is limited when consensus or guidance is unavailable.",
                    "confidence": 0.76,
                }
            ],
            citation_ids=evidence_ids,
            chart_ids=chart_ids,
            table_ids=table_ids,
            confidence=0.76,
            writer="deterministic",
        )
