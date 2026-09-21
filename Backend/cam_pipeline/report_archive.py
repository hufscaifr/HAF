from __future__ import annotations

import os
from typing import Any, Optional

import psycopg
from psycopg.rows import dict_row


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect_archive_db() -> psycopg.Connection:
    return psycopg.connect(get_database_url(), row_factory=dict_row)


def init_report_archive(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS report_archive (
            id TEXT PRIMARY KEY,
            report_date DATE NOT NULL,
            category TEXT NOT NULL,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            summary TEXT NOT NULL,
            highlights JSONB NOT NULL DEFAULT '[]'::jsonb,
            thumbnail_url TEXT,
            is_mock BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_report_archive_date ON report_archive (report_date DESC)"
    )


def serialize_report(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "date": row["report_date"].isoformat(),
        "category": row["category"],
        "company": row["company"],
        "title": row["title"],
        "desc": row["description"],
        "summary": row["summary"],
        "highlights": row["highlights"],
        "thumbnail": row["thumbnail_url"],
        "is_mock": row["is_mock"],
    }


def list_archive_reports(limit: int = 20, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    with connect_archive_db() as conn:
        init_report_archive(conn)
        total = conn.execute("SELECT COUNT(*) AS count FROM report_archive").fetchone()["count"]
        rows = conn.execute(
            """
            SELECT * FROM report_archive
            ORDER BY report_date DESC, created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        ).fetchall()
    return [serialize_report(row) for row in rows], int(total)


def get_archive_report(report_id: str) -> Optional[dict[str, Any]]:
    with connect_archive_db() as conn:
        init_report_archive(conn)
        row = conn.execute(
            "SELECT * FROM report_archive WHERE id = %s",
            (report_id,),
        ).fetchone()
    return serialize_report(row) if row else None
