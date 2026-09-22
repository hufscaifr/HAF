from __future__ import annotations

from ai_research_department.models import ChartArtifact, Evidence, TableArtifact


FINANCIAL_METRIC_LABELS = {
    "revenue": "Revenue",
    "operating_income": "Operating Income",
    "net_income": "Net Income",
    "eps": "EPS",
    "per": "PER",
    "pbr": "PBR",
    "roe": "ROE",
    "debt_ratio": "Debt Ratio",
    "operating_margin": "Operating Margin",
    "latest_close": "Latest Close",
    "latest_volume": "Latest Volume",
}


class VisualizationService:
    """Build chart and table artifacts from collected evidence."""

    def build_from_evidence(self, evidence: list[Evidence]) -> tuple[list[ChartArtifact], list[TableArtifact]]:
        numeric = self._numeric_evidence(evidence)
        tables = [self.build_evidence_table(evidence)] if evidence else []
        charts: list[ChartArtifact] = []
        financial_chart = self.build_financial_metric_chart(numeric)
        if financial_chart is not None:
            charts.append(financial_chart)
        valuation_chart = self.build_valuation_chart(numeric)
        if valuation_chart is not None:
            charts.append(valuation_chart)
        if not charts:
            generic_chart = self.build_generic_numeric_chart(numeric)
            if generic_chart is not None:
                charts.append(generic_chart)
        return charts, tables

    def build_evidence_table(self, evidence: list[Evidence]) -> TableArtifact:
        rows = [
            {
                "metric": item.metric,
                "value": item.value,
                "unit": item.unit,
                "period": item.period,
                "source_name": item.source_name,
                "confidence": item.confidence,
                "evidence_id": item.evidence_id,
            }
            for item in evidence
        ]
        return TableArtifact(
            title="Collected Evidence Table",
            columns=["metric", "value", "unit", "period", "source_name", "confidence", "evidence_id"],
            rows=rows,
            evidence_ids=[item.evidence_id for item in evidence],
            description="Data Department가 수집한 evidence를 프론트 표로 표시하기 위한 payload예요.",
        )

    def build_financial_metric_chart(self, evidence: list[Evidence]) -> ChartArtifact | None:
        selected = [
            item
            for item in evidence
            if item.metric in {"revenue", "operating_income", "net_income", "market_cap"}
        ]
        if not selected:
            return None
        return ChartArtifact(
            title="Financial Scale Metrics",
            chart_type="bar",
            data=[self._chart_row(item) for item in selected],
            evidence_ids=[item.evidence_id for item in selected],
            description="매출, 영업이익, 순이익, 시가총액 등 규모 지표를 비교하는 chart-ready payload예요.",
        )

    def build_valuation_chart(self, evidence: list[Evidence]) -> ChartArtifact | None:
        selected = [
            item
            for item in evidence
            if item.metric in {"eps", "per", "pbr", "roe", "debt_ratio", "operating_margin", "latest_close"}
        ]
        if not selected:
            return None
        return ChartArtifact(
            title="Valuation and Profitability Metrics",
            chart_type="bar",
            data=[self._chart_row(item) for item in selected],
            evidence_ids=[item.evidence_id for item in selected],
            description="밸류에이션과 수익성 지표를 비교하는 chart-ready payload예요.",
        )

    def build_generic_numeric_chart(self, evidence: list[Evidence]) -> ChartArtifact | None:
        selected = [item for item in evidence if item.metric]
        if not selected:
            return None
        return ChartArtifact(
            title="Collected Numeric Evidence",
            chart_type="bar",
            data=[self._chart_row(item) for item in selected],
            evidence_ids=[item.evidence_id for item in selected],
            description="수집된 숫자형 evidence를 범용 bar chart로 표시하기 위한 payload예요.",
        )

    def _numeric_evidence(self, evidence: list[Evidence]) -> list[Evidence]:
        numeric: list[Evidence] = []
        for item in evidence:
            try:
                float(item.value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            numeric.append(item)
        return numeric

    def _chart_row(self, evidence: Evidence) -> dict:
        return {
            "metric": evidence.metric,
            "label": FINANCIAL_METRIC_LABELS.get(str(evidence.metric), str(evidence.metric)),
            "value": float(evidence.value),  # type: ignore[arg-type]
            "unit": evidence.unit,
            "period": evidence.period,
            "source_name": evidence.source_name,
            "evidence_id": evidence.evidence_id,
        }
