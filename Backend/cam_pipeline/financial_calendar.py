from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from cam_pipeline.company_selector import DEFAULT_OPENAI_MODEL, get_openai_client_class, normalize_env_api_key
from cam_pipeline.financial_calendar_providers import collect_structured_events


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FINANCIAL_CALENDAR_DB_PATH = PROJECT_ROOT / "financial_calendar.db"
DEFAULT_FINANCIAL_CALENDAR_MODEL = os.getenv("OPENAI_FINANCIAL_CALENDAR_MODEL", DEFAULT_OPENAI_MODEL)
DEFAULT_FINANCIAL_CALENDAR_TIMEZONE = os.getenv("CAM_TIMEZONE", "Asia/Seoul")
DEFAULT_LOOKAHEAD_DAYS = int(os.getenv("CAM_FINANCIAL_CALENDAR_LOOKAHEAD_DAYS", "45"))
DEFAULT_REQUEST_TIMEOUT_SECONDS = float(os.getenv("OPENAI_FINANCIAL_CALENDAR_TIMEOUT_SECONDS", "90"))
DEFAULT_ANALYSIS_BATCH_SIZE = int(os.getenv("CAM_FINANCIAL_CALENDAR_ANALYSIS_BATCH_SIZE", "25"))
ANALYSIS_VERSION = "financial_event_analysis_v2"
EVENT_TYPES = ("macro", "earnings", "disclosure", "policy", "market_holiday")
IMPORTANCE_LEVELS = ("high", "medium", "low")


class FinancialCalendarError(RuntimeError):
    """Raised when financial calendar collection, analysis, or storage fails."""


def get_financial_calendar_db_path() -> Path:
    configured = os.getenv("CAM_FINANCIAL_CALENDAR_DB")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_FINANCIAL_CALENDAR_DB_PATH


def get_today(timezone_name: str = DEFAULT_FINANCIAL_CALENDAR_TIMEZONE) -> date:
    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        timezone = ZoneInfo("UTC")
    return datetime.now(timezone).date()


def default_end_date(start_date: date) -> date:
    return start_date + timedelta(days=DEFAULT_LOOKAHEAD_DAYS)


def parse_iso_date(value: Optional[str], fallback: date) -> date:
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise FinancialCalendarError(f"Invalid date format: {value}. Use YYYY-MM-DD.") from exc


