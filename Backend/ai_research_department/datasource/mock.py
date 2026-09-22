from __future__ import annotations

from typing import Any

from ai_research_department.datasource.base import DataSourceConnector


class MockDataSourceConnector(DataSourceConnector):
    """Deterministic source connector used by the MVP demo and tests."""

    def __init__(self) -> None:
        self.records = {
            "capacity": {
                "source_id": "mock_capacity",
                "fact": "신규 반도체 공장이 2026년 9월 가동을 시작했다.",
                "metric": "production_volume",
                "value": 18.0,
                "unit": "% capacity increase",
                "period": "2027E",
                "source_name": "Mock Company IR",
                "source_url": "mock://company-ir/capacity",
                "source_type": "company_ir",
            },
            "asp": {
                "source_id": "mock_asp",
                "fact": "DRAM 현물 가격이 최근 3개월 동안 12% 상승했다.",
                "metric": "asp",
                "value": 12.0,
                "unit": "% 3m change",
                "period": "2026Q3",
                "source_name": "Mock Industry Data",
                "source_url": "mock://industry/dram-asp",
                "source_type": "industry_data",
            },
            "shipments": {
                "source_id": "mock_shipments",
                "fact": "주요 고객사의 AI 서버 수요 증가로 출하량 전망이 상향됐다.",
                "metric": "shipment_volume",
                "value": 10.0,
                "unit": "% growth",
                "period": "2027E",
                "source_name": "Mock Channel Check",
                "source_url": "mock://channel-check/shipments",
                "source_type": "manual_input",
            },
        }

    async def search(self, query: str) -> list[dict[str, Any]]:
        normalized = query.lower()
        matches = []
        for key, record in self.records.items():
            haystack = f"{key} {record['fact']} {record['metric']}".lower()
            if any(token in haystack for token in normalized.split()):
                matches.append(record)
        return matches or list(self.records.values())[:1]

    async def fetch(self, source_id: str) -> dict[str, Any]:
        for record in self.records.values():
            if record["source_id"] == source_id:
                return record
        raise KeyError(f"Unknown mock source: {source_id}")

    async def extract(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        return [raw_data]
