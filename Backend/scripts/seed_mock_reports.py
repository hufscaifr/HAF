from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from cam_pipeline.company_selector import load_project_dotenv
from cam_pipeline.report_archive import connect_archive_db, init_report_archive


def main() -> None:
    load_project_dotenv()
    reports = json.loads((BACKEND_DIR / "data" / "mock_reports.json").read_text())
    with connect_archive_db() as conn:
        init_report_archive(conn)
        for report in reports:
            conn.execute(
                """
                INSERT INTO report_archive (
                    id, report_date, category, company, title, description,
                    summary, highlights, thumbnail_url, is_mock, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, TRUE, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    report_date = EXCLUDED.report_date,
                    category = EXCLUDED.category,
                    company = EXCLUDED.company,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    summary = EXCLUDED.summary,
                    highlights = EXCLUDED.highlights,
                    thumbnail_url = EXCLUDED.thumbnail_url,
                    is_mock = TRUE,
                    updated_at = NOW()
                """,
                (
                    report["id"], report["date"], report["category"], report["company"],
                    report["title"], report["desc"], report["summary"],
                    json.dumps(report["highlights"], ensure_ascii=False), report["thumbnail"],
                ),
            )
    print(f"Seeded {len(reports)} mock reports.")


if __name__ == "__main__":
    main()
