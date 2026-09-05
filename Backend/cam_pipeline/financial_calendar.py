from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from cam_pipeline.company_selector import (
    DEFAULT_OPENAI_MODEL,
    LLMConfigurationError,
    get_openai_client_class,
    normalize_env_api_key,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FINANCIAL_CALENDAR_DB_PATH = PROJECT_ROOT / "financial_calendar.db"
DEFAULT_FINANCIAL_CALENDAR_MODEL = os.getenv(
    "OPENAI_FINANCIAL_CALENDAR_MODEL",
    DEFAULT_OPENAI_MODEL,
)
DEFAULT_FINANCIAL_CALENDAR_TIMEZONE = os.getenv("CAM_TIMEZONE", "Asia/Seoul")
DEFAULT_LOOKAHEAD_DAYS = int(os.getenv("CAM_FINANCIAL_CALENDAR_LOOKAHEAD_DAYS", "45"))
DEFAULT_REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("OPENAI_FINANCIAL_CALENDAR_TIMEOUT_SECONDS", "90")
)
PROMPT_VERSION = "financial_calendar_events_v1"
DEFAULT_ALLOWED_DOMAINS = (
    "federalreserve.gov",
    "newyorkfed.org",
    "kansascityfed.org",
    "bok.or.kr",
    "bls.gov",
    "bea.gov",
    "census.gov",
    "ismworld.org",
    "kostat.go.kr",
    "krx.co.kr",
    "kind.krx.co.kr",
    "dart.fss.or.kr",
    "opendart.fss.or.kr",
    "finance.yahoo.com",
    "nasdaq.com",
    "investor.nvidia.com",
    "samsung.com",
    "skhynix.com",
    "apple.com",
    "microsoft.com",
    "tesla.com",
)
DEFAULT_SEARCH_CONTEXT_SIZE = os.getenv(
    "OPENAI_FINANCIAL_CALENDAR_SEARCH_CONTEXT_SIZE",
    "low",
)

EVENT_CATEGORIES = (
    "rate",
    "economic_indicator",
    "earning",
    "policy",
    "market_holiday",
    "auction",
    "other",
)
IMPORTANCE_LEVELS = ("high", "medium", "low")


class FinancialCalendarError(RuntimeError):
    """Raised when financial calendar refresh or storage fails."""


def get_financial_calendar_db_path() -> Path:
    configured = os.getenv("CAM_FINANCIAL_CALENDAR_DB")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_FINANCIAL_CALENDAR_DB_PATH


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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            importance TEXT NOT NULL,
            detail TEXT,
            country TEXT,
            source_name TEXT,
            source_url TEXT,
            unique_key TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique_key
        ON events(unique_key)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_date
        ON events(date)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calendar_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    ensure_calendar_columns(conn)
    conn.commit()


