from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DB_PATH = PROJECT_ROOT / "reports.db"


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
                   generate_date, author, created_at, updated_at
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
    payload: dict[str, Any] = {
        "id": report_row["report_id"],
        "Title": report_row["title"],
        "subtitle": report_row["subtitle"],
        "paragraph_title": report_row["paragraph_title"],
        "summary": report_row["summary"],
        "generate_date": report_row["generate_date"],
        "author": report_row["author"],
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
