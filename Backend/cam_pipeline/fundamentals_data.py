from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from io import BytesIO
import os
import re
from typing import Any, Optional
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

import pandas as pd
import requests

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
    normalize_env_api_key,
)
from cam_pipeline.market_data import (
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    fetch_selection_market_data,
)


DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
DART_SINGLE_ACCOUNT_ALL_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
DART_SINGLE_INDICATOR_URL = "https://opendart.fss.or.kr/api/fnlttSinglIndx.json"
DART_TIMEOUT = 20
DART_SOURCE_NAME = "OpenDART"
DART_NO_DATA_STATUS = "013"
DART_REPORT_CODES = {
    "11011": "사업보고서",
    "11014": "3분기보고서",
    "11012": "반기보고서",
    "11013": "1분기보고서",
}
DART_REPORT_SEARCH_ORDER = ("11011", "11014", "11012", "11013")
DART_FS_DIV_SEARCH_ORDER = ("CFS", "OFS")
DART_RATIO_CATEGORY_CODES = ("M210000", "M220000")


class FundamentalsDataError(RuntimeError):
    """Raised when fundamental metrics cannot be fetched or calculated."""


@dataclass
class CompanyFundamentals:
    company_name: str
    company_name_ko: str
    ticker: str
    market: str
    yahoo_symbol: str
    corp_code: Optional[str]
    business_year: Optional[str]
    report_code: Optional[str]
    report_name: Optional[str]
    statement_date: Optional[str]
    latest_close: Optional[float]
    market_cap: Optional[float]
    shares_outstanding: Optional[float]
    valuation_metrics: dict[str, Any]
    raw_indicator_values: dict[str, Any]
    source: str
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_name_ko": self.company_name_ko,
            "ticker": self.ticker,
            "market": self.market,
            "yahoo_symbol": self.yahoo_symbol,
            "corp_code": self.corp_code,
            "business_year": self.business_year,
            "report_code": self.report_code,
            "report_name": self.report_name,
            "statement_date": self.statement_date,
            "latest_close": self.latest_close,
            "market_cap": self.market_cap,
            "shares_outstanding": self.shares_outstanding,
            "valuation_metrics": self.valuation_metrics,
            "raw_indicator_values": self.raw_indicator_values,
            "source": self.source,
            "error": self.error,
        }