def ensure_calendar_columns(conn: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(events)").fetchall()
    }
    column_defs = {
        "country": "TEXT",
        "source_name": "TEXT",
        "source_url": "TEXT",
        "unique_key": "TEXT",
        "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }
    for column, definition in column_defs.items():
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE events ADD COLUMN {column} {definition}")


def get_metadata(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM calendar_metadata WHERE key = ?",
        (key,),
    ).fetchone()
    return str(row["value"]) if row else None


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn.execute(
        """
        INSERT INTO calendar_metadata (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, value, now),
    )


def list_financial_events(
    start_date: date,
    end_date: date,
    category: Optional[str] = None,
    importance: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    with connect_calendar_db(db_path) as conn:
        init_financial_calendar_db(conn)
        query = """
            SELECT id, date, title, category, importance, detail, country, source_name, source_url, updated_at
            FROM events
            WHERE date BETWEEN ? AND ?
        """
        params: list[Any] = [start_date.isoformat(), end_date.isoformat()]
        if category:
            query += " AND category = ?"
            params.append(category)
        if importance:
            query += " AND importance = ?"
            params.append(importance)
        query += " ORDER BY date ASC, importance_rank ASC, title ASC"

        wrapped_query = query.replace(
            "importance_rank",
            "CASE importance WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END",
        )
        rows = conn.execute(wrapped_query, params).fetchall()
        return [dict(row) for row in rows]


def refresh_financial_calendar(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    model: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    today = get_today()
    start = start_date or today
    end = end_date or default_end_date(start)
    if end < start:
        raise FinancialCalendarError("end_date must be greater than or equal to start_date.")

    chosen_model = model or DEFAULT_FINANCIAL_CALENDAR_MODEL
    payload = collect_financial_calendar_events(
        start_date=start,
        end_date=end,
        model=chosen_model,
    )
    events = normalize_calendar_events(payload.get("events", []), start, end)

    with connect_calendar_db(db_path) as conn:
        init_financial_calendar_db(conn)
        upsert_financial_events(conn, events)
        set_metadata(conn, "last_refresh_date", today.isoformat())
        set_metadata(conn, "last_refresh_start_date", start.isoformat())
        set_metadata(conn, "last_refresh_end_date", end.isoformat())
        set_metadata(conn, "last_refresh_model", chosen_model)
        set_metadata(conn, "prompt_version", PROMPT_VERSION)
        conn.commit()

    return {
        "status": "success",
        "model": chosen_model,
        "prompt_version": PROMPT_VERSION,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "inserted_or_updated": len(events),
        "events": events,
    }


def ensure_financial_calendar_current(
    model: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    today = get_today()
    with connect_calendar_db(db_path) as conn:
        init_financial_calendar_db(conn)
        last_refresh_date = get_metadata(conn, "last_refresh_date")

    if last_refresh_date == today.isoformat():
        return {
            "refreshed": False,
            "last_refresh_date": last_refresh_date,
        }

    result = refresh_financial_calendar(
        start_date=today,
        end_date=default_end_date(today),
        model=model,
        db_path=db_path,
    )
    return {
        "refreshed": True,
        "last_refresh_date": today.isoformat(),
        "refresh_result": result,
    }


def upsert_financial_events(conn: sqlite3.Connection, events: list[dict[str, Any]]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for event in events:
        unique_key = build_event_unique_key(event)
        conn.execute(
            """
            INSERT INTO events (
                date, title, category, importance, detail, country,
                source_name, source_url, unique_key, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unique_key) DO UPDATE SET
                title = excluded.title,
                category = excluded.category,
                importance = excluded.importance,
                detail = excluded.detail,
                country = excluded.country,
                source_name = excluded.source_name,
                source_url = excluded.source_url,
                updated_at = excluded.updated_at
            """,
            (
                event["date"],
                event["title"],
                event["category"],
                event["importance"],
                event.get("detail", ""),
                event.get("country", ""),
                event.get("source_name", ""),
                event.get("source_url", ""),
                unique_key,
                now,
                now,
            ),
        )


def build_event_unique_key(event: dict[str, Any]) -> str:
    return "|".join(
        [
            str(event.get("date", "")).strip(),
            str(event.get("category", "")).strip().lower(),
            str(event.get("title", "")).strip().lower(),
        ]
    )


def collect_financial_calendar_events(
    start_date: date,
    end_date: date,
    model: str,
) -> dict[str, Any]:
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not set.")

    client = get_openai_client_class()(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=build_financial_calendar_prompt(start_date, end_date),
        store=False,
        tools=[build_financial_calendar_web_search_tool()],
        text={
            "format": {
                "type": "json_schema",
                "name": "financial_calendar_events",
                "strict": True,
                "schema": build_financial_calendar_schema(),
            }
        },
        timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
    )

    if not response.output_text:
        raise FinancialCalendarError("OpenAI returned an empty financial calendar response.")

    return json.loads(response.output_text)


def build_financial_calendar_web_search_tool() -> dict[str, Any]:
    return {
        "type": "web_search",
        "filters": {
            "allowed_domains": list(get_allowed_domains()),
        },
        "search_context_size": normalize_search_context_size(
            DEFAULT_SEARCH_CONTEXT_SIZE
        ),
    }


def get_allowed_domains() -> tuple[str, ...]:
    configured = os.getenv("OPENAI_FINANCIAL_CALENDAR_ALLOWED_DOMAINS", "").strip()
    if not configured:
        return DEFAULT_ALLOWED_DOMAINS
    domains = tuple(
        normalize_domain(domain)
        for domain in configured.split(",")
        if normalize_domain(domain)
    )
    return domains or DEFAULT_ALLOWED_DOMAINS


def normalize_domain(value: str) -> str:
    domain = value.strip().lower()
    domain = domain.removeprefix("https://").removeprefix("http://")
    return domain.strip("/")


def normalize_search_context_size(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    return "low"


def build_financial_calendar_prompt(start_date: date, end_date: date) -> str:
    window_days = max((end_date - start_date).days + 1, 1)
    max_events = max(8, round(window_days / 45 * 25))
    return f"""
You are building a financial-market calendar for Korean retail and professional investors.

Collect important scheduled financial events from {start_date.isoformat()} through {end_date.isoformat()}, inclusive.
Use web search only to verify dates from the allowed source domains. Do not broaden the search to fill the calendar.

Editorial standard:
- The calendar is for Korean investors who track KOSPI/KOSDAQ market impact.
- Do not collect every possible financial event.
- Include only events with medium or high market relevance for Korean equities, rates, FX, or major global risk assets.
- If no reliable scheduled events exist in the window, return an empty `events` array.
- Do not keep searching to satisfy a minimum count.

Always include when available:
- US FOMC decisions and major Fed policy events.
- Korea Bank of Korea monetary policy decisions.
- US CPI, PCE, nonfarm payrolls/jobs, GDP, retail sales, ISM PMI, and other clearly market-moving indicators.
- Korea CPI, GDP, exports/imports, industrial activity, employment, and other clearly market-moving indicators.
- Korea and US stock-market holidays only when they affect trading.
- Earnings events for large market-moving companies relevant to Korean equities, especially Samsung Electronics, SK Hynix, NVIDIA, Apple, Microsoft, Tesla, major AI infrastructure, semiconductors, batteries, autos, platforms, and banks.

Include selectively only if likely market-moving:
- ECB/BOJ or other major central-bank events.
- US Treasury auctions.
- Jackson Hole, OPEC+, G20, or similar global policy events.

Exclude:
- Low-relevance regional statistics.
- Small-cap earnings with limited market impact.
- Rumored or unsourced expected dates.
- Events with no exact or reliably expected date.
- Duplicate events with slightly different names.

Rules:
- Return Korean text.
- Prefer exact calendar dates. If a company earnings date is estimated, keep the date only when a reliable calendar marks it as expected and include "예상" in detail.
- Do not invent dates. If the date is not available, omit the event.
- Return at most {max_events} events for this collection window.
- `category` must be one of: {", ".join(EVENT_CATEGORIES)}.
- `importance` must be one of: {", ".join(IMPORTANCE_LEVELS)}.
- Use `low` only for events that are still worth showing. Omit truly low-value events.
- `date` must be YYYY-MM-DD.
- `title` should be short enough for a calendar card.
- `detail` should explain why the event matters in one Korean sentence.
- `country` should be "US", "KR", "Global", or another concise country/region label.
- Include one source name and one source URL when available. Use an empty string only if no stable source URL is available.

Return only JSON matching the schema.
""".strip()


def build_financial_calendar_schema() -> dict[str, Any]:
    event_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "date": {"type": "string"},
            "title": {"type": "string"},
            "category": {"type": "string", "enum": list(EVENT_CATEGORIES)},
            "importance": {"type": "string", "enum": list(IMPORTANCE_LEVELS)},
            "detail": {"type": "string"},
            "country": {"type": "string"},
            "source_name": {"type": "string"},
            "source_url": {"type": "string"},
        },
        "required": [
            "date",
            "title",
            "category",
            "importance",
            "detail",
            "country",
            "source_name",
            "source_url",
        ],
    }

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "events": {
                "type": "array",
                "items": event_schema,
            },
        },
        "required": ["events"],
    }


def normalize_calendar_events(
    raw_events: Any,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    if not isinstance(raw_events, list):
        return []

    normalized_events: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            continue
        event_date = parse_event_date(raw_event.get("date"))
        if event_date is None or event_date < start_date or event_date > end_date:
            continue

        category = normalize_choice(raw_event.get("category"), EVENT_CATEGORIES, "other")
        importance = normalize_choice(raw_event.get("importance"), IMPORTANCE_LEVELS, "medium")
        event = {
            "date": event_date.isoformat(),
            "title": str(raw_event.get("title", "")).strip(),
            "category": category,
            "importance": importance,
            "detail": str(raw_event.get("detail", "")).strip(),
            "country": str(raw_event.get("country", "")).strip(),
            "source_name": str(raw_event.get("source_name", "")).strip(),
            "source_url": str(raw_event.get("source_url", "")).strip(),
        }
        if not event["title"]:
            continue
        key = build_event_unique_key(event)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        normalized_events.append(event)

    normalized_events.sort(
        key=lambda event: (
            event["date"],
            IMPORTANCE_LEVELS.index(event["importance"]),
            event["title"],
        )
    )
    return normalized_events


def parse_event_date(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def normalize_choice(value: Any, allowed_values: tuple[str, ...], fallback: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in allowed_values:
        return normalized
    return fallback
