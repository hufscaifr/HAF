from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

from ai_research_department.config import load_backend_env
from cam_pipeline.krx_listings import (
    KrxListingsError,
    connect_krx_listings_db,
    init_krx_listings_db,
    lookup_krx_listing,
    normalize_ticker,
    refresh_krx_listings,
)


class ResolvedCompany(BaseModel):
    """Company identity resolved from a user-provided name or ticker."""

    company: str
    ticker: str
    market: str
    source: str


class CompanyResolutionError(RuntimeError):
    """Raised when a company name cannot be mapped to a listed company."""


def resolve_company(
    company: str,
    ticker: str | None = None,
    market: str | None = None,
    refresh_if_missing: bool = True,
) -> ResolvedCompany:
    """Resolve Korean listed company name/ticker/market using KRX listings."""
    load_backend_env()
    normalized_ticker = normalize_ticker(ticker) if ticker else ""
    if normalized_ticker:
        listing = lookup_krx_listing(normalized_ticker)
        return ResolvedCompany(
            company=str(listing.get("title") if listing else company).strip() or company,
            ticker=normalized_ticker,
            market=str((listing or {}).get("market") or market or "KOSPI").strip().upper(),
            source="krx_listing" if listing else "request",
        )

    listing = find_listing_by_company_name(company)
    if listing is None:
        listing = find_listing_with_finance_datareader(company)
    if listing is None:
        listing = find_listing_with_dart_cache(company, market=market)
    if listing is None and refresh_if_missing:
        try:
            refresh_krx_listings()
            listing = find_listing_by_company_name(company)
        except (KrxListingsError, Exception) as exc:
            raise CompanyResolutionError(
                "기업명으로 종목을 찾으려면 KRX listings DB가 필요합니다. "
                "FinanceDataReader fallback도 실패했고 KRX_AUTH_KEY로 갱신하지 못했습니다."
            ) from exc

    if listing is None:
        raise CompanyResolutionError(f"KRX listings에서 기업명을 찾지 못했습니다: {company}")

    return ResolvedCompany(
        company=str(listing["title"]),
        ticker=str(listing["ticker"]),
        market=str(listing["market"]).upper(),
        source="krx_listing",
    )


def find_listing_by_company_name(company: str, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Find a KRX listing by exact or partial Korean company name."""
    name = str(company or "").strip()
    if not name:
        return None
    try:
        with connect_krx_listings_db(db_path) as conn:
            init_krx_listings_db(conn)
            exact = conn.execute(
                """
                SELECT ticker, title, market, market_code, updated_at
                FROM krx_listings
                WHERE title = ?
                LIMIT 1
                """,
                (name,),
            ).fetchone()
            if exact:
                return dict(exact)
            partial = conn.execute(
                """
                SELECT ticker, title, market, market_code, updated_at
                FROM krx_listings
                WHERE title LIKE ?
                ORDER BY LENGTH(title) ASC, market ASC
                LIMIT 1
                """,
                (f"%{name}%",),
            ).fetchone()
            return dict(partial) if partial else None
    except sqlite3.Error:
        return None


def find_listing_with_finance_datareader(company: str) -> Optional[dict[str, Any]]:
    """Resolve a Korean company name through FinanceDataReader's KRX listing."""
    try:
        import FinanceDataReader as fdr

        listings = fdr.StockListing("KRX")
    except Exception:
        return None


def find_listing_with_dart_cache(company: str, market: str | None = None) -> Optional[dict[str, Any]]:
    """Resolve company from the cached OpenDART corp code file if present."""
    cache_path = Path(__file__).resolve().parents[2] / ".cache" / "dart_corp_codes.json"
    if not cache_path.is_file():
        return None
    name = str(company or "").strip()
    if not name:
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for ticker, profile in payload.items():
        corp_name = str(profile.get("corp_name", "")).strip()
        if corp_name == name:
            return {
                "ticker": normalize_ticker(ticker),
                "title": corp_name,
                "market": str(market or "KOSPI").upper(),
                "market_code": "",
                "updated_at": "",
            }
    for ticker, profile in payload.items():
        corp_name = str(profile.get("corp_name", "")).strip()
        if name in corp_name:
            return {
                "ticker": normalize_ticker(ticker),
                "title": corp_name,
                "market": str(market or "KOSPI").upper(),
                "market_code": "",
                "updated_at": "",
            }
    return None

    name = str(company or "").strip()
    if not name:
        return None
    try:
        exact = listings[listings["Name"] == name]
        if exact.empty:
            exact = listings[listings["Name"].astype(str).str.contains(name, regex=False, na=False)]
        if exact.empty:
            return None
        row = exact.iloc[0].to_dict()
        market = str(row.get("Market") or row.get("MarketId") or "KOSPI").upper()
        if "KOSDAQ" not in market:
            market = "KOSPI"
        return {
            "ticker": normalize_ticker(row.get("Code") or row.get("Symbol")),
            "title": str(row.get("Name") or name),
            "market": market,
            "market_code": str(row.get("MarketId") or ""),
            "updated_at": "",
        }
    except Exception:
        return None