def fetch_selection_fundamentals(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> dict[str, Any]:
    market_result = fetch_selection_market_data(
        url=url,
        provider=provider,
        model=model,
        max_companies=max_companies,
        article_char_limit=article_char_limit,
        period=period,
        interval=interval,
    )

    fundamentals = analyze_market_data_fundamentals(
        market_result["market_data"]["companies"]
    )

    return {
        "article": market_result["article"],
        "provider": market_result["provider"],
        "model": market_result["model"],
        "selection": market_result["selection"],
        "market_data": market_result["market_data"],
        "fundamentals": {
            "companies": fundamentals,
        },
    }


def analyze_market_data_fundamentals(
    companies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for company in companies:
        try:
            fundamentals = analyze_company_fundamentals(company)
            results.append(fundamentals.to_dict())
        except FundamentalsDataError as exc:
            results.append(
                CompanyFundamentals(
                    company_name=str(company.get("company_name", "")).strip(),
                    company_name_ko=str(company.get("company_name_ko", "")).strip(),
                    ticker=normalize_ticker_or_original(company.get("ticker", "")),
                    market=str(company.get("market", "")).strip(),
                    yahoo_symbol=str(company.get("yahoo_symbol", "")).strip(),
                    corp_code=None,
                    business_year=None,
                    report_code=None,
                    report_name=None,
                    statement_date=None,
                    latest_close=to_float(company.get("latest_close")),
                    market_cap=None,
                    shares_outstanding=None,
                    valuation_metrics={},
                    raw_indicator_values={},
                    source=DART_SOURCE_NAME,
                    error=str(exc),
                ).to_dict()
            )

    return results


def analyze_company_fundamentals(company: dict[str, Any]) -> CompanyFundamentals:
    ticker = normalize_ticker(company.get("ticker", ""))
    latest_close = to_float(company.get("latest_close"))
    yahoo_symbol = str(company.get("yahoo_symbol", "")).strip()
    corp_profile = lookup_dart_corp_profile(ticker)
    filing = fetch_latest_dart_filing(corp_profile["corp_code"])

    valuation_metrics, raw_indicator_values = build_valuation_metrics(
        latest_close=latest_close,
        statement_records=filing["statement_records"],
        ratio_lookup=filing["ratio_lookup"],
    )

    statement_date = first_non_empty(
        filing.get("statement_date"),
        determine_statement_date(raw_indicator_values),
    )
    business_year = first_non_empty(
        filing.get("business_year"),
        statement_date[:4] if statement_date else None,
    )

    return CompanyFundamentals(
        company_name=str(company.get("company_name", "")).strip(),
        company_name_ko=str(company.get("company_name_ko", "")).strip(),
        ticker=ticker,
        market=str(company.get("market", "")).strip(),
        yahoo_symbol=yahoo_symbol,
        corp_code=corp_profile["corp_code"],
        business_year=business_year,
        report_code=filing["report_code"],
        report_name=build_dart_report_name(
            filing["report_code"],
            filing["fs_div"],
        ),
        statement_date=statement_date,
        latest_close=latest_close,
        market_cap=valuation_metrics.get("market_cap"),
        shares_outstanding=valuation_metrics.get("shares_outstanding"),
        valuation_metrics=valuation_metrics,
        raw_indicator_values=raw_indicator_values,
        source=DART_SOURCE_NAME,
    )


def fetch_latest_dart_filing(corp_code: str) -> dict[str, Any]:
    current_year = date.today().year
    business_years = [str(current_year - offset) for offset in range(1, 5)]

    for business_year in business_years:
        for report_code in DART_REPORT_SEARCH_ORDER:
            for fs_div in DART_FS_DIV_SEARCH_ORDER:
                statement_records = fetch_dart_statement_records(
                    corp_code=corp_code,
                    business_year=business_year,
                    report_code=report_code,
                    fs_div=fs_div,
                )
                if not statement_records:
                    continue

                ratio_lookup, ratio_statement_date = fetch_dart_ratio_lookup(
                    corp_code=corp_code,
                    business_year=business_year,
                    report_code=report_code,
                )

                statement_date = first_non_empty(
                    extract_statement_date_from_records(statement_records),
                    ratio_statement_date,
                )
                return {
                    "corp_code": corp_code,
                    "business_year": business_year,
                    "report_code": report_code,
                    "fs_div": fs_div,
                    "statement_date": statement_date,
                    "statement_records": statement_records,
                    "ratio_lookup": ratio_lookup,
                }

    raise FundamentalsDataError("DART에서 최근 재무제표를 찾지 못했습니다.")


def fetch_dart_statement_records(
    corp_code: str,
    business_year: str,
    report_code: str,
    fs_div: str,
) -> list[dict[str, Any]]:
    payload = request_dart_json(
        DART_SINGLE_ACCOUNT_ALL_URL,
        {
            "corp_code": corp_code,
            "bsns_year": business_year,
            "reprt_code": report_code,
            "fs_div": fs_div,
        },
        allow_no_data=True,
    )
    records = payload.get("list", [])
    return normalize_statement_records(records)


def fetch_dart_ratio_lookup(
    corp_code: str,
    business_year: str,
    report_code: str,
) -> tuple[dict[str, Optional[float]], Optional[str]]:
    ratio_lookup: dict[str, Optional[float]] = {}
    statement_date: Optional[str] = None

    for idx_cl_code in DART_RATIO_CATEGORY_CODES:
        payload = request_dart_json(
            DART_SINGLE_INDICATOR_URL,
            {
                "corp_code": corp_code,
                "bsns_year": business_year,
                "reprt_code": report_code,
                "idx_cl_code": idx_cl_code,
            },
            allow_no_data=True,
        )
        for item in payload.get("list", []):
            idx_name = normalize_label(item.get("idx_nm"))
            ratio_lookup[idx_name] = to_float(item.get("idx_val"))
            statement_date = first_non_empty(
                statement_date,
                normalize_statement_date(item.get("stlm_dt")),
            )

    return ratio_lookup, statement_date


def request_dart_json(
    url: str,
    params: dict[str, Any],
    allow_no_data: bool = False,
) -> dict[str, Any]:
    api_key = get_dart_api_key()
    response = requests.get(
        url,
        params={
            "crtfc_key": api_key,
            **params,
        },
        timeout=DART_TIMEOUT,
    )
    response.raise_for_status()

    payload = response.json()
    status = str(payload.get("status", "")).strip()
    if status == "000":
        return payload
    if allow_no_data and status == DART_NO_DATA_STATUS:
        return {"list": []}

    message = str(payload.get("message", "알 수 없는 오류")).strip()
    raise FundamentalsDataError(f"DART API 호출 실패: {message} (status={status})")


@lru_cache(maxsize=1)
def load_dart_corp_codes() -> dict[str, dict[str, str]]:
    api_key = get_dart_api_key()
    response = requests.get(
        DART_CORP_CODE_URL,
        params={"crtfc_key": api_key},
        timeout=DART_TIMEOUT,
    )
    response.raise_for_status()

    try:
        with ZipFile(BytesIO(response.content)) as archive:
            member_names = archive.namelist()
            if not member_names:
                raise FundamentalsDataError("DART corpCode 응답 ZIP이 비어 있습니다.")
            xml_bytes = archive.read(member_names[0])
    except BadZipFile as exc:
        raise FundamentalsDataError(parse_dart_corp_code_error(response.content)) from exc

    root = ET.fromstring(xml_bytes)
    mapping: dict[str, dict[str, str]] = {}
    for node in root.findall(".//list"):
        stock_code = normalize_digits(node.findtext("stock_code", ""))
        corp_code = str(node.findtext("corp_code", "")).strip()
        if not stock_code or not corp_code:
            continue

        mapping[stock_code] = {
            "corp_code": corp_code,
            "corp_name": str(node.findtext("corp_name", "")).strip(),
            "modify_date": str(node.findtext("modify_date", "")).strip(),
        }

    if not mapping:
        raise FundamentalsDataError("DART corpCode 목록에서 상장사 종목코드를 찾지 못했습니다.")
    return mapping


def parse_dart_corp_code_error(content: bytes) -> str:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return "DART corpCode 응답을 해석하지 못했습니다."

    status = str(root.findtext(".//status", "")).strip()
    message = str(root.findtext(".//message", "")).strip()
    if status or message:
        return f"DART corpCode 호출 실패: {message or '알 수 없는 오류'} (status={status or 'N/A'})"
    return "DART corpCode 응답을 해석하지 못했습니다."


def lookup_dart_corp_profile(ticker: str) -> dict[str, str]:
    corp_profile = load_dart_corp_codes().get(normalize_ticker(ticker))
    if corp_profile is None:
        raise FundamentalsDataError(f"DART corp_code를 찾지 못했습니다: {ticker}")
    return corp_profile


def build_valuation_metrics(
    latest_close: Optional[float],
    statement_records: list[dict[str, Any]],
    ratio_lookup: dict[str, Optional[float]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    diluted_eps, diluted_eps_date, diluted_eps_source = extract_account_value(
        statement_records,
        subject_divisions=("IS", "CIS"),
        account_ids=("ifrs-full_DilutedEarningsLossPerShare",),
        account_names=("희석주당이익",),
    )
    basic_eps, basic_eps_date, basic_eps_source = extract_account_value(
        statement_records,
        subject_divisions=("IS", "CIS"),
        account_ids=("ifrs-full_BasicEarningsLossPerShare",),
        account_names=("기본주당이익",),
    )
    revenue, revenue_date, revenue_source = extract_account_value(
        statement_records,
        subject_divisions=("IS", "CIS"),
        account_ids=("ifrs-full_Revenue",),
        account_names=("매출액", "영업수익"),
    )
    operating_income, operating_income_date, operating_income_source = extract_account_value(
        statement_records,
        subject_divisions=("IS", "CIS"),
        account_ids=("dart_OperatingIncomeLoss",),
        account_names=("영업이익",),
    )
    net_income_common, net_income_date, net_income_source = extract_account_value(
        statement_records,
        subject_divisions=("IS", "CIS"),
        account_ids=(
            "ifrs-full_ProfitLossAttributableToOwnersOfParent",
            "ifrs-full_ProfitLoss",
        ),
        account_names=("지배기업 소유지분", "당기순이익", "당기순이익(손실)"),
    )
    common_stock_equity, common_stock_equity_date, common_stock_equity_source = extract_account_value(
        statement_records,
        subject_divisions=("BS",),
        account_ids=(
            "ifrs-full_EquityAttributableToOwnersOfParent",
            "ifrs-full_Equity",
        ),
        account_names=("지배기업 소유주지분", "자본총계"),
    )
    cash_and_equivalents, cash_and_equivalents_date, cash_and_equivalents_source = extract_account_value(
        statement_records,
        subject_divisions=("BS",),
        account_ids=("ifrs-full_CashAndCashEquivalents",),
        account_names=("현금및현금성자산",),
    )
    operating_cash_flow, operating_cash_flow_date, operating_cash_flow_source = extract_account_value(
        statement_records,
        subject_divisions=("CF",),
        account_ids=("ifrs-full_CashFlowsFromUsedInOperatingActivities",),
        account_names=("영업활동현금흐름",),
    )
    cash_dividends_paid, cash_dividends_paid_date, cash_dividends_paid_source = extract_account_value(
        statement_records,
        subject_divisions=("CF",),
        account_ids=("ifrs-full_DividendsPaidClassifiedAsFinancingActivities",),
        account_names=("배당금의지급",),
    )

    debt_components = extract_total_debt(statement_records)
    total_debt = debt_components["value"]
    total_debt_date = debt_components["date"]
    total_debt_source = debt_components["source"]

    depreciation_and_amortization = extract_depreciation_and_amortization(statement_records)
    ebitda = None
    if operating_income is not None and depreciation_and_amortization["value"] is not None:
        ebitda = operating_income + depreciation_and_amortization["value"]

    eps = first_float(diluted_eps, basic_eps)
    shares_outstanding = estimate_share_count(net_income_common, eps)
    bps = safe_divide(common_stock_equity, shares_outstanding)
    cash_flow_per_share = safe_divide(operating_cash_flow, shares_outstanding)

    cash_dps = None
    if cash_dividends_paid is not None and shares_outstanding not in (None, 0):
        cash_dps = abs(cash_dividends_paid) / shares_outstanding

    market_cap = None
    if latest_close is not None and shares_outstanding not in (None, 0):
        market_cap = latest_close * shares_outstanding

    enterprise_value = calculate_enterprise_value(
        market_cap=market_cap,
        total_debt=total_debt,
        cash_and_equivalents=cash_and_equivalents,
    )
    per = safe_divide(latest_close, eps)
    pbr = safe_divide(latest_close, bps)
    pcr = safe_divide(latest_close, cash_flow_per_share)
    ev_to_ebitda = safe_divide(enterprise_value, ebitda)
    cash_dividend_yield = safe_divide(cash_dps, latest_close, multiplier=100.0)
    operating_margin = first_float(
        ratio_lookup.get(normalize_label("영업이익률")),
        safe_divide(operating_income, revenue, multiplier=100.0),
    )
    net_margin = first_float(
        ratio_lookup.get(normalize_label("순이익률")),
        safe_divide(net_income_common, revenue, multiplier=100.0),
    )

    valuation_metrics = {
        "eps": eps,
        "bps": bps,
        "per": per,
        "pbr": pbr,
        "pcr": pcr,
        "ev_to_ebitda": ev_to_ebitda,
        "ebitda": ebitda,
        "cash_dps": cash_dps,
        "cash_dividend_yield": cash_dividend_yield,
        "current_per": per,
        "current_pbr": pbr,
        "roe": to_float(ratio_lookup.get(normalize_label("ROE"))),
        "debt_ratio": to_float(ratio_lookup.get(normalize_label("부채비율"))),
        "current_ratio": to_float(ratio_lookup.get(normalize_label("유동비율"))),
        "operating_margin": operating_margin,
        "net_margin": net_margin,
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,
        "shares_outstanding": shares_outstanding,
    }

    raw_indicator_values = {
        "diluted_eps": diluted_eps,
        "diluted_eps_source": diluted_eps_source,
        "diluted_eps_statement_date": diluted_eps_date,
        "basic_eps": basic_eps,
        "basic_eps_source": basic_eps_source,
        "basic_eps_statement_date": basic_eps_date,
        "revenue": revenue,
        "revenue_source": revenue_source,
        "revenue_statement_date": revenue_date,
        "operating_income": operating_income,
        "operating_income_source": operating_income_source,
        "operating_income_statement_date": operating_income_date,
        "net_income_common": net_income_common,
        "net_income_common_source": net_income_source,
        "net_income_common_statement_date": net_income_date,
        "common_stock_equity": common_stock_equity,
        "common_stock_equity_source": common_stock_equity_source,
        "common_stock_equity_statement_date": common_stock_equity_date,
        "total_debt": total_debt,
        "total_debt_source": total_debt_source,
        "total_debt_statement_date": total_debt_date,
        "cash_and_equivalents": cash_and_equivalents,
        "cash_and_equivalents_source": cash_and_equivalents_source,
        "cash_and_equivalents_statement_date": cash_and_equivalents_date,
        "operating_cash_flow": operating_cash_flow,
        "operating_cash_flow_source": operating_cash_flow_source,
        "operating_cash_flow_statement_date": operating_cash_flow_date,
        "cash_dividends_paid": cash_dividends_paid,
        "cash_dividends_paid_source": cash_dividends_paid_source,
        "cash_dividends_paid_statement_date": cash_dividends_paid_date,
        "depreciation_and_amortization": depreciation_and_amortization["value"],
        "depreciation_and_amortization_source": depreciation_and_amortization["source"],
        "depreciation_and_amortization_statement_date": depreciation_and_amortization["date"],
        "ratio_roe": to_float(ratio_lookup.get(normalize_label("ROE"))),
        "ratio_debt_ratio": to_float(ratio_lookup.get(normalize_label("부채비율"))),
        "ratio_current_ratio": to_float(ratio_lookup.get(normalize_label("유동비율"))),
        "ratio_net_margin": to_float(ratio_lookup.get(normalize_label("순이익률"))),
        "computed_eps": eps,
        "computed_bps": bps,
        "computed_per": per,
        "computed_pbr": pbr,
        "computed_pcr": pcr,
        "computed_ev_to_ebitda": ev_to_ebitda,
        "computed_cash_dps": cash_dps,
        "computed_cash_dividend_yield": cash_dividend_yield,
        "computed_operating_margin": operating_margin,
        "computed_net_margin": net_margin,
        "shares_outstanding": shares_outstanding,
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,
    }

    return valuation_metrics, raw_indicator_values


def extract_total_debt(statement_records: list[dict[str, Any]]) -> dict[str, Optional[Any]]:
    direct_value, direct_date, direct_source = extract_account_value(
        statement_records,
        subject_divisions=("BS",),
        account_ids=(
            "ifrs-full_Borrowings",
            "dart_ShortTermBorrowingsAndLongTermBorrowings",
        ),
        account_names=("총차입금", "차입금"),
    )
    if direct_value is not None:
        return {"value": direct_value, "date": direct_date, "source": direct_source}

    component_specs = (
        (("ifrs-full_CurrentBorrowings",), ("단기차입금",)),
        (("ifrs-full_CurrentPortionOfLongtermBorrowings",), ("유동성장기부채",)),
        (("ifrs-full_NoncurrentPortionOfNoncurrentLoansReceived",), ("장기차입금",)),
        (("ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",), ("사채",)),
        (("ifrs-full_LeaseLiabilities",), ("리스부채",)),
        (("ifrs-full_CurrentLeaseLiabilities",), ("유동리스부채",)),
    )

    total = 0.0
    matched_sources: list[str] = []
    matched_dates: list[str] = []
    has_any_component = False
    for account_ids, account_names in component_specs:
        value, value_date, value_source = extract_account_value(
            statement_records,
            subject_divisions=("BS",),
            account_ids=account_ids,
            account_names=account_names,
        )
        if value is None:
            continue
        has_any_component = True
        total += value
        if value_source:
            matched_sources.append(value_source)
        if value_date:
            matched_dates.append(value_date)

    if not has_any_component:
        return {"value": None, "date": None, "source": None}

    return {
        "value": total,
        "date": max(matched_dates) if matched_dates else None,
        "source": " + ".join(matched_sources) if matched_sources else None,
    }


def extract_depreciation_and_amortization(
    statement_records: list[dict[str, Any]],
) -> dict[str, Optional[Any]]:
    value, value_date, value_source = extract_account_value(
        statement_records,
        subject_divisions=("IS", "CIS", "CF"),
        account_names_contains=("감가상각", "상각비", "depreciation", "amortization", "amortisation"),
        account_ids_contains=("Depreciation", "Amortization", "Amortisation"),
    )
    return {"value": value, "date": value_date, "source": value_source}


def extract_account_value(
    statement_records: list[dict[str, Any]],
    subject_divisions: tuple[str, ...],
    account_ids: tuple[str, ...] = (),
    account_names: tuple[str, ...] = (),
    account_ids_contains: tuple[str, ...] = (),
    account_names_contains: tuple[str, ...] = (),
) -> tuple[Optional[float], Optional[str], Optional[str]]:
    filtered = [
        record
        for record in statement_records
        if not subject_divisions or record["sj_div"] in subject_divisions
    ]
    if not filtered:
        return None, None, None

    exact_id_matches = {
        normalize_label(account_id)
        for account_id in account_ids
    }
    exact_name_matches = {
        normalize_label(account_name)
        for account_name in account_names
    }
    contains_id_matches = tuple(
        normalize_label(account_id)
        for account_id in account_ids_contains
    )
    contains_name_matches = tuple(
        normalize_label(account_name)
        for account_name in account_names_contains
    )

    for record in filtered:
        account_id = record["account_id_normalized"]
        if account_id and account_id in exact_id_matches:
            return record["amount"], record["statement_date"], record["source"]

    for record in filtered:
        account_name = record["account_name_normalized"]
        if account_name and account_name in exact_name_matches:
            return record["amount"], record["statement_date"], record["source"]

    for record in filtered:
        account_id = record["account_id_normalized"]
        if account_id and any(token in account_id for token in contains_id_matches):
            return record["amount"], record["statement_date"], record["source"]

    for record in filtered:
        account_name = record["account_name_normalized"]
        if account_name and any(token in account_name for token in contains_name_matches):
            return record["amount"], record["statement_date"], record["source"]

    return None, None, None


def normalize_statement_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for order, record in enumerate(records):
        account_name = str(record.get("account_nm", "")).strip()
        account_id = str(record.get("account_id", "")).strip()
        amount = to_float(record.get("thstrm_amount"))
        normalized.append(
            {
                "order": order,
                "sj_div": str(record.get("sj_div", "")).strip(),
                "account_nm": account_name,
                "account_id": account_id,
                "account_name_normalized": normalize_label(account_name),
                "account_id_normalized": normalize_label(account_id),
                "amount": amount,
                "statement_date": normalize_statement_date(record.get("thstrm_dt")),
                "source": account_id or account_name or None,
            }
        )

    return normalized


def determine_statement_date(raw_indicator_values: dict[str, Any]) -> Optional[str]:
    date_keys = (
        "diluted_eps_statement_date",
        "basic_eps_statement_date",
        "revenue_statement_date",
        "operating_income_statement_date",
        "net_income_common_statement_date",
        "common_stock_equity_statement_date",
        "total_debt_statement_date",
        "cash_and_equivalents_statement_date",
        "operating_cash_flow_statement_date",
        "cash_dividends_paid_statement_date",
        "depreciation_and_amortization_statement_date",
    )
    dates = [
        str(raw_indicator_values[key]).strip()
        for key in date_keys
        if raw_indicator_values.get(key)
    ]
    if not dates:
        return None
    return max(dates)


def extract_statement_date_from_records(statement_records: list[dict[str, Any]]) -> Optional[str]:
    dates = [
        str(record["statement_date"]).strip()
        for record in statement_records
        if record.get("statement_date")
    ]
    if not dates:
        return None
    return max(dates)


def build_dart_report_name(report_code: Optional[str], fs_div: Optional[str]) -> Optional[str]:
    if not report_code:
        return None
    report_label = DART_REPORT_CODES.get(report_code, report_code)
    if not fs_div:
        return report_label
    fs_label = "연결" if str(fs_div).strip().upper() == "CFS" else "별도"
    return f"{report_label} ({fs_label})"


def get_dart_api_key() -> str:
    api_key = normalize_env_api_key(os.getenv("DART_API_KEY"))
    if not api_key:
        raise FundamentalsDataError("DART_API_KEY is not set.")
    return api_key


def normalize_ticker(value: Any) -> str:
    digits = normalize_digits(value)
    if not digits:
        raise FundamentalsDataError(f"Invalid ticker: {value}")
    return digits


def normalize_ticker_or_original(value: Any) -> str:
    try:
        return normalize_ticker(value)
    except FundamentalsDataError:
        return str(value).strip()


def normalize_digits(value: Any) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits.zfill(6) if digits else ""


def normalize_label(value: Any) -> str:
    return str(value).strip().lower()


def normalize_statement_date(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None

    matches = re.findall(r"(\d{4})[.\-/](\d{2})[.\-/](\d{2})", text)
    if matches:
        year, month, day = matches[-1]
        return f"{year}-{month}-{day}"

    return text or None


def estimate_share_count(
    net_income_common: Optional[float],
    eps: Optional[float],
) -> Optional[float]:
    if net_income_common is None or eps in (None, 0):
        return None

    estimated = abs(net_income_common / eps)
    if estimated <= 0:
        return None
    return estimated


def calculate_enterprise_value(
    market_cap: Optional[float],
    total_debt: Optional[float],
    cash_and_equivalents: Optional[float],
) -> Optional[float]:
    if market_cap is None:
        return None
    debt = total_debt or 0.0
    cash = cash_and_equivalents or 0.0
    return market_cap + debt - cash


def safe_divide(
    numerator: Optional[float],
    denominator: Optional[float],
    multiplier: float = 1.0,
) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return (numerator / denominator) * multiplier


def first_float(*values: Any) -> Optional[float]:
    for value in values:
        numeric = to_float(value)
        if numeric is not None:
            return numeric
    return None


def first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text in {"-", "N/A", "nan", "None"}:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None
