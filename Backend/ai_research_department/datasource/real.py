from __future__ import annotations

from typing import Any

from ai_research_department.config import disable_incompatible_pandas_accelerators, load_backend_env
from ai_research_department.datasource.base import DataSourceConnector

disable_incompatible_pandas_accelerators()

from cam_pipeline.fundamentals_data import FundamentalsDataError, analyze_company_fundamentals


class RealCompanyDataConnector(DataSourceConnector):
    """Collect real market and OpenDART evidence for a resolved company."""

    def __init__(
        self,
        company: str,
        ticker: str,
        market: str,
        period: str = "6mo",
        interval: str = "1d",
    ) -> None:
        load_backend_env()
        self.company = company
        self.ticker = ticker
        self.market = market
        self.period = period
        self.interval = interval
        self._records: dict[str, dict[str, Any]] | None = None

    async def search(self, query: str) -> list[dict[str, Any]]:
        records = self._ensure_records()
        normalized = str(query or "").lower()
        exact_matches = [
            record
            for record in records.values()
            if normalized
            and normalized
            in {
                str(record.get("metric", "")).lower(),
                str(record.get("source_id", "")).lower(),
            }
        ]
        if exact_matches:
            return exact_matches

        matches = [
            record
            for record in records.values()
            if normalized and normalized in str(record.get("fact", "")).lower()
        ]
        return matches or list(records.values())

    async def fetch(self, source_id: str) -> dict[str, Any]:
        records = self._ensure_records()
        if source_id not in records:
            raise KeyError(f"Unknown real source: {source_id}")
        return records[source_id]

    async def extract(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        return [raw_data]

    def _ensure_records(self) -> dict[str, dict[str, Any]]:
        if self._records is not None:
            return self._records

        company_payload = {
            "company_name": self.company,
            "company_name_ko": self.company,
            "ticker": self.ticker,
            "market": self.market,
        }
        records: dict[str, dict[str, Any]] = {}
        try:
            market_data = self._fetch_market_data()
            records.update(self._market_records(market_data))
        except Exception as exc:
            records["market_error"] = self._error_record("market_error", "Yahoo Finance", str(exc), "market_data")

        try:
            fundamentals = analyze_company_fundamentals(
                {
                    **company_payload,
                    "latest_close": records.get("latest_close", {}).get("value"),
                    "yahoo_symbol": records.get("latest_close", {}).get("yahoo_symbol", ""),
                }
            ).to_dict()
            records.update(self._fundamental_records(fundamentals))
        except FundamentalsDataError as exc:
            records["fundamentals_error"] = self._error_record("fundamentals_error", "OpenDART", str(exc), "filing")

        self._records = records
        return records

    def _fetch_market_data(self) -> dict[str, Any]:
        """Fetch recent OHLCV directly from yfinance with robust date handling."""
        import yfinance as yf

        yahoo_symbol = self._yahoo_symbol()
        history = yf.download(
            yahoo_symbol,
            period=self.period,
            interval=self.interval,
            auto_adjust=False,
            actions=False,
            progress=False,
            threads=False,
            timeout=20,
            multi_level_index=False,
        )
        if history.empty:
            raise RuntimeError(f"No price history returned for {yahoo_symbol}.")
        first_index = history.index[0]
        last_index = history.index[-1]
        last_row = history.iloc[-1]
        return {
            "ticker": self.ticker,
            "market": self.market,
            "yahoo_symbol": yahoo_symbol,
            "currency": "KRW" if self.market.upper() in {"KOSPI", "KOSDAQ"} else None,
            "start_date": str(getattr(first_index, "date", lambda: first_index)()),
            "end_date": str(getattr(last_index, "date", lambda: last_index)()),
            "latest_close": float(last_row["Close"]),
            "latest_volume": int(last_row["Volume"]),
        }

    def _yahoo_symbol(self) -> str:
        suffix = ".KQ" if str(self.market).upper() == "KOSDAQ" else ".KS"
        return f"{str(self.ticker).zfill(6)}{suffix}"

    def _market_records(self, market_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {
            "latest_close": {
                "source_id": "latest_close",
                "fact": f"{self.company} 최근 종가는 {market_data.get('latest_close')} {market_data.get('currency') or ''}입니다.",
                "metric": "latest_close",
                "value": market_data.get("latest_close"),
                "unit": market_data.get("currency") or "price",
                "period": market_data.get("end_date"),
                "source_name": "Yahoo Finance",
                "source_url": f"https://finance.yahoo.com/quote/{market_data.get('yahoo_symbol')}",
                "source_type": "market_data",
                "yahoo_symbol": market_data.get("yahoo_symbol"),
            },
            "latest_volume": {
                "source_id": "latest_volume",
                "fact": f"{self.company} 최근 거래량은 {market_data.get('latest_volume')}주입니다.",
                "metric": "latest_volume",
                "value": market_data.get("latest_volume"),
                "unit": "shares",
                "period": market_data.get("end_date"),
                "source_name": "Yahoo Finance",
                "source_url": f"https://finance.yahoo.com/quote/{market_data.get('yahoo_symbol')}",
                "source_type": "market_data",
            },
        }

    def _fundamental_records(self, fundamentals: dict[str, Any]) -> dict[str, dict[str, Any]]:
        metrics = fundamentals.get("valuation_metrics", {})
        records: dict[str, dict[str, Any]] = {}
        for metric in (
            "per",
            "pbr",
            "eps",
            "bps",
            "roe",
            "debt_ratio",
            "operating_margin",
            "net_margin",
            "market_cap",
            "shares_outstanding",
            "revenue",
            "operating_income",
            "net_income",
        ):
            value = metrics.get(metric)
            if value is None:
                continue
            records[metric] = {
                "source_id": metric,
                "fact": f"{self.company}의 {metric} 값은 {value}입니다.",
                "metric": metric,
                "value": value,
                "unit": self._metric_unit(metric),
                "period": fundamentals.get("business_year") or fundamentals.get("statement_date"),
                "source_name": "OpenDART",
                "source_url": "https://opendart.fss.or.kr/",
                "source_type": "filing",
            }
        return records

    def _error_record(self, source_id: str, source_name: str, message: str, source_type: str) -> dict[str, Any]:
        return {
            "source_id": source_id,
            "fact": f"{source_name} 데이터 수집 실패: {message}",
            "metric": source_id,
            "value": None,
            "unit": None,
            "period": None,
            "source_name": source_name,
            "source_url": None,
            "source_type": source_type,
        }

    def _metric_unit(self, metric: str) -> str:
        if metric in {"per", "pbr"}:
            return "x"
        if metric in {"roe", "debt_ratio", "operating_margin", "net_margin"}:
            return "%"
        if metric in {"eps", "bps"}:
            return "KRW/share"
        return "KRW"
