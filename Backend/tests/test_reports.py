from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app


SAMPLE_REPORT = {
    "Title": "유가 급등 파장",
    "subtitle": "중동 불안발 국제유가 급등과 정부 유류가격 통제",
    "paragraph_title": "S-Oil, 삼성전자, SK하이닉스",
    "summary": "국제유가 급등이 국내 주요 기업에 미칠 영향을 요약합니다.",
    "generate_date": "2026-09-18",
    "author": "제갈민찬",
    "company1_name": "S-Oil",
    "company1_ticker": "010950",
    "company1_opinion_summary": "정제마진 개선 가능성을 주시합니다.",
    "company1_ta_summary": "단기 추세는 중립입니다.",
    "company2_name": "삼성전자",
    "company2_ticker": "005930",
    "company2_opinion_summary": "원가 부담의 영향을 확인해야 합니다.",
    "company2_ta_summary": "중기 지지선 부근입니다.",
    "company3_name": "SK하이닉스",
    "company3_ticker": "000660",
    "company3_opinion_summary": "메모리 업황 회복이 핵심입니다.",
    "company3_ta_summary": "변동성 확대 구간입니다.",
}


class ReportsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "REPORTS_API_TOKEN": "test-report-token",
                "CAM_REPORTS_DB": str(Path(self.temp_dir.name) / "reports.db"),
            },
        )
        self.env.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.env.stop()
        self.temp_dir.cleanup()

    def test_report_ingestion_is_authenticated_and_idempotent(self) -> None:
        unauthorized = self.client.post("/api/reports", json=SAMPLE_REPORT)
        self.assertEqual(unauthorized.status_code, 401)

        headers = {"Authorization": "Bearer test-report-token"}
        created = self.client.post("/api/reports", json=SAMPLE_REPORT, headers=headers)
        duplicate = self.client.post("/api/reports", json=SAMPLE_REPORT, headers=headers)

        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.json()["created"])
        self.assertEqual(duplicate.status_code, 201)
        self.assertFalse(duplicate.json()["created"])
        self.assertEqual(created.json()["report_id"], duplicate.json()["report_id"])

    def test_saved_report_can_be_listed_and_read(self) -> None:
        headers = {"Authorization": "Bearer test-report-token"}
        created = self.client.post("/api/reports", json=SAMPLE_REPORT, headers=headers)
        report_id = created.json()["report_id"]

        listing = self.client.get("/api/reports")
        detail = self.client.get(f"/api/reports/{report_id}")

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["total"], 1)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["report"]["Title"], SAMPLE_REPORT["Title"])
        self.assertEqual(len(detail.json()["report"]["companies"]), 3)
        self.assertEqual(
            detail.json()["report"]["company2_ticker"],
            SAMPLE_REPORT["company2_ticker"],
        )


if __name__ == "__main__":
    unittest.main()
