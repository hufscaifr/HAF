from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is included in requirements.txt
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")


REQUEST_TIMEOUT = float(os.getenv("CAM_CALENDAR_HTTP_TIMEOUT_SECONDS", "20"))
USER_AGENT = "CAM-Financial-Calendar/1.0"
DEFAULT_EARNINGS_TICKERS = (
    "005930.KS", "000660.KS", "AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META"
)
FRED_MAJOR_RELEASES = (
    "consumer price index",
    "employment situation",
    "gross domestic product",
    "personal income and outlays",
    "producer price index",
    "advance monthly sales for retail and food services",
    "industrial production and capacity utilization",
    "u.s. international trade in goods and services",
    "job openings and labor turnover survey",
    "new residential construction",
    "manufacturing and trade inventories and sales",
)


@dataclass
class ProviderResult:
    provider: str
    status: str
    events: list[dict[str, Any]]
    message: str = ""


def collect_structured_events(
    start_date: date,
    end_date: date,
    providers: Optional[list[str]] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry: dict[str, Callable[[date, date], ProviderResult]] = {
        "fred": collect_fred_release_dates,
        "fomc": collect_fomc_schedule,
        "dart": collect_dart_disclosures,
        "yfinance": collect_yfinance_earnings,
        "ecos": collect_ecos_calendar,
    }
    selected = providers or list(registry)
    events: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for name in selected:
        collector = registry.get(name)
        if collector is None:
            reports.append({"provider": name, "status": "error", "count": 0, "message": "Unknown provider"})
            continue
        try:
            result = collector(start_date, end_date)
        except Exception as exc:
            result = ProviderResult(name, "error", [], str(exc))
        events.extend(result.events)
        reports.append(
            {"provider": result.provider, "status": result.status, "count": len(result.events), "message": result.message}
        )
    return events, reports


def collect_fred_release_dates(start_date: date, end_date: date) -> ProviderResult:
    api_key = os.getenv("FRED_API_KEY", "").strip()
    if not api_key:
        return ProviderResult("fred", "skipped", [], "FRED_API_KEY is not set")
    events = []
    offset = 0
    while offset < 20_000:
        response = requests.get(
            "https://api.stlouisfed.org/fred/releases/dates",
            params={
                "api_key": api_key, "file_type": "json",
                "realtime_start": start_date.isoformat(), "realtime_end": end_date.isoformat(),
                "include_release_dates_with_no_data": "true", "limit": 1000, "offset": offset,
                "order_by": "release_date", "sort_order": "desc",
            },
            headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("release_dates", [])
        if not rows:
            break
        for item in rows:
            event_date = str(item.get("date", ""))[:10]
            title = str(item.get("release_name", "")).strip()
            if not _in_range(event_date, start_date, end_date) or not _is_major_fred_release(title):
                continue
            release_id = str(item.get("release_id", ""))
            events.append(_event(
                source="fred", source_id=f"{release_id}:{event_date}", event_date=event_date,
                title=title, event_type="macro", country="US",
                importance=_fred_importance(title),
                detail="FRED가 제공하는 미국 주요 경제지표 공식 발표 일정입니다.",
                source_name="Federal Reserve Bank of St. Louis (FRED)",
                source_url=f"https://fred.stlouisfed.org/releases/calendar?rid={release_id}",
            ))
        oldest_date = str(rows[-1].get("date", ""))[:10]
        if oldest_date and oldest_date < start_date.isoformat():
            break
        offset += len(rows)
        if offset >= int(payload.get("count", 0) or 0):
            break
    return ProviderResult("fred", "success", events)


def collect_fomc_schedule(start_date: date, end_date: date) -> ProviderResult:
    response = requests.get(
        "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    events: list[dict[str, Any]] = []
    for panel in soup.select(".panel.panel-default"):
        heading = panel.select_one(".panel-heading")
        year_match = re.search(r"20\d{2}", heading.get_text(" ", strip=True) if heading else "")
        if not year_match:
            continue
        year = int(year_match.group())
        for row in panel.select(".row.fomc-meeting"):
            month_node = row.select_one(".fomc-meeting__month")
            date_node = row.select_one(".fomc-meeting__date")
            if not month_node or not date_node:
                continue
            parsed = _parse_fomc_date(year, month_node.get_text(" ", strip=True), date_node.get_text(" ", strip=True))
            if parsed is None:
                continue
            announced_at = datetime(parsed.year, parsed.month, parsed.day, 14, 0, tzinfo=ZoneInfo("America/New_York"))
            announced_at_kst = announced_at.astimezone(ZoneInfo("Asia/Seoul"))
            if not (start_date <= announced_at_kst.date() <= end_date):
                continue
            events.append(_event(
                source="fomc", source_id=parsed.isoformat(), event_date=announced_at_kst.date().isoformat(),
                title="FOMC Rate Decision", event_type="policy", country="US", importance="high",
                time=announced_at_kst.strftime("%H:%M KST"),
                detail="미 연준의 기준금리 결정과 성명 발표 일정입니다.",
                source_name="Federal Reserve",
                source_url="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            ))
    return ProviderResult("fomc", "success", events)


def collect_dart_disclosures(start_date: date, end_date: date) -> ProviderResult:
    api_key = os.getenv("DART_API_KEY", "").strip()
    if not api_key:
        return ProviderResult("dart", "skipped", [], "DART_API_KEY is not set")
    events: list[dict[str, Any]] = []
    page_no = 1
    while page_no <= 10:
        response = requests.get(
            "https://opendart.fss.or.kr/api/list.json",
            params={"crtfc_key": api_key, "bgn_de": start_date.strftime("%Y%m%d"),
                    "end_de": end_date.strftime("%Y%m%d"), "page_no": page_no, "page_count": 100},
            headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") == "013":
            break
        if payload.get("status") != "000":
            raise RuntimeError(f"OpenDART: {payload.get('message', 'unknown error')}")
        for item in payload.get("list", []):
            event_date = _compact_date(item.get("rcept_dt"))
            report_name = str(item.get("report_nm", "")).strip()
            corp_name = str(item.get("corp_name", "")).strip()
            receipt_no = str(item.get("rcept_no", "")).strip()
            if not event_date or not report_name:
                continue
            events.append(_event(
                source="dart", source_id=receipt_no, event_date=event_date,
                title=f"{corp_name} {report_name}", event_type="disclosure", country="KR",
                importance=_dart_importance(report_name), ticker=str(item.get("stock_code", "")).strip(),
                detail=f"{corp_name}이 제출한 {report_name} 공시입니다.", source_name="OpenDART",
                source_url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
            ))
        total_pages = int(payload.get("total_page", 1) or 1)
        if page_no >= total_pages:
            break
        page_no += 1
    return ProviderResult("dart", "success", events)


def collect_yfinance_earnings(start_date: date, end_date: date) -> ProviderResult:
    try:
        import yfinance as yf
    except ImportError:
        return ProviderResult("yfinance", "skipped", [], "yfinance is not installed")
    configured = os.getenv("CAM_CALENDAR_EARNINGS_TICKERS", "")
    tickers = [value.strip() for value in configured.split(",") if value.strip()] or list(DEFAULT_EARNINGS_TICKERS)
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for symbol in tickers:
        try:
            frame = yf.Ticker(symbol).get_earnings_dates(limit=12)
            if frame is None or frame.empty:
                continue
            for timestamp, row in frame.iterrows():
                event_day = timestamp.date()
                if event_day < start_date or event_day > end_date:
                    continue
                estimate = _number(row.get("EPS Estimate"))
                actual = _number(row.get("Reported EPS"))
                events.append(_event(
                    source="yfinance", source_id=f"{symbol}:{event_day.isoformat()}",
                    event_date=event_day.isoformat(), title=f"{symbol} Earnings",
                    event_type="earnings", country=_ticker_country(symbol), importance="high",
                    ticker=symbol, forecast=estimate, consensus=estimate, actual=actual,
                    detail=f"{symbol}의 실적 발표 예정일입니다.", source_name="Yahoo Finance",
                    source_url=f"https://finance.yahoo.com/quote/{symbol}/calendar/",
                ))
        except Exception as exc:
            errors.append(f"{symbol}: {exc}")
    message = "; ".join(errors[:3])
    return ProviderResult("yfinance", "partial" if errors else "success", events, message)


def collect_ecos_calendar(start_date: date, end_date: date) -> ProviderResult:
    url = os.getenv("ECOS_RELEASE_CALENDAR_URL", "").strip()
    if not url:
        return ProviderResult(
            "ecos", "skipped", [],
            "ECOS has no universal release-calendar endpoint; set ECOS_RELEASE_CALENDAR_URL to an official JSON feed",
        )
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    rows = payload if isinstance(payload, list) else payload.get("events", [])
    events = []
    for item in rows:
        event_date = str(item.get("date", ""))[:10]
        if not _in_range(event_date, start_date, end_date):
            continue
        events.append(_event(
            source="ecos", source_id=str(item.get("id", f"{event_date}:{item.get('title', '')}")),
            event_date=event_date, title=str(item.get("title", "한국은행 경제지표 발표")),
            event_type="macro", country="KR", importance=str(item.get("importance", "medium")),
            time=str(item.get("time", "")), previous=item.get("previous"), forecast=item.get("forecast"),
            consensus=item.get("consensus"), actual=item.get("actual"), detail=str(item.get("detail", "")),
            source_name="한국은행 ECOS", source_url=str(item.get("source_url", url)),
        ))
    return ProviderResult("ecos", "success", events)


def _event(source: str, source_id: str, event_date: str, title: str, event_type: str,
           country: str, importance: str, source_name: str, source_url: str, **values: Any) -> dict[str, Any]:
    digest = hashlib.sha1(f"{source}|{source_id}".encode("utf-8")).hexdigest()[:16]
    event = {
        "id": f"evt-{source}-{digest}", "date": event_date, "title": title,
        "type": event_type, "country": country, "time": values.pop("time", ""),
        "importance": importance, "forecast": values.pop("forecast", None),
        "consensus": values.pop("consensus", None), "previous": values.pop("previous", None),
        "actual": values.pop("actual", None), "detail": values.pop("detail", ""),
        "aiComment": "", "expectedImpact": "", "source_name": source_name,
        "source_url": source_url, "source_provider": source, "source_id": source_id,
        "ticker": values.pop("ticker", ""), "raw_payload": values or None,
    }
    return event


def _parse_fomc_date(year: int, month_text: str, date_text: str) -> Optional[date]:
    day_numbers = re.findall(r"\d{1,2}", date_text)
    if not day_numbers:
        return None
    clean_month = re.sub(r"[^A-Za-z]", "", month_text).strip()
    try:
        month = datetime.strptime(clean_month[:3], "%b").month
        return date(year, month, int(day_numbers[-1]))
    except ValueError:
        return None


def _in_range(value: str, start_date: date, end_date: date) -> bool:
    try:
        parsed = date.fromisoformat(value)
        return start_date <= parsed <= end_date
    except ValueError:
        return False


def _compact_date(value: Any) -> str:
    raw = re.sub(r"\D", "", str(value or ""))
    if len(raw) != 8:
        return ""
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except ValueError:
        return ""


def _number(value: Any) -> Optional[float]:
    try:
        if value is None or str(value).lower() == "nan":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _ticker_country(symbol: str) -> str:
    return "KR" if symbol.endswith((".KS", ".KQ")) else "US"


def _dart_importance(report_name: str) -> str:
    high_terms = ("잠정", "합병", "분할", "유상증자", "부도", "영업정지", "회생", "감사의견")
    return "high" if any(term in report_name for term in high_terms) else "medium"


def _is_major_fred_release(title: str) -> bool:
    normalized = title.strip().lower()
    return normalized in FRED_MAJOR_RELEASES or normalized == "g.17 industrial production and capacity utilization"


def _fred_importance(title: str) -> str:
    high_terms = {"consumer price index", "employment situation", "gross domestic product", "personal income and outlays"}
    normalized = title.strip().lower()
    return "high" if normalized in high_terms else "medium"
