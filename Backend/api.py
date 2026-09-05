from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Literal, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, HttpUrl

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
    LLMConfigurationError,
    get_gemini_modules,
    get_openai_client_class,
    normalize_env_api_key,
    select_companies_from_url,
)
from cam_pipeline.market_data import (
    fetch_market_data_for_companies,
    safe_build_yahoo_symbol,
    safe_normalize_ticker,
)
from cam_pipeline.price_plot import (
    DEFAULT_DAILY_PLOT_INTERVAL,
    DEFAULT_DAILY_PLOT_PERIOD,
    DEFAULT_DAILY_RECENT_POINTS,
    DEFAULT_PLOT_INTERVAL,
    DEFAULT_PLOT_PERIOD,
    DEFAULT_RECENT_POINTS,
    generate_report_price_plots,
)
from cam_pipeline.opinion_engine import derive_company_opinions
from cam_pipeline.technical_analysis import DEFAULT_RECENT_ROWS, analyze_market_data_companies
from cam_pipeline.fundamentals_data import analyze_market_data_fundamentals
from cam_pipeline.financial_calendar import (
    DEFAULT_FINANCIAL_CALENDAR_MODEL,
    FinancialCalendarError,
    default_end_date,
    ensure_financial_calendar_current,
    get_today,
    list_financial_events,
    parse_iso_date,
    refresh_financial_calendar,
)


FRAMER_ORIGIN = "https://ambiguous-replacement-035632.framer.app"
STATIC_DIR = Path(__file__).resolve().parent / "static"
PLOTS_DIR = STATIC_DIR / "plots"


class NewResearchRequest(BaseModel):
    url: HttpUrl = Field(..., description="News article URL to crawl and analyze.")
    provider: Literal["openai", "gemini"] = DEFAULT_PROVIDER
    model: Optional[str] = None
    max_companies: int = Field(default=3, ge=1, le=10)
    article_char_limit: int = Field(default=DEFAULT_ARTICLE_CHAR_LIMIT, ge=1000, le=50000)


class ChartResearchRequest(NewResearchRequest):
    daily_plot_period: str = DEFAULT_DAILY_PLOT_PERIOD
    daily_plot_interval: str = DEFAULT_DAILY_PLOT_INTERVAL
    daily_recent_points: int = Field(default=DEFAULT_DAILY_RECENT_POINTS, ge=5, le=500)
    intraday_plot_period: str = DEFAULT_PLOT_PERIOD
    intraday_plot_interval: str = DEFAULT_PLOT_INTERVAL
    intraday_recent_points: int = Field(default=DEFAULT_RECENT_POINTS, ge=5, le=500)
    recent_rows: int = Field(default=DEFAULT_RECENT_ROWS, ge=1, le=30)


class FinancialCalendarRefreshRequest(BaseModel):
    start_date: Optional[str] = Field(
        default=None,
        description="Refresh start date in YYYY-MM-DD format. Defaults to today.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Refresh end date in YYYY-MM-DD format. Defaults to one year after start_date.",
    )
    model: Optional[str] = Field(
        default=None,
        description="OpenAI model used for calendar collection.",
    )


app = FastAPI(
    title="CAM Backend API",
    description="HTTP API for crawling a news URL and selecting meaningful Korean listed companies.",
    version="0.1.0",
)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CAM_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response


