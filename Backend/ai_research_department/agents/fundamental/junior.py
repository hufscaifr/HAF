from __future__ import annotations

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.models import Forecast, FundamentalAssumption, ResearchTask
from ai_research_department.workspace.research_context import ResearchContext


class FundamentalJuniorAgent(JuniorAgent):
    """Translate evidence and hypotheses into business assumptions."""

    def __init__(self) -> None:
        super().__init__("FundamentalJuniorAgent", "Forecast business drivers")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        if context.project.request.data_mode == "real":
            return await self._execute_real(task, context)

        evidence_ids = [item.evidence_id for item in context.evidence() if item.verified]
        assumptions = [
            FundamentalAssumption(
                metric="shipment_volume",
                value=110.0,
                unit="index",
                period="2027E",
                reasoning=["신규 공장 가동과 고객 수요 증가로 출하량 지수가 상승해요."],
                evidence_ids=evidence_ids,
                confidence=0.78,
            ),
            FundamentalAssumption(
                metric="asp",
                value=112.0,
                unit="index",
                period="2027E",
                reasoning=["DRAM 가격 상승 자료를 ASP 지수에 반영했어요."],
                evidence_ids=evidence_ids,
                confidence=0.76,
            ),
            FundamentalAssumption(
                metric="gross_margin",
                value=0.38,
                unit="ratio",
                period="2027E",
                reasoning=["ASP 상승과 가동률 개선은 마진에 긍정적이에요."],
                evidence_ids=evidence_ids,
                confidence=0.74,
            ),
        ]
        forecasts = [
            Forecast(
                metric="revenue_growth",
                previous_assumption=4.0,
                new_assumption=10.0,
                unit="%",
                direction="up",
                reasoning=["출하량과 ASP가 동시에 개선되는 시나리오예요."],
                evidence_ids=evidence_ids,
                confidence=0.77,
            )
        ]
        for assumption in assumptions:
            context.save_assumption(assumption)
        for forecast in forecasts:
            context.save_forecast(forecast)
        self.audit(context, "execute", target=task.task_id, reason="Revenue growth assumption revised")
        return AgentResult(
            status="completed",
            summary="Revenue growth assumption revised.",
            created_entities=[*[item.assumption_id for item in assumptions], *[item.forecast_id for item in forecasts]],
            confidence=0.77,
        )

    async def _execute_real(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        evidence = [item for item in context.evidence() if item.verified]
        evidence_ids = [item.evidence_id for item in evidence]
        by_metric = {str(item.metric): item for item in evidence if item.metric}

        assumptions: list[FundamentalAssumption] = []
        for metric, fallback_unit in (
            ("revenue", "KRW"),
            ("operating_income", "KRW"),
            ("eps", "KRW/share"),
            ("operating_margin", "%"),
            ("roe", "%"),
            ("debt_ratio", "%"),
            ("per", "x"),
            ("pbr", "x"),
        ):
            source = by_metric.get(metric)
            if source is None or source.value is None:
                continue
            assumptions.append(
                FundamentalAssumption(
                    metric=metric,
                    value=source.value,
                    unit=source.unit or fallback_unit,
                    period=source.period,
                    reasoning=[f"{source.source_name}에서 수집된 {metric} evidence를 사용했어요."],
                    evidence_ids=[source.evidence_id],
                    confidence=source.confidence,
                )
            )

        if not assumptions:
            return AgentResult(
                status="revision_required",
                summary="No real financial assumptions could be created from collected evidence.",
                confidence=0.3,
            )

        forecast = Forecast(
            metric="fundamental_snapshot",
            previous_assumption=None,
            new_assumption=None,
            unit=None,
            direction="neutral",
            reasoning=["실제 수집된 재무·시장 evidence를 기반으로 현재 fundamentals snapshot을 구성했어요."],
            evidence_ids=evidence_ids,
            confidence=min(max(sum(item.confidence for item in evidence) / len(evidence), 0.5), 0.9) if evidence else 0.5,
        )
        for assumption in assumptions:
            context.save_assumption(assumption)
        context.save_forecast(forecast)
        self.audit(context, "execute", target=task.task_id, reason=f"{len(assumptions)} real assumptions created")
        return AgentResult(
            status="completed",
            summary=f"{len(assumptions)} real assumptions created.",
            created_entities=[*[item.assumption_id for item in assumptions], forecast.forecast_id],
            confidence=forecast.confidence,
        )
