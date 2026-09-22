from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DB_PATH = PROJECT_ROOT / "reports.db"
DEFAULT_REPORT_PDF_MAX_BYTES = 25 * 1024 * 1024


def get_reports_db_path() -> Path:
    configured = os.getenv("CAM_REPORTS_DB")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_REPORTS_DB_PATH


def connect_reports_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_reports_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_reports_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            ingestion_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            paragraph_title TEXT NOT NULL,
            summary TEXT NOT NULL,
            generate_date TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    ensure_report_upload_columns(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS report_companies (
            report_id TEXT NOT NULL,
            position INTEGER NOT NULL CHECK(position BETWEEN 1 AND 3),
            name TEXT NOT NULL,
            ticker TEXT NOT NULL,
            opinion_summary TEXT NOT NULL,
            ta_summary TEXT NOT NULL,
            PRIMARY KEY (report_id, position),
            FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_generate_date
        ON reports(generate_date DESC, created_at DESC)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_report_companies_ticker
        ON report_companies(ticker)
        """
    )
    conn.commit()


def ensure_report_upload_columns(conn: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(reports)").fetchall()
    }
    upload_columns = {
        "report_date": "TEXT",
        "category": "TEXT",
        "company": "TEXT",
        "s3_key": "TEXT",
        "original_filename": "TEXT",
        "content_type": "TEXT",
        "file_size": "INTEGER",
        "description": "TEXT NOT NULL DEFAULT ''",
        "content": "TEXT NOT NULL DEFAULT ''",
        "highlights_json": "TEXT NOT NULL DEFAULT '[]'",
    }
    for column_name, column_type in upload_columns.items():
        if column_name not in existing_columns:
            conn.execute(
                f"ALTER TABLE reports ADD COLUMN {column_name} {column_type}"
            )


def save_uploaded_report(
    *,
    title: str,
    report_date: str,
    category: str,
    company: Optional[str],
    s3_key: str,
    original_filename: str,
    content_type: str,
    file_size: int,
    description: str = "",
    summary: str = "",
    content: str = "",
    highlights: Optional[list[str]] = None,
) -> dict[str, Any]:
    normalized_date = normalize_date(report_date)
    now = utc_now()
    report_id = str(uuid.uuid4())
    ingestion_key = hashlib.sha256(s3_key.encode("utf-8")).hexdigest()

    with connect_reports_db() as conn:
        init_reports_db(conn)
        conn.execute(
            """
            INSERT INTO reports (
                report_id, ingestion_key, title, subtitle, paragraph_title,
                summary, generate_date, author, report_date, category, company,
                s3_key, original_filename, content_type, file_size,
                description, content, highlights_json, created_at, updated_at
            ) VALUES (?, ?, ?, '', '', ?, ?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                ingestion_key,
                title.strip(),
                summary.strip(),
                normalized_date,
                normalized_date,
                category.strip(),
                company.strip() if company else None,
                s3_key,
                original_filename,
                content_type,
                file_size,
                description.strip(),
                content.strip(),
                json.dumps(highlights or [], ensure_ascii=False),
                now,
                now,
            ),
        )
        conn.commit()
        report = get_report_by_id(report_id, conn=conn)
    if not report:
        raise RuntimeError("The uploaded report was not found after saving.")
    return report


def get_report_s3_settings() -> tuple[str, str]:
    region = os.getenv("AWS_REGION", "").strip()
    bucket = os.getenv("AWS_S3_BUCKET", "").strip()
    if not region:
        raise RuntimeError("AWS_REGION is not configured.")
    if not bucket:
        raise RuntimeError("AWS_S3_BUCKET is not configured.")
    return region, bucket


def get_report_pdf_max_bytes() -> int:
    configured = os.getenv("REPORT_PDF_MAX_BYTES", "").strip()
    if not configured:
        return DEFAULT_REPORT_PDF_MAX_BYTES
    try:
        value = int(configured)
    except ValueError as exc:
        raise RuntimeError("REPORT_PDF_MAX_BYTES must be an integer.") from exc
    if value <= 0:
        raise RuntimeError("REPORT_PDF_MAX_BYTES must be greater than zero.")
    return value


def build_report_s3_key(report_date: str, filename: str) -> str:
    normalized_date = normalize_date(report_date)
    safe_name = sanitize_pdf_filename(filename)
    year, month, _ = normalized_date.split("-")
    return f"reports/{year}/{month}/{uuid.uuid4().hex}-{safe_name}"


def sanitize_pdf_filename(filename: str) -> str:
    basename = Path(filename or "report.pdf").name
    stem = re.sub(r"[^\w.-]+", "-", basename, flags=re.UNICODE).strip("-.")
    if not stem:
        stem = "report.pdf"
    if not stem.lower().endswith(".pdf"):
        stem = f"{stem}.pdf"
    return stem[:180]


def save_report(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    normalized = normalize_report_payload(payload)
    ingestion_key = build_ingestion_key(normalized)
    now = utc_now()

    with connect_reports_db() as conn:
        init_reports_db(conn)
        existing = conn.execute(
            "SELECT report_id FROM reports WHERE ingestion_key = ?",
            (ingestion_key,),
        ).fetchone()
        if existing:
            report = get_report_by_id(existing["report_id"], conn=conn)
            return report, False

        report_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO reports (
                report_id, ingestion_key, title, subtitle, paragraph_title,
                summary, generate_date, author, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                ingestion_key,
                normalized["Title"],
                normalized["subtitle"],
                normalized["paragraph_title"],
                normalized["summary"],
                normalized["generate_date"],
                normalized["author"],
                now,
                now,
            ),
        )
        conn.executemany(
            """
            INSERT INTO report_companies (
                report_id, position, name, ticker, opinion_summary, ta_summary
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    report_id,
                    company["position"],
                    company["name"],
                    company["ticker"],
                    company["opinion_summary"],
                    company["ta_summary"],
                )
                for company in normalized["companies"]
            ],
        )
        conn.commit()
        report = get_report_by_id(report_id, conn=conn)
    return report, True


def list_reports(limit: int = 20, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    with connect_reports_db() as conn:
        init_reports_db(conn)
        total = int(conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0])
        rows = conn.execute(
            """
            SELECT report_id
            FROM reports
            ORDER BY generate_date DESC, created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        reports = [get_report_by_id(row["report_id"], conn=conn) for row in rows]
    return reports, total


def get_report_by_id(
    report_id: str,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[dict[str, Any]]:
    owns_connection = conn is None
    connection = conn or connect_reports_db()
    try:
        init_reports_db(connection)
        row = connection.execute(
            """
            SELECT report_id, title, subtitle, paragraph_title, summary,
                   generate_date, author, report_date, category, company,
                   s3_key, original_filename, content_type, file_size,
                   description, content, highlights_json,
                   created_at, updated_at
            FROM reports
            WHERE report_id = ?
            """,
            (report_id,),
        ).fetchone()
        if not row:
            return None

        company_rows = connection.execute(
            """
            SELECT position, name, ticker, opinion_summary, ta_summary
            FROM report_companies
            WHERE report_id = ?
            ORDER BY position
            """,
            (report_id,),
        ).fetchall()
        return serialize_report(row, company_rows)
    finally:
        if owns_connection:
            connection.close()


def normalize_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "Title": str(payload["Title"]).strip(),
        "subtitle": str(payload["subtitle"]).strip(),
        "paragraph_title": str(payload["paragraph_title"]).strip(),
        "summary": str(payload["summary"]).strip(),
        "generate_date": normalize_date(payload["generate_date"]),
        "author": str(payload["author"]).strip(),
        "companies": [],
    }
    for position in range(1, 4):
        normalized["companies"].append(
            {
                "position": position,
                "name": str(payload[f"company{position}_name"]).strip(),
                "ticker": str(payload[f"company{position}_ticker"]).strip(),
                "opinion_summary": str(payload[f"company{position}_opinion_summary"]).strip(),
                "ta_summary": str(payload[f"company{position}_ta_summary"]).strip(),
            }
        )
    return normalized


def serialize_report(
    report_row: sqlite3.Row,
    company_rows: list[sqlite3.Row],
) -> dict[str, Any]:
    companies = [
        {
            "position": row["position"],
            "name": row["name"],
            "ticker": row["ticker"],
            "opinion_summary": row["opinion_summary"],
            "ta_summary": row["ta_summary"],
        }
        for row in company_rows
    ]
    try:
        highlights = json.loads(report_row["highlights_json"] or "[]")
    except (json.JSONDecodeError, TypeError):
        highlights = []
    if not isinstance(highlights, list):
        highlights = []

    title = report_row["title"]
    report_date = report_row["report_date"] or report_row["generate_date"]
    description = report_row["description"] or report_row["subtitle"] or report_row["summary"]
    payload: dict[str, Any] = {
        "id": report_row["report_id"],
        "Title": title,
        "title": title,
        "subtitle": report_row["subtitle"],
        "paragraph_title": report_row["paragraph_title"],
        "summary": report_row["summary"],
        "generate_date": report_row["generate_date"],
        "author": report_row["author"],
        "report_date": report_date,
        "date": report_date,
        "category": report_row["category"],
        "company": report_row["company"],
        "s3_key": report_row["s3_key"],
        "original_filename": report_row["original_filename"],
        "content_type": report_row["content_type"],
        "file_size": report_row["file_size"],
        "desc": description,
        "description": description,
        "content": report_row["content"] or "",
        "highlights": [str(item) for item in highlights if str(item).strip()],
        "thumbnail": None,
        "is_mock": False,
        "companies": companies,
        "created_at": report_row["created_at"],
        "updated_at": report_row["updated_at"],
    }
    for company in companies:
        position = company["position"]
        payload[f"company{position}_name"] = company["name"]
        payload[f"company{position}_ticker"] = company["ticker"]
        payload[f"company{position}_opinion_summary"] = company["opinion_summary"]
        payload[f"company{position}_ta_summary"] = company["ta_summary"]
    return payload


def build_ingestion_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_date(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value)).isoformat()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
