from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api import app


REPORT_FORM = {
    "title": "Daily Market Report",
    "report_date": "2026-09-18",
    "category": "daily",
    "company": "Samsung Electronics",
    "description": "Daily market analysis",
    "summary": "Semiconductors led the market.",
    "content": "Samsung Electronics and memory demand were analyzed.",
    "highlights": '["Memory demand", "Foreign inflows"]',
}
PDF_BYTES = b"%PDF-1.7\nmock report content\n%%EOF"


class ReportsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "REPORTS_API_TOKEN": "test-report-token",
                "CAM_REPORTS_DB": str(Path(self.temp_dir.name) / "reports.db"),
                "AWS_REGION": "ap-northeast-2",
                "AWS_S3_BUCKET": "test-report-bucket",
                "REPORT_PDF_MAX_BYTES": "1048576",
            },
        )
        self.env.start()
        self.s3 = MagicMock()
        self.boto_client = patch("api.boto3.client", return_value=self.s3)
        self.boto_client.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.boto_client.stop()
        self.env.stop()
        self.temp_dir.cleanup()

    def upload(self, **overrides):
        data = {**REPORT_FORM, **overrides}
        return self.client.post(
            "/api/reports",
            data=data,
            files={"file": ("report.pdf", PDF_BYTES, "application/pdf")},
            headers={"Authorization": "Bearer test-report-token"},
        )

    def test_report_upload_is_authenticated(self) -> None:
        response = self.client.post(
            "/api/reports",
            data=REPORT_FORM,
            files={"file": ("report.pdf", PDF_BYTES, "application/pdf")},
        )
        self.assertEqual(response.status_code, 401)
        self.s3.upload_fileobj.assert_not_called()

    def test_pdf_is_uploaded_and_metadata_is_saved(self) -> None:
        created = self.upload()

        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["category"], "daily")
        self.assertTrue(body["s3_key"].startswith("reports/2026/09/"))
        self.s3.upload_fileobj.assert_called_once()

        listing = self.client.get("/api/reports")
        detail = self.client.get(f"/api/reports/{body['report_id']}")

        self.assertEqual(listing.json()["total"], 1)
        self.assertEqual(detail.status_code, 200)
        report = detail.json()["report"]
        self.assertEqual(report["report_date"], "2026-09-18")
        self.assertEqual(report["company"], "Samsung Electronics")
        self.assertEqual(report["content_type"], "application/pdf")
        self.assertEqual(report["file_size"], len(PDF_BYTES))
        self.assertEqual(report["title"], "Daily Market Report")
        self.assertEqual(report["content"], REPORT_FORM["content"])
        self.assertEqual(report["highlights"], ["Memory demand", "Foreign inflows"])
        self.assertFalse(report["is_mock"])

    def test_non_pdf_content_is_rejected_before_s3_upload(self) -> None:
        response = self.client.post(
            "/api/reports",
            data=REPORT_FORM,
            files={"file": ("report.pdf", b"not a pdf", "application/pdf")},
            headers={"Authorization": "Bearer test-report-token"},
        )

        self.assertEqual(response.status_code, 400)
        self.s3.upload_fileobj.assert_not_called()

    def test_s3_object_is_deleted_when_database_save_fails(self) -> None:
        with patch("api.save_uploaded_report", side_effect=RuntimeError("db unavailable")):
            response = self.upload()

        self.assertEqual(response.status_code, 502)
        self.s3.delete_object.assert_called_once()


if __name__ == "__main__":
    unittest.main()