def connect_calendar_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_financial_calendar_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_financial_calendar_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, title TEXT NOT NULL,
            category TEXT NOT NULL, importance TEXT NOT NULL, detail TEXT, country TEXT,
            source_name TEXT, source_url TEXT, unique_key TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique_key ON events(unique_key)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar_metadata (
            key TEXT PRIMARY KEY, value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    ensure_calendar_columns(conn)
    conn.commit()


def ensure_calendar_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    columns = {
        "event_uid": "TEXT", "time": "TEXT", "forecast": "TEXT", "consensus": "TEXT",
        "previous": "TEXT", "actual": "TEXT", "ai_comment": "TEXT",
        "expected_impact": "TEXT", "source_provider": "TEXT", "source_id": "TEXT",
        "ticker": "TEXT", "raw_payload": "TEXT", "analysis_version": "TEXT",
        "country": "TEXT", "source_name": "TEXT", "source_url": "TEXT", "unique_key": "TEXT",
        "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }
    for column, definition in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE events ADD COLUMN {column} {definition}")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_events_event_uid ON events(event_uid)")


def get_metadata(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM calendar_metadata WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else None


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn.execute("""
        INSERT INTO calendar_metadata (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    """, (key, value, now))


def list_financial_events(
    start_date: date, end_date: date, category: Optional[str] = None,
    importance: Optional[str] = None, db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    with connect_calendar_db(db_path) as conn:
        init_financial_calendar_db(conn)
        query = """
            SELECT id AS legacy_id, event_uid, date, title, category, country, time, importance,
                   forecast, consensus, previous, actual, detail, ai_comment,
                   expected_impact, source_name, source_url, ticker
            FROM events WHERE date BETWEEN ? AND ?
        """
        params: list[Any] = [start_date.isoformat(), end_date.isoformat()]
        if category:
            query += " AND category = ?"
            params.append(_legacy_type(category))
        if importance:
            query += " AND importance = ?"
            params.append(importance)
        query += " ORDER BY date, CASE importance WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, title"
        return [_api_event(dict(row)) for row in conn.execute(query, params).fetchall()]


def refresh_financial_calendar(
    start_date: Optional[date] = None, end_date: Optional[date] = None,
    model: Optional[str] = None, db_path: Optional[Path] = None,
    providers: Optional[list[str]] = None, analyze: bool = True,
) -> dict[str, Any]:
    today = get_today()
    start = start_date or today
    end = end_date or default_end_date(start)
    if end < start:
        raise FinancialCalendarError("end_date must be greater than or equal to start_date.")

    raw_events, provider_reports = collect_structured_events(start, end, providers)
    events = normalize_calendar_events(raw_events, start, end)
    analysis_error = None
    if analyze and events:
        try:
            events = analyze_financial_events(events, model or DEFAULT_FINANCIAL_CALENDAR_MODEL)
        except Exception as exc:
            analysis_error = str(exc)

    with connect_calendar_db(db_path) as conn:
        init_financial_calendar_db(conn)
        upsert_financial_events(conn, events)
        set_metadata(conn, "last_refresh_date", today.isoformat())
        set_metadata(conn, "last_refresh_start_date", start.isoformat())
        set_metadata(conn, "last_refresh_end_date", end.isoformat())
        set_metadata(conn, "analysis_version", ANALYSIS_VERSION)
        set_metadata(conn, "provider_status", json.dumps(provider_reports, ensure_ascii=False))
        conn.commit()

    analysis_status = "error" if analysis_error else ("success" if analyze and events else "skipped")
    return {
        "status": "success", "start_date": start.isoformat(), "end_date": end.isoformat(),
        "inserted_or_updated": len(events), "events": events, "providers": provider_reports,
        "analysis": {"requested": analyze, "model": model or DEFAULT_FINANCIAL_CALENDAR_MODEL,
                     "status": analysis_status, "error": analysis_error},
    }


def ensure_financial_calendar_current(
    model: Optional[str] = None, db_path: Optional[Path] = None,
) -> dict[str, Any]:
    today = get_today()
    with connect_calendar_db(db_path) as conn:
        init_financial_calendar_db(conn)
        last_refresh_date = get_metadata(conn, "last_refresh_date")
        analysis_version = get_metadata(conn, "analysis_version")
    if last_refresh_date == today.isoformat() and analysis_version == ANALYSIS_VERSION:
        return {"refreshed": False, "last_refresh_date": last_refresh_date}
    result = refresh_financial_calendar(today, default_end_date(today), model, db_path)
    return {"refreshed": True, "last_refresh_date": today.isoformat(), "refresh_result": result}


def upsert_financial_events(conn: sqlite3.Connection, events: list[dict[str, Any]]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for event in events:
        unique_key = build_event_unique_key(event)
        values = (
            event["id"], event["date"], event["title"], event["type"], event["importance"],
            event.get("detail", ""), event.get("country", ""), event.get("time", ""),
            _db_value(event.get("forecast")), _db_value(event.get("consensus")),
            _db_value(event.get("previous")), _db_value(event.get("actual")),
            event.get("aiComment", ""), event.get("expectedImpact", ""),
            event.get("source_name", ""), event.get("source_url", ""),
            event.get("source_provider", ""), event.get("source_id", ""), event.get("ticker", ""),
            json.dumps(event.get("raw_payload"), ensure_ascii=False) if event.get("raw_payload") else None,
            ANALYSIS_VERSION if event.get("aiComment") else None, unique_key, now, now,
        )
        conn.execute("""
            INSERT INTO events (
                event_uid, date, title, category, importance, detail, country, time,
                forecast, consensus, previous, actual, ai_comment, expected_impact,
                source_name, source_url, source_provider, source_id, ticker, raw_payload,
                analysis_version, unique_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unique_key) DO UPDATE SET
                event_uid=excluded.event_uid, title=excluded.title, category=excluded.category,
                importance=excluded.importance, detail=excluded.detail, country=excluded.country,
                time=excluded.time, forecast=excluded.forecast, consensus=excluded.consensus,
                previous=excluded.previous, actual=excluded.actual,
                ai_comment=CASE WHEN excluded.ai_comment != '' THEN excluded.ai_comment ELSE events.ai_comment END,
                expected_impact=CASE WHEN excluded.expected_impact != '' THEN excluded.expected_impact ELSE events.expected_impact END,
                source_name=excluded.source_name, source_url=excluded.source_url,
                source_provider=excluded.source_provider, source_id=excluded.source_id,
                ticker=excluded.ticker, raw_payload=excluded.raw_payload,
                analysis_version=COALESCE(excluded.analysis_version, events.analysis_version),
                updated_at=excluded.updated_at
        """, values)


def analyze_financial_events(events: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise FinancialCalendarError("OPENAI_API_KEY is not set; structured events were saved without AI analysis.")
    client = get_openai_client_class()(api_key=api_key)
    analyses: dict[str, dict[str, Any]] = {}
    batch_size = max(DEFAULT_ANALYSIS_BATCH_SIZE, 1)
    for offset in range(0, len(events), batch_size):
        compact = [{key: event.get(key) for key in (
            "id", "date", "title", "type", "country", "forecast", "consensus", "previous", "actual", "detail"
        )} for event in events[offset:offset + batch_size]]
        response = client.responses.create(
        model=model, store=False, timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        input=(
            "다음은 공식/정형 공급자에서 수집한 금융 이벤트다. 사실 필드를 수정하거나 새 사실을 만들지 말고, "
            "한국 주식시장 투자자 관점에서 각 이벤트의 중요도, 한 줄 코멘트, 예상 영향을 한국어로 작성하라. "
            "컨센서스가 없으면 없는 수치를 추측하지 말라.\n\n" + json.dumps(compact, ensure_ascii=False)
        ),
        text={"format": {"type": "json_schema", "name": "financial_event_analysis",
                         "strict": True, "schema": _analysis_schema()}},
        )
        if not response.output_text:
            raise FinancialCalendarError("OpenAI returned an empty event analysis response.")
        analyses.update({item["id"]: item for item in json.loads(response.output_text).get("analyses", [])})
    for event in events:
        analysis = analyses.get(event["id"])
        if analysis:
            event["importance"] = analysis["importance"]
            event["aiComment"] = analysis["aiComment"].strip()
            event["expectedImpact"] = analysis["expectedImpact"].strip()
    return events


def normalize_calendar_events(raw_events: Any, start_date: date, end_date: date) -> list[dict[str, Any]]:
    if not isinstance(raw_events, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_events:
        if not isinstance(raw, dict):
            continue
        event_date = parse_event_date(raw.get("date"))
        if event_date is None or not (start_date <= event_date <= end_date):
            continue
        event = {
            "id": str(raw.get("id", "")).strip(), "date": event_date.isoformat(),
            "title": str(raw.get("title", "")).strip(),
            "type": _legacy_type(str(raw.get("type") or raw.get("category") or "macro")),
            "country": str(raw.get("country", "")).strip(), "time": str(raw.get("time", "")).strip(),
            "importance": _choice(raw.get("importance"), IMPORTANCE_LEVELS, "medium"),
            "forecast": raw.get("forecast"), "consensus": raw.get("consensus"),
            "previous": raw.get("previous"), "actual": raw.get("actual"),
            "detail": str(raw.get("detail", "")).strip(),
            "aiComment": str(raw.get("aiComment", "")).strip(),
            "expectedImpact": str(raw.get("expectedImpact", "")).strip(),
            "source_name": str(raw.get("source_name", "")).strip(),
            "source_url": str(raw.get("source_url", "")).strip(),
            "source_provider": str(raw.get("source_provider", "")).strip(),
            "source_id": str(raw.get("source_id", "")).strip(),
            "ticker": str(raw.get("ticker", "")).strip(), "raw_payload": raw.get("raw_payload"),
        }
        if not event["id"] or not event["title"]:
            continue
        key = build_event_unique_key(event)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(event)
    normalized.sort(key=lambda item: (
        item["date"], IMPORTANCE_LEVELS.index(item["importance"]), item["title"]
    ))
    return normalized


def build_event_unique_key(event: dict[str, Any]) -> str:
    provider = str(event.get("source_provider", "")).strip().lower()
    source_id = str(event.get("source_id", "")).strip().lower()
    if provider and source_id:
        return f"{provider}|{source_id}"
    return "|".join((
        str(event.get("date", "")), str(event.get("type", "")),
        str(event.get("title", "")).lower(),
    ))


def parse_event_date(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def _analysis_schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "properties": {"analyses": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "importance": {"type": "string", "enum": list(IMPORTANCE_LEVELS)},
                "aiComment": {"type": "string"}, "expectedImpact": {"type": "string"},
            },
            "required": ["id", "importance", "aiComment", "expectedImpact"],
        }}},
        "required": ["analyses"],
    }


def _api_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["event_uid"] or f"evt-legacy-{row['legacy_id']}",
        "date": row["date"], "title": row["title"],
        "type": row["category"], "country": row["country"] or "", "time": row["time"] or "",
        "importance": row["importance"], "forecast": row["forecast"], "consensus": row["consensus"],
        "previous": row["previous"], "actual": row["actual"], "detail": row["detail"] or "",
        "aiComment": row["ai_comment"] or "", "expectedImpact": row["expected_impact"] or "",
        "source_name": row["source_name"] or "", "source_url": row["source_url"] or "",
        "ticker": row["ticker"] or "",
    }


def _legacy_type(value: str) -> str:
    normalized = value.strip().lower()
    return {
        "rate": "policy", "economic_indicator": "macro", "earning": "earnings",
        "auction": "policy", "other": "macro",
    }.get(normalized, normalized)


def _choice(value: Any, allowed: tuple[str, ...], fallback: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else fallback


def _db_value(value: Any) -> Optional[str]:
    return None if value is None else str(value)
