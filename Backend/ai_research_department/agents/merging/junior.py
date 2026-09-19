from __future__ import annotations

import json
import os

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.config import load_backend_env
from ai_research_department.llm.openai_provider import OpenAIProvider
from ai_research_department.models import (
    FrontendReportJson,
    Report,
    ReportClaim,
    ReportSection,
    ResearchTask,
)
from ai_research_department.repositories.sqlite_repository import dump_model
from ai_research_department.utils.number_format import format_korean_number
from ai_research_department.workspace.research_context import ResearchContext


class MergingJuniorAgent(JuniorAgent):
    """Merge approved section drafts into one final frontend-ready JSON report."""

    def __init__(self) -> None:
        super().__init__("MergingJuniorEditor", "Merge section drafts into final JSON report")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        load_backend_env()
        drafts = [item for item in context.section_drafts() if item.approved]
        if not drafts:
            return AgentResult(status="revision_required", summary="Approved section drafts are missing.", confidence=0.3)

        writer = "deterministic"
        model = None
        try:
            if context.project.request.data_mode == "real" and os.getenv("OPENAI_API_KEY", "").strip():
                report_json = await self._merge_with_openai(context)
                writer = "openai"
                model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
            else:
                report_json = self._merge_fallback(context)
        except Exception as exc:
            self.audit(context, "merge_fallback", target=task.task_id, reason=str(exc))
            report_json = self._merge_fallback(context)

        claims = self._build_claims(report_json, context)
        sections = self._build_sections(report_json, claims)
        report = Report(
            title=report_json.title,
            sections=sections,
            claims=claims,
            json_payload=dump_model(report_json),
            writer=f"parallel_sections+{writer}_merge",
            model=model,
        )
        context.save_report(report)
        self.audit(context, "execute", target=task.task_id, reason=f"Final report merged by {writer}")
        return AgentResult(
            status="completed",
            summary=f"Final JSON report merged by {writer}.",
            created_entities=[report.report_id],
            confidence=0.88 if writer == "openai" else 0.78,
        )

    async def _merge_with_openai(self, context: ResearchContext) -> FrontendReportJson:
        provider = OpenAIProvider()
        prompt = {
            "instructions": {
                "language": "ko",
                "task": "Merge approved section drafts into one long brokerage-style frontend JSON report.",
                "rules": [
                    "Preserve numeric values from evidence and estimates exactly.",
                    "Do not invent target prices, ratings, consensus, or unsupported facts.",
                    "Use supplied chart_ids and table_ids.",
                    "Use only supplied citation_ids.",
                    "Use Korean large-number display units such as 조, 억, 만 in narrative text, while preserving raw numeric values in financial_snapshot.",
                    "Make the report longer and more institutional than the section drafts, while staying evidence-bound.",
                ],
            },
            "request": dump_model(context.project.request),
            "section_drafts": [dump_model(item) for item in context.section_drafts() if item.approved],
            "evidence": [dump_model(item) for item in context.evidence() if item.verified],
            "estimates": [dump_model(item) for item in context.estimates() if item.approved],
            "risk_assessments": [dump_model(item) for item in context.risk_assessments() if item.approved],
            "charts": [dump_model(item) for item in context.charts()],
            "tables": [dump_model(item) for item in context.tables()],
        }
        return await provider.generate_structured(
            system_prompt=(
                "You are the merging editor of a Korean securities research center. "
                "Create one final frontend-ready JSON report from approved section drafts. "
                "The output must be coherent, longer than the drafts, and strictly evidence-bound."
            ),
            user_prompt=json.dumps(prompt, ensure_ascii=False, indent=2, default=str),
            output_schema=FrontendReportJson,
        )

    def _merge_fallback(self, context: ResearchContext) -> FrontendReportJson:
        request = context.project.request
        estimate = [item for item in context.estimates() if item.approved][-1]
        drafts = [item for item in context.section_drafts() if item.approved]
        chart_ids = [chart.chart_id for chart in context.charts()]
        table_ids = [table.table_id for table in context.tables()]
        verified_evidence = [item for item in context.evidence() if item.verified]
        evidence_ids = list(dict.fromkeys([eid for draft in drafts for eid in draft.citation_ids] + [item.evidence_id for item in verified_evidence]))
        lineage_ids = evidence_ids + [estimate.estimate_id]
        draft_by_key = {draft.section_key: draft for draft in drafts}
        risk_assessments = [item for item in context.risk_assessments() if item.approved]
        metrics = {item.metric: item for item in verified_evidence if item.metric}
        close = self._metric_text(metrics, "latest_close", decimals=1)
        volume = self._metric_text(metrics, "latest_volume", decimals=1)
        revenue = self._metric_text(metrics, "revenue", decimals=1)
        operating_income = self._metric_text(metrics, "operating_income", decimals=1)
        eps = self._metric_text(metrics, "eps", decimals=1)
        per = self._metric_text(metrics, "per", decimals=2)
        pbr = self._metric_text(metrics, "pbr", decimals=2)
        roe = self._metric_text(metrics, "roe", decimals=2)
        operating_margin = self._metric_text(metrics, "operating_margin", decimals=2)
        debt_ratio = self._metric_text(metrics, "debt_ratio", decimals=2)
        estimate_revenue = format_korean_number(estimate.revenue, "KRW")
        estimate_operating_profit = format_korean_number(estimate.operating_profit, "KRW")
        estimate_eps = format_korean_number(estimate.eps, "KRW/share")
        data_date = metrics.get("latest_close").period if metrics.get("latest_close") else str(request.as_of_date)
        summary = [
            f"{request.company} 리포트는 단일 기업 입력 이후 KRX listing, 시장 가격, DART 재무지표를 연결해 작성한 증권사형 earnings preview예요. 기준 가격 데이터는 {data_date} 종가 {close}, 거래량 {volume}이고, 재무 데이터는 매출 {revenue}, 영업이익 {operating_income}, EPS {eps}을 중심으로 구성했어요.",
            f"현재 valuation snapshot은 PER {per}, PBR {pbr}, ROE {roe}, 영업이익률 {operating_margin}, 부채비율 {debt_ratio}를 함께 봅니다. 목표주가나 투자의견은 외부 consensus 또는 analyst 가정이 없으면 만들지 않도록 제한했어요.",
            f"실적 추정은 수집된 공시 기반 데이터를 2026 preview snapshot으로 이월한 보수적 형태입니다. 매출 추정치는 {estimate_revenue}, 영업이익 추정치는 {estimate_operating_profit}, EPS는 {estimate_eps}이며 revision은 비교 기준 부재로 계산하지 않았어요.",
            "핵심 체크포인트는 가격 모멘텀, 이익 규모, 수익성 지표, 재무 안정성, 그리고 공시 데이터 시차입니다. 이 구조는 프론트에서 표와 차트를 함께 렌더링할 수 있도록 chart_ids와 table_ids를 포함합니다.",
            "본 결과물은 긴 리포트 초안 생성을 위한 backend JSON이며, 모든 claim은 evidence, estimate, hypothesis 중 하나 이상에 연결되도록 검증 단계에서 확인됩니다.",
        ]
        earnings_bullets = [
            f"매출 전망: {estimate.period} 매출은 {estimate_revenue}으로 저장됐습니다. 현재 workflow에서는 별도 consensus 입력이 없으므로 공시 기반 revenue evidence를 직접 근거로 사용합니다.",
            f"영업이익 전망: {estimate.period} 영업이익은 {estimate_operating_profit}입니다. 영업이익률 evidence는 {operating_margin}로, 매출 규모 대비 이익 체력 점검의 중심 지표입니다.",
            f"EPS 전망: EPS는 {estimate_eps}입니다. previous EPS 또는 consensus가 없으면 revision 계산을 강제로 만들지 않고 null로 둡니다.",
            "해석: 현 단계의 preview는 방향성보다 데이터 정합성을 우선합니다. 추후 consensus API 또는 내부 모델 assumption이 붙으면 revision, surprise, sensitivity table을 확장할 수 있습니다.",
        ]
        valuation_bullets = [
            f"가격 기준: {data_date} 종가 {close}를 사용했습니다. price chart artifact가 있으면 프론트에서 가격/거래량 흐름을 함께 보여줄 수 있습니다.",
            f"멀티플: PER {per}, PBR {pbr}를 함께 확인합니다. 단일 PER만으로 결론을 내리지 않고 ROE와 마진을 같이 보는 형태로 구성했습니다.",
            f"수익성: ROE {roe}, 영업이익률 {operating_margin}입니다. ROE와 margin이 유지되면 높은 PBR의 설명력이 생기지만, 둔화 시 multiple 부담이 커집니다.",
            f"재무 안정성: 부채비율 {debt_ratio}입니다. 리포트에서는 안정성 지표를 downside risk 완충 요인으로 분리해 볼 수 있게 했습니다.",
            "제한 사항: 목표주가, 적정 PER, upside/downside는 analyst assumption 또는 peer multiple dataset이 없으면 산출하지 않습니다.",
        ]
        risk_items = self._risk_items(risk_assessments, lineage_ids, close, volume)
        return FrontendReportJson(
            title=f"{request.company} Earnings Preview",
            company=request.company,
            ticker=request.ticker,
            market=request.market or "",
            as_of_date=str(request.as_of_date),
            report_type=request.research_type,
            investment_summary=summary,
            key_issues=[
                draft_by_key.get("key_issues", drafts[0]).summary,
                f"주가/거래량: {data_date} 종가 {close}, 거래량 {volume} 기준으로 price action을 확인합니다.",
                f"실적/수익성: 매출 {revenue}, 영업이익 {operating_income}, 영업이익률 {operating_margin}를 중심으로 earnings quality를 점검합니다.",
                f"밸류에이션/재무안정성: PER {per}, PBR {pbr}, ROE {roe}, 부채비율 {debt_ratio}를 동시에 봅니다.",
            ],
            financial_snapshot={
                "period": estimate.period,
                "revenue": estimate.revenue,
                "operating_profit": estimate.operating_profit,
                "eps": estimate.eps,
                "eps_revision_pct": estimate.eps_revision_pct,
                "latest_close": metrics.get("latest_close").value if metrics.get("latest_close") else None,
                "latest_volume": metrics.get("latest_volume").value if metrics.get("latest_volume") else None,
                "per": metrics.get("per").value if metrics.get("per") else None,
                "pbr": metrics.get("pbr").value if metrics.get("pbr") else None,
                "roe": metrics.get("roe").value if metrics.get("roe") else None,
                "operating_margin": metrics.get("operating_margin").value if metrics.get("operating_margin") else None,
                "debt_ratio": metrics.get("debt_ratio").value if metrics.get("debt_ratio") else None,
            },
            investment_points=[
                {
                    "title": "실적 preview의 기준선",
                    "thesis": f"{estimate.period} preview는 매출 {estimate_revenue}, 영업이익 {estimate_operating_profit}, EPS {estimate_eps}를 기준선으로 둡니다. 이 수치는 현재 승인된 estimate와 공시 기반 evidence에 연결됩니다.",
                    "supporting_metrics": earnings_bullets,
                    "citation_ids": lineage_ids,
                },
                {
                    "title": "valuation check",
                    "thesis": f"PER {per}, PBR {pbr}, ROE {roe}를 함께 보면 가격 부담과 자기자본 수익성을 동시에 확인할 수 있습니다. 아직 peer multiple이나 목표 multiple은 연결하지 않았기 때문에 결론은 snapshot 해석에 머뭅니다.",
                    "supporting_metrics": valuation_bullets,
                    "citation_ids": lineage_ids,
                },
                {
                    "title": "데이터 기반 확장성",
                    "thesis": "보고서 JSON은 chart_ids, table_ids, evidence lineage를 함께 반환합니다. 프론트에서는 같은 payload로 리포트 본문, 재무 table, 가격 chart를 동시에 렌더링할 수 있습니다.",
                    "supporting_metrics": [
                        f"생성된 chart artifact 수: {len(chart_ids)}",
                        f"생성된 table artifact 수: {len(table_ids)}",
                        "부서별 section draft를 먼저 만들고 merge하는 구조라, 느린 섹션은 fallback 처리하면서도 최종 보고서를 완성할 수 있습니다.",
                    ],
                    "citation_ids": lineage_ids,
                }
            ],
            earnings_outlook=self._section_payload(draft_by_key.get("earnings_outlook"), "earnings_outlook", "Earnings Outlook", chart_ids, table_ids, lineage_ids, bullets=earnings_bullets),
            valuation=self._section_payload(draft_by_key.get("valuation"), "valuation", "Valuation", chart_ids, table_ids, lineage_ids, bullets=valuation_bullets),
            risks=[
                {
                    "title": title,
                    "description": description,
                    "severity": severity,
                    "citation_ids": citations,
                }
                for title, description, severity, citations in risk_items
            ],
            conclusion=self._section_payload(
                draft_by_key.get("conclusion"),
                "conclusion",
                "Conclusion",
                chart_ids,
                table_ids,
                lineage_ids,
                bullets=[
                    "현재 단계에서는 Buy/Sell/Hold 또는 목표주가를 만들지 않습니다. 근거 데이터가 붙지 않은 결론을 방지하기 위한 설계입니다.",
                    "다음 고도화는 consensus API, peer valuation DB, segment-level assumption, sensitivity table 순서가 적합합니다.",
                    "프론트 연동 시 json_payload를 본문 렌더링에 쓰고, charts/tables 배열을 별도 visualization component에 매핑하면 됩니다.",
                ],
            ),
            evidence_notes=[
                "각 부서 section draft를 Merging Department가 취합한 JSON 리포트예요.",
                "모든 숫자는 evidence 또는 estimate snapshot에서 가져왔어요.",
            ],
            chart_ids=chart_ids,
            table_ids=table_ids,
        )

    def _risk_items(
        self,
        risk_assessments: list,
        lineage_ids: list[str],
        close: str,
        volume: str,
    ) -> list[tuple[str, str, str, list[str]]]:
        if risk_assessments:
            return [
                (
                    risk.title,
                    (
                        f"{risk.description} Fundamental 검증: {risk.fundamental_impact} "
                        f"주가 검증: {risk.price_impact} 검증 의견: {risk.verification_view}"
                    ),
                    risk.severity,
                    list(dict.fromkeys(risk.evidence_ids + risk.estimate_ids + lineage_ids)),
                )
                for risk in risk_assessments
            ]
        return [
            (
                "공시 데이터 시차",
                "DART 재무지표는 공시 기준 시점과 리포트 작성 시점 사이의 시차가 존재합니다. 실적 발표 이후 revenue, operating income, EPS evidence를 다시 refresh해야 합니다.",
                "medium",
                lineage_ids,
            ),
            (
                "시장 가격 변동성",
                f"최근 종가 {close}와 거래량 {volume} 기준의 snapshot이므로, 가격 급변 구간에서는 valuation multiple이 빠르게 바뀔 수 있습니다.",
                "medium",
                lineage_ids,
            ),
            (
                "추정치 입력 부재",
                "외부 consensus 또는 analyst forecast가 없으면 revision, surprise, 목표주가를 계산하지 않습니다. 이는 과잉 추정을 막는 장점이 있지만 리포트 결론의 공격성은 낮춥니다.",
                "low",
                lineage_ids,
            ),
        ]

    def _metric_text(self, metrics: dict, metric: str, decimals: int = 2) -> str:
        evidence = metrics.get(metric)
        if evidence is None or evidence.value is None:
            return "N/A"
        if isinstance(evidence.value, (int, float)):
            return format_korean_number(evidence.value, evidence.unit, decimals=decimals)
        else:
            value = str(evidence.value)
        return f"{value} {evidence.unit or ''}".strip()

    def _section_payload(
        self,
        draft,
        section_key: str,
        title: str,
        chart_ids: list[str],
        table_ids: list[str],
        evidence_ids: list[str],
        bullets: list[str] | None = None,
    ) -> dict:
        if draft is None:
            return {
                "section_key": section_key,
                "title": title,
                "summary": "",
                "bullets": bullets or [],
                "citation_ids": evidence_ids,
                "chart_ids": chart_ids,
                "table_ids": table_ids,
            }
        return {
            "section_key": draft.section_key,
            "title": draft.title,
            "summary": draft.summary,
            "bullets": draft.bullets or bullets or [],
            "citation_ids": draft.citation_ids or evidence_ids,
            "chart_ids": draft.chart_ids or chart_ids,
            "table_ids": draft.table_ids or table_ids,
        }

    def _build_claims(self, report_json: FrontendReportJson, context: ResearchContext) -> list[ReportClaim]:
        valid_evidence_ids = {item.evidence_id for item in context.evidence()}
        valid_estimate_ids = {item.estimate_id for item in context.estimates()}
        valid_hypothesis_ids = {item.hypothesis_id for item in context.hypotheses()}
        default_evidence_ids = [item.evidence_id for item in context.evidence() if item.verified]
        default_estimate_ids = [item.estimate_id for item in context.estimates() if item.approved]
        claims: list[ReportClaim] = []
        sentences: list[tuple[str, list[str]]] = []
        sentences.extend((item, []) for item in report_json.investment_summary)
        for point in report_json.investment_points:
            sentences.append((point.thesis, point.citation_ids))
        sentences.append((report_json.earnings_outlook.summary, report_json.earnings_outlook.citation_ids))
        sentences.append((report_json.valuation.summary, report_json.valuation.citation_ids))
        for risk in report_json.risks:
            sentences.append((risk.description, risk.citation_ids))
        sentences.append((report_json.conclusion.summary, report_json.conclusion.citation_ids))
        for sentence, citation_ids in sentences:
            evidence_ids = [item for item in citation_ids if item in valid_evidence_ids]
            estimate_ids = [item for item in citation_ids if item in valid_estimate_ids]
            hypothesis_ids = [item for item in citation_ids if item in valid_hypothesis_ids]
            if not evidence_ids and not estimate_ids and not hypothesis_ids:
                evidence_ids = default_evidence_ids
                estimate_ids = default_estimate_ids
            claims.append(ReportClaim(sentence=sentence, evidence_ids=evidence_ids, estimate_ids=estimate_ids, hypothesis_ids=hypothesis_ids))
        return claims

    def _build_sections(self, report_json: FrontendReportJson, claims: list[ReportClaim]) -> list[ReportSection]:
        claim_ids = [claim.claim_id for claim in claims]
        return [
            ReportSection(title="Investment Summary", body="\n".join(f"- {item}" for item in report_json.investment_summary), claim_ids=claim_ids),
            ReportSection(title="Investment Points", body="\n".join(f"- {point.title}: {point.thesis}" for point in report_json.investment_points), claim_ids=claim_ids),
            ReportSection(title=report_json.earnings_outlook.title, body=self._section_body(report_json.earnings_outlook.summary, report_json.earnings_outlook.bullets), claim_ids=claim_ids),
            ReportSection(title=report_json.valuation.title, body=self._section_body(report_json.valuation.summary, report_json.valuation.bullets), claim_ids=claim_ids),
            ReportSection(title="Risks", body="\n".join(f"- {risk.title} ({risk.severity}): {risk.description}" for risk in report_json.risks), claim_ids=claim_ids),
            ReportSection(title=report_json.conclusion.title, body=self._section_body(report_json.conclusion.summary, report_json.conclusion.bullets), claim_ids=claim_ids),
        ]

    def _section_body(self, summary: str, bullets: list[str]) -> str:
        return summary if not bullets else summary + "\n" + "\n".join(f"- {item}" for item in bullets)