app.add_middleware(PrivateNetworkAccessMiddleware)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/financial-calendar")
def get_financial_calendar(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    importance: Optional[str] = None,
    refresh_if_stale: bool = True,
    model: Optional[str] = None,
) -> dict:
    today = get_today()
    try:
        parsed_start_date = parse_iso_date(start_date, today)
        parsed_end_date = parse_iso_date(end_date, default_end_date(parsed_start_date))
        if parsed_end_date < parsed_start_date:
            raise FinancialCalendarError("end_date must be greater than or equal to start_date.")

        refresh_status: dict[str, Any] = {"refreshed": False}
        refresh_error = None
        if refresh_if_stale:
            try:
                refresh_status = ensure_financial_calendar_current(
                    model=model or DEFAULT_FINANCIAL_CALENDAR_MODEL,
                )
            except (LLMConfigurationError, FinancialCalendarError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                refresh_error = str(exc)

        events = list_financial_events(
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            category=category,
            importance=importance,
        )
        if refresh_error and not events:
            raise HTTPException(status_code=502, detail=refresh_error)

        return {
            "status": "success",
            "start_date": parsed_start_date.isoformat(),
            "end_date": parsed_end_date.isoformat(),
            "events": events,
            "count": len(events),
            "refresh": refresh_status,
            "refresh_error": refresh_error,
        }
    except FinancialCalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/financial-calendar/refresh")
def refresh_financial_calendar_events(request: FinancialCalendarRefreshRequest) -> dict:
    today = get_today()
    try:
        parsed_start_date = parse_iso_date(request.start_date, today)
        parsed_end_date = parse_iso_date(
            request.end_date,
            default_end_date(parsed_start_date),
        )
        return refresh_financial_calendar(
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            model=request.model or DEFAULT_FINANCIAL_CALENDAR_MODEL,
        )
    except FinancialCalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def run_required_three_company_selection(request: NewResearchRequest) -> dict:
    try:
        return select_companies_from_url(
            url=str(request.url),
            provider=request.provider,
            model=request.model,
            max_companies=3,
            article_char_limit=request.article_char_limit,
            require_exact_count=True,
        )
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch the news article: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def build_frontend_company_payload(companies: list[dict]) -> list[dict]:
    frontend_companies: list[dict] = []

    for company in companies:
        score = round(float(company.get("confidence", 0) or 0), 3)
        market = str(company.get("market", "")).strip()
        korean_ticker = safe_normalize_ticker(company.get("ticker", ""))
        yahoo_ticker = safe_build_yahoo_symbol(
            ticker=korean_ticker,
            market=market,
        )
        name_ko = str(company.get("company_name_ko", "")).strip()
        name_en = str(company.get("company_name", "")).strip()

        frontend_companies.append(
            {
                "name": name_ko or name_en,
                "ticker": yahoo_ticker,
                "score": score,
                "score_percent": round(score * 100, 1),
                "company_name": name_en,
                "company_name_ko": name_ko,
                "korean_ticker": korean_ticker,
                "market": market,
                "risk_analysis": str(company.get("risk_analysis", "")).strip(),
            }
        )

    return frontend_companies


def build_static_file_url(http_request: Request, file_path: str | None) -> Optional[str]:
    if not file_path:
        return None

    resolved_path = Path(file_path).resolve()
    try:
        relative_path = resolved_path.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return None

    forwarded_proto = http_request.headers.get("x-forwarded-proto")
    forwarded_host = http_request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        base_url = f"{forwarded_proto}://{forwarded_host}".rstrip("/")
    else:
        base_url = str(http_request.base_url).rstrip("/")
    return f"{base_url}/static/{relative_path.as_posix()}"


def build_image_data_url(file_path: str | None) -> Optional[str]:
    if not file_path:
        return None

    path = Path(file_path)
    if not path.is_file():
        return None

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def add_chart_urls_to_companies(
    companies: list[dict],
    plot_results: list[dict],
    http_request: Request,
) -> list[dict]:
    plots_by_ticker = {
        str(plot.get("ticker", "")).strip(): plot
        for plot in plot_results
        if str(plot.get("ticker", "")).strip()
    }
    enriched_companies: list[dict] = []

    for company in companies:
        ticker = str(company.get("korean_ticker", "")).strip()
        plot = plots_by_ticker.get(ticker, {})
        daily_plot_path = plot.get("daily_plot_path")
        intraday_plot_path = plot.get("intraday_plot_path")
        plot_path = plot.get("plot_path")
        enriched_companies.append(
            {
                **company,
                "chart_url": build_static_file_url(http_request, plot_path),
                "chart_data_url": build_image_data_url(plot_path),
                "daily_chart_url": build_static_file_url(
                    http_request,
                    daily_plot_path,
                ),
                "daily_chart_data_url": build_image_data_url(
                    daily_plot_path,
                ),
                "intraday_chart_url": build_static_file_url(
                    http_request,
                    intraday_plot_path,
                ),
                "intraday_chart_data_url": build_image_data_url(
                    intraday_plot_path,
                ),
                "latest_close": plot.get("daily_latest_close") or plot.get("intraday_latest_close"),
                "daily_start_date": plot.get("daily_start_date"),
                "daily_end_date": plot.get("daily_end_date"),
                "intraday_start_date": plot.get("intraday_start_date"),
                "intraday_end_date": plot.get("intraday_end_date"),
                "chart_error": plot.get("error"),
            }
        )

    return enriched_companies


def map_by_ticker(items: list[dict]) -> dict[str, dict]:
    return {
        str(item.get("ticker", "")).strip(): item
        for item in items
        if str(item.get("ticker", "")).strip()
    }


def format_metric(value: object, suffix: str = "", digits: int = 2) -> Optional[str]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    number = round_decimal(number, digits)
    return f"{number:,.{digits}f}{suffix}"


def round_decimal(value: object, digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return round(number, digits)


def build_financial_analysis(fundamentals: dict) -> Optional[str]:
    if fundamentals.get("error"):
        return None

    metrics = fundamentals.get("valuation_metrics", {})
    per = format_metric(metrics.get("per"), "배")
    pbr = format_metric(metrics.get("pbr"), "배")
    roe = format_metric(metrics.get("roe"), "%")
    debt_ratio = format_metric(metrics.get("debt_ratio"), "%")
    operating_margin = format_metric(metrics.get("operating_margin"), "%")
    report_name = fundamentals.get("report_name")

    parts = []
    if per or pbr:
        valuation = " / ".join(
            item
            for item in (
                f"PER {per}" if per else None,
                f"PBR {pbr}" if pbr else None,
            )
            if item
        )
        parts.append(f"밸류에이션은 {valuation} 수준입니다.")
    if roe or operating_margin:
        profitability = " / ".join(
            item
            for item in (
                f"ROE {roe}" if roe else None,
                f"영업이익률 {operating_margin}" if operating_margin else None,
            )
            if item
        )
        parts.append(f"수익성 지표는 {profitability}입니다.")
    if debt_ratio:
        parts.append(f"부채비율은 {debt_ratio}입니다.")
    if report_name:
        parts.append(f"기준 보고서는 {report_name}입니다.")

    return " ".join(parts) if parts else None


def build_financial_metrics(fundamentals: dict) -> dict:
    metrics = fundamentals.get("valuation_metrics", {})
    return {
        "per": round_decimal(metrics.get("per")),
        "pbr": round_decimal(metrics.get("pbr")),
        "pcr": round_decimal(metrics.get("pcr")),
        "ev_to_ebitda": round_decimal(metrics.get("ev_to_ebitda")),
        "eps": round_decimal(metrics.get("eps")),
        "bps": round_decimal(metrics.get("bps")),
        "roe": round_decimal(metrics.get("roe")),
        "debt_ratio": round_decimal(metrics.get("debt_ratio")),
        "current_ratio": round_decimal(metrics.get("current_ratio")),
        "operating_margin": round_decimal(metrics.get("operating_margin")),
        "net_margin": round_decimal(metrics.get("net_margin")),
        "market_cap": round_decimal(
            metrics.get("market_cap") or fundamentals.get("market_cap")
        ),
        "shares_outstanding": round_decimal(
            metrics.get("shares_outstanding") or fundamentals.get("shares_outstanding")
        ),
        "business_year": fundamentals.get("business_year"),
        "report_name": fundamentals.get("report_name"),
        "statement_date": fundamentals.get("statement_date"),
        "source": fundamentals.get("source"),
    }


def build_institutional_financial_prompt(
    selected_companies: list[dict],
    fundamentals_companies: list[dict],
) -> str:
    payload = []
    selected_by_ticker = map_by_ticker(selected_companies)
    for fundamentals in fundamentals_companies:
        ticker = str(fundamentals.get("ticker", "")).strip()
        selected = selected_by_ticker.get(ticker, {})
        payload.append(
            {
                "ticker": ticker,
                "company_name_ko": (
                    fundamentals.get("company_name_ko")
                    or selected.get("company_name_ko")
                ),
                "company_name": (
                    fundamentals.get("company_name")
                    or selected.get("company_name")
                ),
                "market": fundamentals.get("market") or selected.get("market"),
                "news_investment_thesis": selected.get("rationale"),
                "article_relevance": selected.get("article_relevance"),
                "key_catalysts": selected.get("key_catalysts", []),
                "risks": selected.get("risks", []),
                "latest_close": fundamentals.get("latest_close"),
                "business_year": fundamentals.get("business_year"),
                "report_name": fundamentals.get("report_name"),
                "statement_date": fundamentals.get("statement_date"),
                "valuation_metrics": fundamentals.get("valuation_metrics", {}),
                "raw_indicator_values": fundamentals.get("raw_indicator_values", {}),
                "fundamental_error": fundamentals.get("error"),
            }
        )

    return f"""
You are a senior sell-side equity research analyst at a Korean securities firm.

Write institutional-grade financial statement and valuation analysis in Korean for each company.

Required analytical standard:
- Use the logic and language of professional Korean brokerage research.
- Start from the financial statements and ratio data provided, then connect them to valuation.
- Discuss profitability, growth quality, balance-sheet risk, cash-flow quality, and valuation burden or upside.
- Explain how metrics such as PER, PBR, ROE, operating margin, debt ratio, EV/EBITDA, EPS, BPS, and market cap affect the investment view.
- If data is missing, state the limitation explicitly and avoid inventing numbers.
- When valuation is high, explain what earnings growth, ROE, margin expansion, or catalyst would be needed to justify it.
- When valuation is low, explain whether it looks like undervaluation or a value trap using profitability, leverage, and earnings visibility.
- Do not give generic textbook definitions. Write as if this will be shown to finance professionals.
- Keep each company's analysis as one dense Korean paragraph of 4 to 7 sentences.
- Include nuanced investment logic, not a simple buy/sell slogan.
- Use a warm Korean explanatory tone ending mostly with "~해요", "~이에요", "~일 수 있어요", or "~로 보여요".
- Avoid stiff report endings such as "~합니다", "~입니다", "~된다", and "~판단된다" unless unavoidable.
- Keep the analytical depth and sell-side valuation logic, but make the wording feel approachable for a web product.

Return only valid JSON matching this shape:
{{
  "companies": [
    {{
      "ticker": "005930",
      "financial_analysis": "Korean institutional valuation analysis paragraph"
    }}
  ]
}}

Input companies and financial data:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def build_financial_analysis_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ticker": {"type": "string"},
                        "financial_analysis": {"type": "string"},
                    },
                    "required": ["ticker", "financial_analysis"],
                },
            }
        },
        "required": ["companies"],
    }


def run_openai_financial_analysis(
    prompt: str,
    schema: dict[str, Any],
    model: Optional[str],
) -> dict[str, Any]:
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not set.")

    client = get_openai_client_class()(api_key=api_key)
    response = client.responses.create(
        model=model or "gpt-4o",
        input=prompt,
        store=False,
        text={
            "format": {
                "type": "json_schema",
                "name": "institutional_financial_analysis",
                "strict": True,
                "schema": schema,
            }
        },
    )
    if not response.output_text:
        raise RuntimeError("OpenAI returned an empty financial analysis.")
    return json.loads(response.output_text)


def run_gemini_financial_analysis(
    prompt: str,
    schema: dict[str, Any],
    model: Optional[str],
) -> dict[str, Any]:
    genai_module, genai_types_module = get_gemini_modules()
    api_key = normalize_env_api_key(os.getenv("GEMINI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("GEMINI_API_KEY is not set.")

    client = genai_module.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or "gemini-2.5-flash",
        contents=prompt,
        config=genai_types_module.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty financial analysis.")
    return json.loads(response.text)


def generate_institutional_financial_analyses(
    selected_companies: list[dict],
    fundamentals_companies: list[dict],
    provider: str,
    model: Optional[str],
) -> dict[str, str]:
    prompt = build_institutional_financial_prompt(
        selected_companies=selected_companies,
        fundamentals_companies=fundamentals_companies,
    )
    schema = build_financial_analysis_schema()
    provider = provider.lower()

    if provider == "openai":
        payload = run_openai_financial_analysis(prompt, schema, model)
    elif provider == "gemini":
        payload = run_gemini_financial_analysis(prompt, schema, model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    analyses: dict[str, str] = {}
    for company in payload.get("companies", []):
        ticker = safe_normalize_ticker(company.get("ticker", ""))
        text = str(company.get("financial_analysis", "")).strip()
        if ticker and text:
            analyses[ticker] = text
    return analyses


TECHNICAL_ANALYSIS_PROMPT_TEMPLATE = """
You are a technical analyst with over 15 years of experience at the research center of a leading Korean securities firm.

Based on the provided technical indicators, generate a professional technical analysis report comparable to one produced by a sell-side equity research analyst.

## Analysis Principles

1. Never draw conclusions based on a single indicator.
2. Confirm whether multiple indicators support the same conclusion before making a judgment.
3. If conflicting signals exist, explicitly explain them and discuss which signal is more reliable and why.
4. Do not simply list indicator values; interpret their implications.
5. Write at a level appropriate for finance professionals, graduate students in finance, or equity research analysts.
6. Avoid absolute statements such as "guaranteed uptrend" or "strong buy."
7. Your analysis should be based solely on the current technical conditions and should not make definitive predictions about future price movements.

------------------------------------------------

Input Data

{{technical_indicator_json}}

------------------------------------------------

Please analyze the following sections in order.

# 1. Trend

Analyze the following indicators collectively:

- SMA 20
- SMA 50
- EMA 20
- Current closing price relative to moving averages
- Moving average alignment
- ADX
- +DI
- -DI

Include the following points:

- Whether the market is currently in an uptrend, downtrend, or sideways trend
- Trend strength
- Sustainability of the current trend
- Presence of Golden Cross or Death Cross
- Relationship between the short-term and medium-term trends

------------------------------------------------

# 2. Momentum

Analyze the following indicators:

- RSI
- MACD
- MACD Signal
- MACD Histogram
- Stochastic %K
- Stochastic %D

Discuss:

- Whether bullish momentum is strengthening or weakening
- Whether bearish momentum is strengthening or weakening
- Overbought or oversold conditions
- Whether MACD and RSI provide consistent signals
- Whether the Stochastic Oscillator provides an early reversal signal

------------------------------------------------

# 3. Volatility

Analyze:

- Bollinger Bands
- Bollinger Band Width
- ATR

Discuss:

- Whether volatility is expanding or contracting
- The current price position within the Bollinger Bands
- The possibility of a breakout following a Bollinger Band squeeze
- The significance of the ATR level regarding recent price fluctuations

------------------------------------------------

# 4. Volume and Money Flow

Analyze:

- OBV
- OBV SMA 5
- OBV SMA 20
- Volume SMA 20

Discuss:

- Whether trading volume supports the current price trend
- Whether institutional or market participation appears to be increasing
- Whether price appreciation is accompanied by sufficient trading volume
- Whether volume strengthens or weakens the reliability of the current trend

------------------------------------------------

# 5. Short-Term Price Action

Analyze:

- 3-day return
- 5-day return

Discuss:

- Recent short-term price performance
- Whether momentum is accelerating or decelerating
- Possibility of short-term overheating
- Whether recent price movements are consistent with the broader trend

------------------------------------------------

# 6. Overall Assessment

Integrate all of the above analyses and provide:

### (1) Current Technical Position

Select the most appropriate description and explain your reasoning.

Examples include:

- Early-stage uptrend
- Sustained uptrend
- Overextended uptrend
- Sideways consolidation
- Technical rebound
- Continuing downtrend

### (2) Bullish Signals

Identify the 2-4 strongest bullish technical factors.

### (3) Bearish Signals

Identify the 2-4 strongest bearish technical factors.

### (4) Key Technical Signals to Monitor

Explain the most important technical developments that investors should watch next.

Examples include:

- RSI moving above 70
- MACD maintaining a bullish crossover
- Rising ADX
- Increasing trading volume
- Breakout above the upper Bollinger Band

------------------------------------------------

# Writing Style

- Write in the style of a professional equity research report.
- Use concise, well-structured paragraphs rather than bullet-heavy explanations.
- Focus on interpretation instead of repeating numerical values.
- Use a warm Korean explanatory tone ending mostly with "~해요", "~이에요", "~일 수 있어요", or "~로 보여요".
- Avoid stiff report endings such as "~합니다", "~입니다", "~된다", and "~판단된다" unless unavoidable.
- Keep the analysis professional, but make it read like a clear web-product explanation rather than a formal PDF report.
- Use expressions such as:
  - "suggests"
  - "indicates"
  - "is consistent with"
  - "supports the view that"
  - "implies"
  - "appears to"
- Integrate multiple indicators into a coherent interpretation rather than discussing each indicator independently.

Example:

"The short-term moving averages remain above the medium-term moving averages, while the ADX indicates improving trend strength. Together, these signals suggest that the prevailing uptrend remains intact. However, the RSI is approaching overbought territory, implying that upside momentum may gradually moderate in the near term."

------------------------------------------------

# Output Format

## Trend
(Analysis)

## Momentum
(Analysis)

## Volatility
(Analysis)

## Volume and Money Flow
(Analysis)

## Short-Term Price Action
(Analysis)

## Overall Assessment
(Analysis)

------------------------------------------------

Provide the entire response in Korean.
""".strip()


def build_technical_indicator_payload(
    technical_companies: list[dict],
    opinions: list[dict],
) -> list[dict]:
    opinion_by_ticker = map_by_ticker(opinions)
    payload: list[dict] = []

    for technical in technical_companies:
        ticker = str(technical.get("ticker", "")).strip()
        opinion = opinion_by_ticker.get(ticker, {})
        payload.append(
            {
                "ticker": ticker,
                "company_name_ko": technical.get("company_name_ko"),
                "company_name": technical.get("company_name"),
                "market": technical.get("market"),
                "yahoo_symbol": technical.get("yahoo_symbol"),
                "row_count": technical.get("row_count"),
                "latest_date": technical.get("latest_date"),
                "latest_close": technical.get("latest_close"),
                "latest_indicators": technical.get("latest_indicators", {}),
                "signal_context": technical.get("signal_context", {}),
                "latest_signal": technical.get("latest_signal", {}),
                "recent_rows": technical.get("recent_rows", []),
                "rule_based_opinion": {
                    "opinion": opinion.get("opinion"),
                    "score": opinion.get("score"),
                    "confidence": opinion.get("confidence"),
                    "risk_level": opinion.get("risk_level"),
                    "rationale": opinion.get("rationale"),
                    "positives": opinion.get("positives", []),
                    "negatives": opinion.get("negatives", []),
                },
                "technical_error": technical.get("error") or opinion.get("error"),
            }
        )

    return payload


def build_institutional_technical_prompt(
    technical_companies: list[dict],
    opinions: list[dict],
) -> str:
    payload = {
        "companies": build_technical_indicator_payload(
            technical_companies=technical_companies,
            opinions=opinions,
        )
    }
    prompt = TECHNICAL_ANALYSIS_PROMPT_TEMPLATE.replace(
        "{{technical_indicator_json}}",
        json.dumps(payload, ensure_ascii=False, indent=2),
    )
    return f"""
{prompt}

Return only valid JSON matching this shape:
{{
  "companies": [
    {{
      "ticker": "005930",
      "technical_analysis_text": "Korean technical analysis report using the requested section format",
      "technical_highlights": [
        {{
          "type": "positive",
          "importance": "high",
          "title": "MACD bullish crossover",
          "detail": "Korean explanation of why this deserves visual emphasis"
        }}
      ]
    }}
  ]
}}

Analyze every company in the input data. Keep each technical_analysis_text in Korean and include the section headings requested above inside the string.
Use the same warm Korean explanatory tone in technical_analysis_text and technical_highlights.detail: mostly "~해요", "~이에요", "~일 수 있어요", or "~로 보여요", while preserving finance-professional analytical depth.

For technical_highlights, identify 2 to 4 items that deserve visual emphasis in the frontend.
- type must be one of: positive, negative, watch.
- importance must be one of: high, medium, low.
- Use high only for the most decision-relevant signals, such as aligned trend/momentum confirmation, major conflicting signals, overbought/oversold risk, volatility breakout setup, or volume confirmation/failure.
- title should be short enough for a UI badge.
- detail should explain why the point matters to a finance professional.
""".strip()


def build_technical_analysis_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ticker": {"type": "string"},
                        "technical_analysis_text": {"type": "string"},
                        "technical_highlights": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["positive", "negative", "watch"],
                                    },
                                    "importance": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                    },
                                    "title": {"type": "string"},
                                    "detail": {"type": "string"},
                                },
                                "required": [
                                    "type",
                                    "importance",
                                    "title",
                                    "detail",
                                ],
                            },
                        },
                    },
                    "required": [
                        "ticker",
                        "technical_analysis_text",
                        "technical_highlights",
                    ],
                },
            }
        },
        "required": ["companies"],
    }


def run_openai_technical_analysis(
    prompt: str,
    schema: dict[str, Any],
    model: Optional[str],
) -> dict[str, Any]:
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not set.")

    client = get_openai_client_class()(api_key=api_key)
    response = client.responses.create(
        model=model or "gpt-4o",
        input=prompt,
        store=False,
        text={
            "format": {
                "type": "json_schema",
                "name": "institutional_technical_analysis",
                "strict": True,
                "schema": schema,
            }
        },
    )
    if not response.output_text:
        raise RuntimeError("OpenAI returned an empty technical analysis.")
    return json.loads(response.output_text)


def run_gemini_technical_analysis(
    prompt: str,
    schema: dict[str, Any],
    model: Optional[str],
) -> dict[str, Any]:
    genai_module, genai_types_module = get_gemini_modules()
    api_key = normalize_env_api_key(os.getenv("GEMINI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("GEMINI_API_KEY is not set.")

    client = genai_module.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or "gemini-2.5-flash",
        contents=prompt,
        config=genai_types_module.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty technical analysis.")
    return json.loads(response.text)


def generate_institutional_technical_analyses(
    technical_companies: list[dict],
    opinions: list[dict],
    provider: str,
    model: Optional[str],
) -> dict[str, dict[str, Any]]:
    prompt = build_institutional_technical_prompt(
        technical_companies=technical_companies,
        opinions=opinions,
    )
    schema = build_technical_analysis_schema()
    provider = provider.lower()

    if provider == "openai":
        payload = run_openai_technical_analysis(prompt, schema, model)
    elif provider == "gemini":
        payload = run_gemini_technical_analysis(prompt, schema, model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    analyses: dict[str, dict[str, Any]] = {}
    for company in payload.get("companies", []):
        ticker = safe_normalize_ticker(company.get("ticker", ""))
        text = str(company.get("technical_analysis_text", "")).strip()
        highlights = company.get("technical_highlights", [])
        if not isinstance(highlights, list):
            highlights = []
        if ticker:
            analyses[ticker] = {
                "technical_analysis_text": text,
                "technical_highlights": highlights,
            }
    return analyses


def add_analysis_to_companies(
    companies: list[dict],
    selected_companies: list[dict],
    daily_market_data: list[dict],
    technical_companies: list[dict],
    opinions: list[dict],
    fundamentals_companies: list[dict],
    financial_analysis_by_ticker: dict[str, str],
    technical_analysis_by_ticker: dict[str, dict[str, Any]],
) -> list[dict]:
    selected_by_ticker = map_by_ticker(selected_companies)
    market_by_ticker = map_by_ticker(daily_market_data)
    technical_by_ticker = map_by_ticker(technical_companies)
    opinion_by_ticker = map_by_ticker(opinions)
    fundamentals_by_ticker = map_by_ticker(fundamentals_companies)
    enriched_companies: list[dict] = []

    for company in companies:
        ticker = str(company.get("korean_ticker", "")).strip()
        selected = selected_by_ticker.get(ticker, {})
        market = market_by_ticker.get(ticker, {})
        technical = technical_by_ticker.get(ticker, {})
        opinion = opinion_by_ticker.get(ticker, {})
        fundamentals = fundamentals_by_ticker.get(ticker, {})
        financial_analysis = (
            financial_analysis_by_ticker.get(ticker)
            or build_financial_analysis(fundamentals)
        )
        ai_technical_analysis = technical_analysis_by_ticker.get(ticker, {})
        technical_analysis_text = ai_technical_analysis.get("technical_analysis_text")
        technical_highlights = ai_technical_analysis.get("technical_highlights", [])
        latest_indicators = technical.get("latest_indicators", {})

        enriched_companies.append(
            {
                **company,
                "latest_close": market.get("latest_close") or technical.get("latest_close"),
                "latest_close_date": market.get("end_date") or technical.get("latest_date"),
                "currency": market.get("currency"),
                "ai_opinion": selected.get("rationale") or selected.get("article_relevance"),
                "recommendation_reason": selected.get("rationale"),
                "article_relevance": selected.get("article_relevance"),
                "key_catalysts": selected.get("key_catalysts", []),
                "risks": selected.get("risks", []),
                "risk_analysis": selected.get("risk_analysis"),
                "technical_opinion": opinion.get("opinion"),
                "technical_opinion_score": opinion.get("score"),
                "technical_confidence": opinion.get("confidence"),
                "risk_level": opinion.get("risk_level"),
                "opinion_rationale": opinion.get("rationale"),
                "technical_analysis_text": technical_analysis_text,
                "ai_technical_analysis": technical_analysis_text,
                "technical_highlights": technical_highlights,
                "positives": opinion.get("positives", []),
                "negatives": opinion.get("negatives", []),
                "financial_analysis": financial_analysis,
                "financial_metrics": build_financial_metrics(fundamentals),
                "financial_error": fundamentals.get("error"),
                "technical_summary": {
                    "rsi_14": latest_indicators.get("rsi_14"),
                    "macd": latest_indicators.get("macd"),
                    "macd_signal": latest_indicators.get("macd_signal"),
                    "sma_20": latest_indicators.get("sma_20"),
                    "sma_50": latest_indicators.get("sma_50"),
                    "latest_signal": technical.get("latest_signal", {}),
                },
                "analysis_error": (
                    market.get("error")
                    or technical.get("error")
                    or opinion.get("error")
                    or fundamentals.get("error")
                ),
            }
        )

    return enriched_companies


def build_chart_research_response(
    payload: ChartResearchRequest,
    http_request: Request,
) -> dict:
    result = run_required_three_company_selection(payload)
    selected_companies = result["selection"]["companies"]

    daily_market_data = fetch_market_data_for_companies(
        companies=selected_companies,
        period=payload.daily_plot_period,
        interval=payload.daily_plot_interval,
    )
    intraday_market_data = fetch_market_data_for_companies(
        companies=selected_companies,
        period=payload.intraday_plot_period,
        interval=payload.intraday_plot_interval,
    )
    plot_results = generate_report_price_plots(
        daily_companies=daily_market_data,
        intraday_companies=intraday_market_data,
        output_dir=str(PLOTS_DIR),
        daily_recent_points=payload.daily_recent_points,
        intraday_recent_points=payload.intraday_recent_points,
        clear_output_dir=False,
    )
    technical_companies = analyze_market_data_companies(
        daily_market_data,
        recent_rows=payload.recent_rows,
    )
    opinions = derive_company_opinions(technical_companies)
    try:
        technical_analysis_by_ticker = generate_institutional_technical_analyses(
            technical_companies=technical_companies,
            opinions=opinions,
            provider=result["provider"],
            model=result["model"],
        )
        technical_analysis_error = None
    except (LLMConfigurationError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        technical_analysis_by_ticker = {}
        technical_analysis_error = str(exc)

    fundamentals_companies = analyze_market_data_fundamentals(daily_market_data)
    try:
        financial_analysis_by_ticker = generate_institutional_financial_analyses(
            selected_companies=selected_companies,
            fundamentals_companies=fundamentals_companies,
            provider=result["provider"],
            model=result["model"],
        )
        financial_analysis_error = None
    except (LLMConfigurationError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        financial_analysis_by_ticker = {}
        financial_analysis_error = str(exc)

    companies_with_charts = add_chart_urls_to_companies(
        companies=build_frontend_company_payload(selected_companies),
        plot_results=plot_results,
        http_request=http_request,
    )
    companies = add_analysis_to_companies(
        companies=companies_with_charts,
        selected_companies=selected_companies,
        daily_market_data=daily_market_data,
        technical_companies=technical_companies,
        opinions=opinions,
        fundamentals_companies=fundamentals_companies,
        financial_analysis_by_ticker=financial_analysis_by_ticker,
        technical_analysis_by_ticker=technical_analysis_by_ticker,
    )

    return {
        "status": "success",
        "summary": result["selection"].get("summary", ""),
        "companies": companies,
        "data_strategy": {
            "analysis_payload": "bundled",
            "chart_images": "url",
            "realtime_price_ready": True,
        },
        "charts": {
            "daily_plot_period": payload.daily_plot_period,
            "daily_plot_interval": payload.daily_plot_interval,
            "intraday_plot_period": payload.intraday_plot_period,
            "intraday_plot_interval": payload.intraday_plot_interval,
            "companies": plot_results,
        },
        "technical_analysis": {
            "recent_rows": payload.recent_rows,
            "prompt_version": "institutional_sell_side_v1",
            "llm_analysis_error": technical_analysis_error,
            "companies": technical_companies,
        },
        "opinions": {
            "method": "regime_aware_technical_score_engine_v3",
            "companies": opinions,
        },
        "fundamentals": {
            "source": "OpenDART",
            "llm_analysis_error": financial_analysis_error,
            "companies": fundamentals_companies,
        },
        "article": result["article"],
        "provider": result["provider"],
        "model": result["model"],
        "selection": result["selection"],
    }


@app.post("/api/new-research")
def create_new_research(request: NewResearchRequest) -> dict:
    result = run_required_three_company_selection(request)
    companies = build_frontend_company_payload(
        result["selection"]["companies"]
    )

    return {
        "status": "success",
        "summary": result["selection"].get("summary", ""),
        "companies": companies,
        "article": result["article"],
        "provider": result["provider"],
        "model": result["model"],
        "selection": result["selection"],
    }


@app.post("/api/new-research-with-charts")
def create_new_research_with_charts(
    payload: ChartResearchRequest,
    http_request: Request,
) -> dict:
    return build_chart_research_response(payload, http_request)


@app.post("/api/company-dashboard")
def get_company_dashboard(
    payload: ChartResearchRequest,
    http_request: Request,
) -> dict:
    return build_chart_research_response(payload, http_request)


@app.post("/api/recommended-companies")
def get_recommended_companies(request: NewResearchRequest) -> dict:
    result = run_required_three_company_selection(request)
    companies = build_frontend_company_payload(result["selection"]["companies"])

    return {
        "status": "success",
        "summary": result["selection"]["summary"],
        "companies": companies,
    }


@app.post("/api/recommended-companies-with-charts")
def get_recommended_companies_with_charts(
    payload: ChartResearchRequest,
    http_request: Request,
) -> dict:
    result = build_chart_research_response(payload, http_request)
    return {
        "status": result["status"],
        "summary": result["summary"],
        "companies": result["companies"],
        "charts": result["charts"],
    }
