from __future__ import annotations

import io
import sys
from pathlib import Path

import boto3


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from cam_pipeline.company_selector import load_project_dotenv
from cam_pipeline.reports import (
    extract_pdf_text,
    get_report_s3_settings,
    list_reports,
    update_report_text,
)


def main() -> None:
    load_project_dotenv()
    region, bucket = get_report_s3_settings()
    s3 = boto3.client("s3", region_name=region)
    reports, _ = list_reports(limit=100)
    updated = 0

    for report in reports:
        if report.get("content") or not report.get("s3_key"):
            continue
        response = s3.get_object(Bucket=bucket, Key=report["s3_key"])
        pdf_bytes = response["Body"].read()
        content = extract_pdf_text(io.BytesIO(pdf_bytes))
        if not content:
            print(f"skipped {report['id']}: no extractable text")
            continue
        update_report_text(report["id"], content)
        updated += 1
        print(f"updated {report['id']}: {len(content)} characters")

    print(f"Backfilled {updated} report(s).")


if __name__ == "__main__":
    main()
