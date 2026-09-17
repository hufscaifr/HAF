from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESEARCH_CACHE_DB_PATH = PROJECT_ROOT / "research_cache.db"
RESEARCH_PIPELINE_VERSION = os.getenv("CAM_RESEARCH_PIPELINE_VERSION", "news_pipeline_v2")


def get_research_cache_db_path() -> Path:
    configured = os.getenv("CAM_RESEARCH_CACHE_DB")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_RESEARCH_CACHE_DB_PATH


def connect_research_cache_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_research_cache_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_research_cache_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS research_jobs (
            research_id TEXT PRIMARY KEY,
            signature TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT,
            article_char_limit INTEGER,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS company_analysis_cache (
            cache_key TEXT PRIMARY KEY,
            research_id TEXT,
            ticker TEXT NOT NULL,
            kind TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_company_analysis_lookup
        ON company_analysis_cache(research_id, ticker, kind)
        """
    )
    conn.commit()


def build_research_signature(
    url: str,
    provider: str,
    model: Optional[str],
    article_char_limit: int,
) -> str:
    return stable_hash(
        {
            "pipeline_version": RESEARCH_PIPELINE_VERSION,
            "url": normalize_url(url),
            "provider": provider,
            "model": model or "",
            "article_char_limit": article_char_limit,
        }
    )


def get_cached_research(signature: str) -> Optional[dict[str, Any]]:
    with connect_research_cache_db() as conn:
        init_research_cache_db(conn)
        row = conn.execute(
            """
            SELECT research_id, payload_json, created_at, updated_at
            FROM research_jobs
            WHERE signature = ?
            """,
            (signature,),
        ).fetchone()
    if not row:
        return None

    payload = json_loads(row["payload_json"])
    payload["research_id"] = row["research_id"]
    payload["cache"] = {
        "hit": True,
        "kind": "research_selection",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    return payload


def get_cached_research_by_id(research_id: str) -> Optional[dict[str, Any]]:
    with connect_research_cache_db() as conn:
        init_research_cache_db(conn)
        row = conn.execute(
            """
            SELECT research_id, payload_json, created_at, updated_at
            FROM research_jobs
            WHERE research_id = ?
            """,
            (research_id,),
        ).fetchone()
    if not row:
        return None

    payload = json_loads(row["payload_json"])
    payload["research_id"] = row["research_id"]
    payload["cache"] = {
        "hit": True,
        "kind": "research_selection",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    return payload


def save_research(
    signature: str,
    url: str,
    provider: str,
    model: Optional[str],
    article_char_limit: int,
    payload: dict[str, Any],
) -> str:
    now = utc_now()
    research_id = payload.get("research_id") or str(uuid.uuid4())
    payload_to_store = {**payload, "research_id": research_id}
    payload_to_store.setdefault("cache", {"hit": False, "kind": "research_selection"})

    with connect_research_cache_db() as conn:
        init_research_cache_db(conn)
        conn.execute(
            """
            INSERT INTO research_jobs (
                research_id, signature, url, provider, model,
                article_char_limit, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(signature) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (
                research_id,
                signature,
                normalize_url(url),
                provider,
                model,
                article_char_limit,
                json_dumps(payload_to_store),
                now,
                now,
            ),
        )
        conn.commit()
    return research_id


def build_company_cache_key(
    kind: str,
    research_id: Optional[str],
    ticker: str,
    provider: str,
    model: Optional[str],
) -> str:
    return stable_hash(
        {
            "kind": kind,
            "research_id": research_id or "",
            "ticker": ticker,
            "provider": provider,
            "model": model or "",
        }
    )


def get_cached_company_analysis(cache_key: str) -> Optional[dict[str, Any]]:
    with connect_research_cache_db() as conn:
        init_research_cache_db(conn)
        row = conn.execute(
            """
            SELECT payload_json, created_at, updated_at
            FROM company_analysis_cache
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()
    if not row:
        return None

    payload = json_loads(row["payload_json"])
    payload["cache"] = {
        "hit": True,
        "kind": payload.get("cache", {}).get("kind", "company_analysis"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    return payload


def save_company_analysis(
    cache_key: str,
    research_id: Optional[str],
    ticker: str,
    kind: str,
    payload: dict[str, Any],
) -> None:
    now = utc_now()
    payload_to_store = {
        **payload,
        "research_id": research_id,
        "cache": {
            "hit": False,
            "kind": kind,
            "updated_at": now,
        },
    }
    with connect_research_cache_db() as conn:
        init_research_cache_db(conn)
        conn.execute(
            """
            INSERT INTO company_analysis_cache (
                cache_key, research_id, ticker, kind,
                payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (
                cache_key,
                research_id,
                ticker,
                kind,
                json_dumps(payload_to_store),
                now,
                now,
            ),
        )
        conn.commit()


def normalize_url(value: str) -> str:
    return str(value or "").strip()


def stable_hash(value: dict[str, Any]) -> str:
    encoded = json_dumps(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_loads(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
