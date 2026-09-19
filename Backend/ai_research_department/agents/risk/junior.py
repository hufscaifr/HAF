from __future__ import annotations

from ai_research_department.agents.base import AgentResult, JuniorAgent
from ai_research_department.models import ResearchTask, RiskAssessment
from ai_research_department.utils.number_format import format_korean_number
from ai_research_department.workspace.research_context import ResearchContext


class RiskJuniorAgent(JuniorAgent):
    """Assess issue-level risks and validate fundamental and price impact."""

    def __init__(self) -> None:
        super().__init__("RiskJuniorAnalyst", "Assess issue risks, impact, and validation checks")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        issues = [item for item in context.issues() if item.approved]
        if not issues:
            return AgentResult(status="revision_required", summary="Approved issues are missing.", confidence=0.3)

        evidence = [item for item in context.evidence() if item.verified]
        estimates = [item for item in context.estimates() if item.approved]
        hypotheses = [item for item in context.hypotheses() if item.approved]
        metric_map = {str(item.metric): item for item in evidence if item.metric}
        estimate_ids = [item.estimate_id for item in estimates]
        created: list[str] = []

        for issue in issues:
            linked_hypotheses = [item for item in hypotheses if item.issue_id == issue.issue_id]
            affected_metrics = list(dict.fromkeys(issue.potential_impacts + [item.affected_metric for item in linked_hypotheses]))
            evidence_ids = self._evidence_ids_for_metrics(metric_map, affected_metrics) or [item.evidence_id for item in evidence]
            risk = RiskAssessment(
                issue_id=issue.issue_id,
                hypothesis_ids=[item.hypothesis_id for item in linked_hypotheses],
                title=self._title(issue.event),
                risk_type=self._risk_type(issue, affected_metrics),
                description=f"{issue.event} 이슈는 {', '.join(affected_metrics[:4]) or '핵심 지표'}에 영향을 줄 수 있어요.",
                likelihood=self._likelihood(issue.importance),
                severity=self._severity(issue.importance, affected_metrics),
                affected_metrics=affected_metrics,
                fundamental_impact=self._fundamental_view(metric_map, affected_metrics, estimates),
                price_impact=self._price_view(metric_map, issue.importance),
                verification_view=self._verification_view(metric_map, affected_metrics, estimates),
                mitigation_or_monitoring=self._monitoring_points(affected_metrics),
                evidence_ids=evidence_ids,
                estimate_ids=estimate_ids,
                confidence=min(max(issue.importance, 0.55), 0.88),
            )
            context.save_risk_assessment(risk)
            created.append(risk.risk_id)

        self.audit(context, "execute", target=task.task_id, reason=f"{len(created)} risk assessments created")
        return AgentResult(
            status="completed",
            summary=f"{len(created)} issue-level risk assessments created.",
            created_entities=created,
            confidence=0.82,
        )

    def _title(self, event: str) -> str:
        return event if len(event) <= 42 else event[:39] + "..."

    def _risk_type(self, issue, affected_metrics: list[str]) -> str:
        metrics = set(affected_metrics)
        if {"latest_close", "latest_volume"} & metrics or issue.issue_type == "market":
            return "price"
        if {"per", "pbr", "roe"} & metrics:
            return "valuation"
        if {"revenue", "operating_income", "eps", "operating_margin"} & metrics:
            return "fundamental"
        return "execution"

    def _likelihood(self, importance: float) -> str:
        if importance >= 0.78:
            return "high"
        if importance >= 0.55:
            return "medium"
        return "low"

    def _severity(self, importance: float, affected_metrics: list[str]) -> str:
        high_impact = {"revenue", "operating_income", "eps", "latest_close", "per", "pbr"}
        if importance >= 0.75 or high_impact.intersection(affected_metrics):
            return "high"
        if importance >= 0.5:
            return "medium"
        return "low"

    def _fundamental_view(self, metric_map: dict, affected_metrics: list[str], estimates: list) -> str:
        parts: list[str] = []
        for metric in ("revenue", "operating_income", "eps", "operating_margin", "roe", "debt_ratio"):
            if metric not in affected_metrics and metric not in metric_map:
                continue
            evidence = metric_map.get(metric)
            if evidence is not None:
                parts.append(f"{metric} evidence는 {format_korean_number(evidence.value, evidence.unit)}입니다")
        if estimates:
            estimate = estimates[-1]
            parts.append(
                "승인 estimate는 "
                f"매출 {format_korean_number(estimate.revenue, 'KRW')}, "
                f"영업이익 {format_korean_number(estimate.operating_profit, 'KRW')}, "
                f"EPS {format_korean_number(estimate.eps, 'KRW/share')}입니다"
            )
        return "; ".join(parts) if parts else "검증 가능한 fundamental evidence가 제한적이므로 추가 데이터 refresh가 필요합니다."

    def _price_view(self, metric_map: dict, importance: float) -> str:
        close = metric_map.get("latest_close")
        volume = metric_map.get("latest_volume")
        if close and volume:
            return (
                f"최근 종가 {format_korean_number(close.value, close.unit)}와 "
                f"거래량 {format_korean_number(volume.value, volume.unit)} 기준으로 주가 민감도를 점검합니다. "
                f"이슈 중요도 {importance:.2f}를 반영해 단기 price risk를 추적해야 합니다."
            )
        return "주가 검증에 필요한 latest_close 또는 latest_volume evidence가 부족합니다."

    def _verification_view(self, metric_map: dict, affected_metrics: list[str], estimates: list) -> str:
        verified_metrics = [metric for metric in affected_metrics if metric in metric_map]
        if estimates and verified_metrics:
            return f"검증 완료: {', '.join(verified_metrics[:6])} evidence와 승인 estimate가 연결됐습니다."
        if verified_metrics:
            return f"부분 검증: {', '.join(verified_metrics[:6])} evidence는 있으나 estimate 연결은 제한적입니다."
        return "미검증: 이슈 영향도를 확인할 직접 evidence가 부족합니다."

    def _monitoring_points(self, affected_metrics: list[str]) -> list[str]:
        points = ["공시/가격 데이터 refresh 이후 risk score를 재검토합니다."]
        if "latest_close" in affected_metrics or "latest_volume" in affected_metrics:
            points.append("종가와 거래량 변화가 valuation multiple에 미치는 영향을 확인합니다.")
        if {"revenue", "operating_income", "eps"} & set(affected_metrics):
            points.append("매출, 영업이익, EPS evidence가 estimate와 일치하는지 재검증합니다.")
        if {"per", "pbr", "roe"} & set(affected_metrics):
            points.append("PER/PBR/ROE 조합으로 valuation 부담과 수익성을 함께 점검합니다.")
        return points

    def _evidence_ids_for_metrics(self, metric_map: dict, affected_metrics: list[str]) -> list[str]:
        return [metric_map[metric].evidence_id for metric in affected_metrics if metric in metric_map]
