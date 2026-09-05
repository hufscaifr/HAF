from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
    select_companies_from_url,
)

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


DEFAULT_PERIOD = "6mo"
DEFAULT_INTERVAL = "1d"
DEFAULT_TIMEOUT = 20
MARKET_SUFFIXES = {
    "KOSPI": ".KS",
    "KOSDAQ": ".KQ",
}
MARKET_TIMEZONES = {
    "KOSPI": "Asia/Seoul",
    "KOSDAQ": "Asia/Seoul",
}


class MarketDataError(RuntimeError):
    """Raised when Yahoo Finance market data cannot be fetched."""


@dataclass
class CompanyOHLCV:
    company_name: str
    company_name_ko: str
    ticker: str
    market: str
    yahoo_symbol: str
    currency: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    row_count: int
    latest_close: Optional[float]
    latest_volume: Optional[int]
    ohlcv: list[dict[str, Any]]
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_name_ko": self.company_name_ko,
            "ticker": self.ticker,
            "market": self.market,
            "yahoo_symbol": self.yahoo_symbol,
            "currency": self.currency,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "row_count": self.row_count,
            "latest_close": self.latest_close,
            "latest_volume": self.latest_volume,
            "ohlcv": self.ohlcv,
            "error": self.error,
        }


def fetch_selection_market_data(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> dict[str, Any]:
    selection_result = select_companies_from_url(
        url=url,
        provider=provider,
        model=model,
        max_companies=max_companies,
        article_char_limit=article_char_limit,
    )

    company_results = fetch_market_data_for_companies(
        companies=selection_result["selection"]["companies"],
        period=period,
        interval=interval,
    )

    return {
        "article": selection_result["article"],
        "provider": selection_result["provider"],
        "model": selection_result["model"],
        "selection": selection_result["selection"],
        "market_data": {
            "period": period,
            "interval": interval,
            "companies": company_results,
        },
    }


def fetch_market_data_for_companies(
    companies: list[dict[str, Any]],
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for company in companies:
        try:
            ohlcv = fetch_company_ohlcv(
                company=company,
                period=period,
                interval=interval,
            )
            results.append(ohlcv.to_dict())
        except MarketDataError as exc:
            results.append(
                CompanyOHLCV(
                    company_name=str(company.get("company_name", "")).strip(),
                    company_name_ko=str(company.get("company_name_ko", "")).strip(),
                    ticker=safe_normalize_ticker(company.get("ticker", "")),
                    market=str(company.get("market", "")).strip(),
                    yahoo_symbol=safe_build_yahoo_symbol(
                        ticker=company.get("ticker", ""),
                        market=company.get("market", ""),
                    ),
                    currency=None,
                    start_date=None,
                    end_date=None,
                    row_count=0,
                    latest_close=None,
                    latest_volume=None,
                    ohlcv=[],
                    error=str(exc),
                ).to_dict()
            )

    return results


def fetch_company_ohlcv(
    company: dict[str, Any],
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> CompanyOHLCV:
    yfinance_module = get_yfinance_module()

    ticker = normalize_ticker(company.get("ticker", ""))
    market = str(company.get("market", "")).strip().upper()
    yahoo_symbol = build_yahoo_symbol(ticker=ticker, market=market)

    history = yfinance_module.download(
        yahoo_symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
        timeout=DEFAULT_TIMEOUT,
        multi_level_index=False,
    )
    if history.empty:
        raise MarketDataError(
            f"No price history returned for {yahoo_symbol} "
            f"(period={period}, interval={interval})."
        )

    normalized = normalize_history_frame(
        history,
        timezone=MARKET_TIMEZONES.get(market),
    )
    first_row = normalized.iloc[0]
    last_row = normalized.iloc[-1]

    return CompanyOHLCV(
        company_name=str(company.get("company_name", "")).strip(),
        company_name_ko=str(company.get("company_name_ko", "")).strip(),
        ticker=ticker,
        market=market,
        yahoo_symbol=yahoo_symbol,
        currency=extract_currency(history),
        start_date=str(first_row["Date"]),
        end_date=str(last_row["Date"]),
        row_count=len(normalized),
        latest_close=float(last_row["Close"]),
        latest_volume=int(last_row["Volume"]),
        ohlcv=frame_to_ohlcv_records(normalized),
    )


def normalize_ticker(ticker: Any) -> str:
    digits = "".join(ch for ch in str(ticker) if ch.isdigit())
    if not digits:
        raise MarketDataError(f"Invalid ticker: {ticker}")
    return digits.zfill(6)


def build_yahoo_symbol(ticker: str, market: str) -> str:
    normalized_market = str(market).strip().upper()
    if normalized_market not in MARKET_SUFFIXES:
        raise MarketDataError(f"Unsupported market for Yahoo Finance: {market}")
    return f"{normalize_ticker(ticker)}{MARKET_SUFFIXES[normalized_market]}"


def normalize_history_frame(
    history: pd.DataFrame,
    timezone: Optional[str] = None,
) -> pd.DataFrame:
    frame = history.reset_index().copy()
    has_intraday_index = "Datetime" in frame.columns
    if "Datetime" in frame.columns:
        frame = frame.rename(columns={"Datetime": "Date"})

    dates = pd.to_datetime(frame["Date"])
    if getattr(dates.dt, "tz", None) is not None:
        if timezone:
            dates = dates.dt.tz_convert(timezone)
        dates = dates.dt.tz_localize(None)
    has_intraday_values = has_intraday_index or (dates.dt.normalize() != dates).any()
    if has_intraday_values:
        frame["Date"] = dates.dt.strftime("%Y-%m-%d %H:%M")
    else:
        frame["Date"] = dates.dt.strftime("%Y-%m-%d")
    ohlcv_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    frame = frame[ohlcv_columns]
    frame["Open"] = frame["Open"].astype(float).round(4)
    frame["High"] = frame["High"].astype(float).round(4)
    frame["Low"] = frame["Low"].astype(float).round(4)
    frame["Close"] = frame["Close"].astype(float).round(4)
    frame["Volume"] = frame["Volume"].fillna(0).astype(int)
    return frame


def frame_to_ohlcv_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "date": row["Date"],
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        }
        for _, row in frame.iterrows()
    ]


def extract_currency(history: pd.DataFrame) -> Optional[str]:
    currency = history.attrs.get("currency")
    return str(currency) if currency else None


def safe_normalize_ticker(ticker: Any) -> str:
    try:
        return normalize_ticker(ticker)
    except MarketDataError:
        return str(ticker).strip()


def safe_build_yahoo_symbol(ticker: Any, market: Any) -> str:
    try:
        return build_yahoo_symbol(str(ticker), str(market))
    except MarketDataError:
        return ""


def get_yfinance_module() -> Any:
    if yf is None:
        raise MarketDataError(
            "The 'yfinance' package is not installed. Run `pip install -r requirements.txt`."
        )
    return yf
