from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KRX_LISTINGS_DB_PATH = PROJECT_ROOT / "krx_listings.db"
DEFAULT_KRX_API_BASE_URL = os.getenv(
    "KRX_API_BASE_URL",
    "https://data-dbg.krx.co.kr/svc/apis",
).rstrip("/")
DEFAULT_KRX_TIMEOUT_SECONDS = float(os.getenv("KRX_TIMEOUT_SECONDS", "30"))
KRX_ENDPOINTS = {
    "KOSPI": os.getenv("KRX_KOSPI_BASE_INFO_PATH", "/sto/stk_isu_base_info"),
    "KOSDAQ": os.getenv("KRX_KOSDAQ_BASE_INFO_PATH", "/sto/ksq_isu_base_info"),
}


class KrxListingsError(RuntimeError):
    """Raised when KRX listing synchronization fails."""


def get_krx_listings_db_path() -> Path:
    configured = os.getenv("CAM_KRX_LISTINGS_DB")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_KRX_LISTINGS_DB_PATH


def connect_krx_listings_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_krx_listings_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_krx_listings_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS krx_listings (
            ticker TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            market TEXT NOT NULL,
            market_code TEXT,
            raw_payload TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_krx_listings_market
        ON krx_listings(market)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS krx_listings_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_krx_auth_key() -> str:
    auth_key = str(os.getenv("KRX_AUTH_KEY") or "").strip().strip('"').strip("'")
    if not auth_key:
        raise KrxListingsError("KRX_AUTH_KEY is not set.")
    return auth_key


def normalize_ticker(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits.zfill(6) if digits else ""


def normalize_market(value: Any) -> str:
    text = str(value or "").strip().upper()
    if "KOSDAQ" in text or "코스닥" in text:
        return "KOSDAQ"
    if "KOSPI" in text or "유가" in text or "코스피" in text:
        return "KOSPI"
    return text


def build_krx_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{DEFAULT_KRX_API_BASE_URL}/{path.lstrip('/')}"


def fetch_krx_listing_rows(market: str, bas_dd: Optional[str] = None) -> list[dict[str, Any]]:
    normalized_market = normalize_market(market)
    endpoint = KRX_ENDPOINTS.get(normalized_market)
    if not endpoint:
        raise KrxListingsError(f"Unsupported KRX market: {market}")

    params: dict[str, str] = {}
    if bas_dd:
        params["basDd"] = bas_dd

    response = requests.get(
        build_krx_url(endpoint),
        headers={"AUTH_KEY": get_krx_auth_key()},
        params=params,
        timeout=DEFAULT_KRX_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    rows = extract_rows(payload)
    if not rows:
        raise KrxListingsError(f"KRX returned no rows for {normalized_market}.")
    return rows


def extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("OutBlock_1", "output", "data", "items", "list"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            nested = extract_rows(value)
            if nested:
                return nested
    return []


def parse_listing_row(row: dict[str, Any], fallback_market: str) -> Optional[dict[str, Any]]:
    ticker = first_value(
        row,
        "ISU_SRT_CD",
        "isuSrtCd",
        "short_code",
        "ticker",
        "code",
        "종목코드",
    )
    title = first_value(
        row,
        "ISU_ABBRV",
        "isuAbrv",
        "ISU_NM",
        "isuNm",
        "KOR_CORP_NM",
        "korCorpNm",
        "stockNameKr",
        "name",
        "title",
        "종목명",
        "한글 종목약명",
    )
    market = first_value(
        row,
        "MKT_NM",
        "mktNm",
        "market",
        "시장구분",
    )
    market_code = first_value(row, "MKT_TP_CD", "mktTpCd", "market_code")

    normalized_ticker = normalize_ticker(ticker)
    normalized_title = str(title or "").strip()
    normalized_market = normalize_market(market) or fallback_market
    if not normalized_ticker or not normalized_title:
        return None

    return {
        "ticker": normalized_ticker,
        "title": normalized_title,
        "market": normalized_market,
        "market_code": str(market_code or "").strip(),
        "raw_payload": row,
    }


def first_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def refresh_krx_listings(
    bas_dd: Optional[str] = None,
    markets: tuple[str, ...] = ("KOSPI", "KOSDAQ"),
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    resolved_bas_dd = bas_dd or resolve_latest_krx_base_date(markets=markets)
    listings: list[dict[str, Any]] = []
    counts: dict[str, int] = {}

    for market in markets:
        normalized_market = normalize_market(market)
        rows = fetch_krx_listing_rows(normalized_market, bas_dd=resolved_bas_dd)
        parsed = [
            listing
            for listing in (
                parse_listing_row(row, normalized_market)
                for row in rows
            )
            if listing
        ]
        listings.extend(parsed)
        counts[normalized_market] = len(parsed)

    with connect_krx_listings_db(db_path) as conn:
        init_krx_listings_db(conn)
        for listing in listings:
            conn.execute(
                """
                INSERT INTO krx_listings (
                    ticker, title, market, market_code, raw_payload,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    title = excluded.title,
                    market = excluded.market,
                    market_code = excluded.market_code,
                    raw_payload = excluded.raw_payload,
                    updated_at = excluded.updated_at
                """,
                (
                    listing["ticker"],
                    listing["title"],
                    listing["market"],
                    listing["market_code"],
                    json_dumps(listing["raw_payload"]),
                    now,
                    now,
                ),
            )
        set_metadata(conn, "last_refresh_at", now)
        set_metadata(conn, "last_refresh_bas_dd", resolved_bas_dd or "")
        set_metadata(conn, "last_refresh_total", str(len(listings)))
        conn.commit()

    return {
        "status": "success",
        "bas_dd": resolved_bas_dd,
        "total": len(listings),
        "counts": counts,
    }


def resolve_latest_krx_base_date(
    markets: tuple[str, ...] = ("KOSPI", "KOSDAQ"),
    lookback_days: int = 10,
) -> str:
    """Find the latest base date that returns KRX listing rows."""
    today = datetime.now().date()
    for offset in range(lookback_days + 1):
        candidate = today - timedelta(days=offset)
        bas_dd = candidate.strftime("%Y%m%d")
        try:
            fetch_krx_listing_rows(markets[0], bas_dd=bas_dd)
            return bas_dd
        except (KrxListingsError, requests.RequestException):
            continue
    raise KrxListingsError(
        f"최근 {lookback_days}일 내 KRX 종목기본정보 기준일자를 찾지 못했습니다."
    )


def lookup_krx_listing(ticker: Any, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    normalized_ticker = normalize_ticker(ticker)
    if not normalized_ticker:
        return None

    try:
        with connect_krx_listings_db(db_path) as conn:
            init_krx_listings_db(conn)
            row = conn.execute(
                """
                SELECT ticker, title, market, market_code, updated_at
                FROM krx_listings
                WHERE ticker = ?
                """,
                (normalized_ticker,),
            ).fetchone()
    except sqlite3.Error:
        return None

    return dict(row) if row else None


def list_krx_listings(
    market: Optional[str] = None,
    limit: int = 50,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    normalized_market = normalize_market(market) if market else None
    safe_limit = max(1, min(int(limit or 50), 500))

    with connect_krx_listings_db(db_path) as conn:
        init_krx_listings_db(conn)
        if normalized_market:
            rows = conn.execute(
                """
                SELECT ticker, title, market, market_code, updated_at
                FROM krx_listings
                WHERE market = ?
                ORDER BY market ASC, ticker ASC
                LIMIT ?
                """,
                (normalized_market, safe_limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ticker, title, market, market_code, updated_at
                FROM krx_listings
                ORDER BY market ASC, ticker ASC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [dict(row) for row in rows]


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn.execute(
        """
        INSERT INTO krx_listings_metadata (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, value, now),
    )


def json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True)
