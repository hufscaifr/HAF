from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

import requests

from cam_pipeline.article_scraper import scrape_article
from cam_pipeline.company_selector import (
    DEFAULT_PROVIDER,
    LLMConfigurationError,
    select_companies_from_url,
)
from cam_pipeline.fundamentals_data import fetch_selection_fundamentals
from cam_pipeline.market_data import fetch_selection_market_data
from cam_pipeline.opinion_engine import fetch_selection_opinions
from cam_pipeline.price_plot import (
    DEFAULT_DAILY_PLOT_INTERVAL,
    DEFAULT_DAILY_PLOT_PERIOD,
    DEFAULT_DAILY_RECENT_POINTS,
    DEFAULT_PLOT_INTERVAL,
    DEFAULT_PLOT_PERIOD,
    DEFAULT_RECENT_POINTS,
    fetch_selection_price_plots,
)
from cam_pipeline.research_report import fetch_selection_research_report
from cam_pipeline.report_pipeline import fetch_selection_report
from cam_pipeline.technical_analysis import fetch_selection_technical_analysis
from cam_pipeline.word_report import fetch_selection_word_report


COMMANDS = {"scrape", "select", "ohlcv", "indicators", "fundamentals", "opinion", "plot", "report", "research", "word-report"}
INDICATOR_DISPLAY_ORDER = [
    ("close", "종가"),
    ("sma_20", "SMA20"),
    ("sma_50", "SMA50"),
    ("ema_20", "EMA20"),
    ("rsi_14", "RSI14"),
    ("macd", "MACD"),
    ("macd_signal", "MACD Signal"),
    ("macd_histogram", "MACD Histogram"),
    ("bb_lower", "Bollinger Lower"),
    ("bb_middle", "Bollinger Middle"),
    ("bb_upper", "Bollinger Upper"),
    ("bb_width", "Bollinger Width"),
    ("atr_14", "ATR14"),
    ("adx_14", "ADX14"),
    ("dmp_14", "+DI14"),
    ("dmn_14", "-DI14"),
    ("stoch_k", "Stochastic %K"),
    ("stoch_d", "Stochastic %D"),
    ("obv", "OBV"),
    ("obv_sma_5", "OBV SMA5"),
    ("obv_sma_20", "OBV SMA20"),
    ("volume_sma_20", "Volume SMA20"),
    ("return_3", "3일 수익률"),
    ("return_5", "5일 수익률"),
]
FUNDAMENTAL_DISPLAY_ORDER = [
    ("per", "PER"),
    ("pbr", "PBR"),
    ("pcr", "PCR"),
    ("ev_to_ebitda", "EV/EBITDA"),
    ("eps", "EPS"),
    ("bps", "BPS"),
    ("ebitda", "EBITDA"),
    ("cash_dps", "CashDPS"),
    ("cash_dividend_yield", "Cash Dividend Yield"),
    ("roe", "ROE"),
    ("debt_ratio", "부채비율"),
    ("current_ratio", "유동비율"),
    ("operating_margin", "영업이익률"),
    ("net_margin", "순이익률"),
    ("market_cap", "시가총액"),
    ("shares_outstanding", "발행주식수"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Corporate analysis model pipeline."
    )
    subparsers = parser.add_subparsers(dest="command")

    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Step 1: scrape a news article from a URL",
    )
    scrape_parser.add_argument("url", help="News article URL to scrape")
    scrape_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the scraped article as JSON",
    )

    select_parser = subparsers.add_parser(
        "select",
        help="Step 2: use an LLM to select promising KOSPI/KOSDAQ companies",
    )
    select_parser.add_argument("url", help="News article URL to analyze")
    select_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use",
    )
    select_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    select_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return",
    )
    select_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    select_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the selection result as JSON",
    )

    ohlcv_parser = subparsers.add_parser(
        "ohlcv",
        help="Step 3: fetch Yahoo Finance OHLCV data for selected companies",
    )
    ohlcv_parser.add_argument("url", help="News article URL to analyze")
    ohlcv_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection",
    )
    ohlcv_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    ohlcv_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    ohlcv_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    ohlcv_parser.add_argument(
        "--period",
        default="6mo",
        help="Yahoo Finance history period such as 1mo, 3mo, 6mo, 1y",
    )
    ohlcv_parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval such as 1d, 1wk, 1mo",
    )
    ohlcv_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the OHLCV result as JSON",
    )

    indicators_parser = subparsers.add_parser(
        "indicators",
        help="Step 4: calculate technical indicators from OHLCV data",
    )
    indicators_parser.add_argument("url", help="News article URL to analyze")
    indicators_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection",
    )
    indicators_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    indicators_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    indicators_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    indicators_parser.add_argument(
        "--period",
        default="6mo",
        help="Yahoo Finance history period such as 1mo, 3mo, 6mo, 1y",
    )
    indicators_parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval such as 1d, 1wk, 1mo",
    )
    indicators_parser.add_argument(
        "--recent-rows",
        type=int,
        default=5,
        help="Number of recent indicator rows to include per company",
    )
    indicators_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the technical analysis result as JSON",
    )

    fundamentals_parser = subparsers.add_parser(
        "fundamentals",
        help="Step 4B: fetch DART financial indicators such as EPS and PBR",
    )
    fundamentals_parser.add_argument("url", help="News article URL to analyze")
    fundamentals_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection",
    )
    fundamentals_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    fundamentals_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    fundamentals_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    fundamentals_parser.add_argument(
        "--period",
        default="6mo",
        help="Price-history period used to source the latest close price",
    )
    fundamentals_parser.add_argument(
        "--interval",
        default="1d",
        help="Price-history interval used to source the latest close price",
    )
    fundamentals_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the fundamentals result as JSON",
    )

    opinion_parser = subparsers.add_parser(
        "opinion",
        help="Step 5: derive buy/sell opinions from the technical indicators",
    )
    opinion_parser.add_argument("url", help="News article URL to analyze")
    opinion_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection",
    )
    opinion_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    opinion_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    opinion_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    opinion_parser.add_argument(
        "--period",
        default="6mo",
        help="Yahoo Finance history period such as 1mo, 3mo, 6mo, 1y",
    )
    opinion_parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval such as 1d, 1wk, 1mo",
    )
    opinion_parser.add_argument(
        "--recent-rows",
        type=int,
        default=5,
        help="Number of recent indicator rows to include per company",
    )
    opinion_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the opinion result as JSON",
    )

    plot_parser = subparsers.add_parser(
        "plot",
        help="Step 6: save recent stock-price plots for selected companies",
    )
    plot_parser.add_argument("url", help="News article URL to analyze")
    plot_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection",
    )
    plot_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    plot_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    plot_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    plot_parser.add_argument(
        "--period",
        default=DEFAULT_PLOT_PERIOD,
        help="Yahoo Finance chart period such as 1d, 5d, 1mo",
    )
    plot_parser.add_argument(
        "--interval",
        default=DEFAULT_PLOT_INTERVAL,
        help="Yahoo Finance chart interval such as 1m, 5m, 1d",
    )
    plot_parser.add_argument(
        "--recent-points",
        type=int,
        default=DEFAULT_RECENT_POINTS,
        help="Number of most recent price points to include in each chart",
    )
    plot_parser.add_argument(
        "--output-dir",
        default="plots",
        help="Directory where PNG plot files will be saved",
    )
    plot_parser.add_argument(
        "--clear-output-dir",
        action="store_true",
        help="Delete existing PNG plot files in the output directory before saving new ones",
    )
    plot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the plot result as JSON",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Run opinions and price plots together in a single command",
    )
    report_parser.add_argument("url", help="News article URL to analyze")
    report_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection",
    )
    report_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    report_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    report_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    report_parser.add_argument(
        "--period",
        default="6mo",
        help="Yahoo Finance history period such as 1mo, 3mo, 6mo, 1y",
    )
    report_parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval such as 1d, 1wk, 1mo",
    )
    report_parser.add_argument(
        "--recent-rows",
        type=int,
        default=5,
        help="Number of recent indicator rows to include per company",
    )
    report_parser.add_argument(
        "--recent-points",
        type=int,
        default=DEFAULT_RECENT_POINTS,
        help="Number of most recent intraday price points to include in each chart",
    )
    report_parser.add_argument(
        "--daily-plot-period",
        default=DEFAULT_DAILY_PLOT_PERIOD,
        help="Yahoo Finance period used for daily chart images, such as 3mo",
    )
    report_parser.add_argument(
        "--daily-plot-interval",
        default=DEFAULT_DAILY_PLOT_INTERVAL,
        help="Yahoo Finance interval used for daily chart images, such as 1d",
    )
    report_parser.add_argument(
        "--daily-recent-points",
        type=int,
        default=DEFAULT_DAILY_RECENT_POINTS,
        help="Number of most recent daily price points to include in each chart",
    )
    report_parser.add_argument(
        "--plot-period",
        default=DEFAULT_PLOT_PERIOD,
        help="Yahoo Finance period used only for chart images, such as 1d or 5d",
    )
    report_parser.add_argument(
        "--plot-interval",
        default=DEFAULT_PLOT_INTERVAL,
        help="Yahoo Finance interval used only for chart images, such as 1m or 5m",
    )
    report_parser.add_argument(
        "--output-dir",
        default="plots",
        help="Directory where PNG plot files will be saved",
    )
    report_parser.add_argument(
        "--clear-output-dir",
        action="store_true",
        help="Delete existing PNG plot files in the output directory before saving new ones",
    )
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the combined report result as JSON",
    )

    research_parser = subparsers.add_parser(
        "research",
        help="Write an LLM-based Korean institutional research report from the calculated data",
    )
    research_parser.add_argument("url", help="News article URL to analyze")
    research_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection and report writing",
    )
    research_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    research_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    research_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    research_parser.add_argument(
        "--period",
        default="6mo",
        help="Yahoo Finance history period such as 1mo, 3mo, 6mo, 1y",
    )
    research_parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval such as 1d, 1wk, 1mo",
    )
    research_parser.add_argument(
        "--recent-rows",
        type=int,
        default=5,
        help="Number of recent indicator rows to include per company",
    )
    research_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the research report result as JSON",
    )

    word_report_parser = subparsers.add_parser(
        "word-report",
        help="Create a Microsoft Word research report with tables and stock-price plots",
    )
    word_report_parser.add_argument("url", help="News article URL to analyze")
    word_report_parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default=DEFAULT_PROVIDER,
        help="LLM provider to use for company selection and report writing",
    )
    word_report_parser.add_argument(
        "--model",
        help="Override the default model for the chosen provider",
    )
    word_report_parser.add_argument(
        "--max-companies",
        type=int,
        default=3,
        help="Maximum number of companies to return from the LLM step",
    )
    word_report_parser.add_argument(
        "--article-char-limit",
        type=int,
        default=12000,
        help="Maximum number of article characters to send to the LLM",
    )
    word_report_parser.add_argument(
        "--period",
        default="6mo",
        help="Yahoo Finance history period such as 1mo, 3mo, 6mo, 1y",
    )
    word_report_parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval such as 1d, 1wk, 1mo",
    )
    word_report_parser.add_argument(
        "--recent-rows",
        type=int,
        default=5,
        help="Number of recent indicator rows to include per company",
    )
    word_report_parser.add_argument(
        "--recent-points",
        type=int,
        default=DEFAULT_RECENT_POINTS,
        help="Number of most recent intraday price points to include in each chart",
    )
    word_report_parser.add_argument(
        "--daily-plot-period",
        default=DEFAULT_DAILY_PLOT_PERIOD,
        help="Yahoo Finance period used for daily chart images, such as 3mo",
    )
    word_report_parser.add_argument(
        "--daily-plot-interval",
        default=DEFAULT_DAILY_PLOT_INTERVAL,
        help="Yahoo Finance interval used for daily chart images, such as 1d",
    )
    word_report_parser.add_argument(
        "--daily-recent-points",
        type=int,
        default=DEFAULT_DAILY_RECENT_POINTS,
        help="Number of most recent daily price points to include in each chart",
    )
    word_report_parser.add_argument(
        "--plot-period",
        default=DEFAULT_PLOT_PERIOD,
        help="Yahoo Finance period used only for chart images, such as 1d or 5d",
    )
    word_report_parser.add_argument(
        "--plot-interval",
        default=DEFAULT_PLOT_INTERVAL,
        help="Yahoo Finance interval used only for chart images, such as 1m or 5m",
    )
    word_report_parser.add_argument(
        "--output-dir",
        default="word_reports",
        help="Directory where the Word report and plot image files will be saved",
    )
    word_report_parser.add_argument(
        "--template-path",
        help="Optional .docx template path to reuse for Word report design",
    )
    word_report_parser.add_argument(
        "--clear-output-dir",
        action="store_true",
        help="Delete existing PNG plot files in the report plot directory before saving new ones",
    )
    word_report_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the Word report result as JSON",
    )

    return parser


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = build_parser()
    raw_args = list(sys.argv[1:] if argv is None else argv)

    if raw_args and raw_args[0] not in COMMANDS and raw_args[0] not in {"-h", "--help"}:
        raw_args = ["scrape", *raw_args]

    return parser.parse_args(raw_args)


def print_article(article: dict) -> None:
    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Extractor: {article['extractor']}")
    print()
    print(article["text"] or "No article text could be extracted.")


def format_indicator_value(key: str, value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if key.startswith("return_") or key.endswith("_yield"):
            if key.startswith("return_"):
                return f"{value * 100:.2f}%"
            return f"{value:.2f}%"
        return f"{value:.4f}"
    return str(value)


def print_indicator_values(indicators: dict) -> None:
    print("   기술적 지표 값:")
    for key, label in INDICATOR_DISPLAY_ORDER:
        print(f"     {label}: {format_indicator_value(key, indicators.get(key))}")


def print_fundamental_values(metrics: dict) -> None:
    print("   재무 지표 값:")
    for key, label in FUNDAMENTAL_DISPLAY_ORDER:
        print(f"     {label}: {format_indicator_value(key, metrics.get(key))}")


def print_selection(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print()
    print(selection["summary"])
    print()

    companies = selection["companies"]
    if not companies:
        print("No sufficiently confident KOSPI/KOSDAQ companies were selected.")
        return

    for index, company in enumerate(companies, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']}"
        )
        print(f"   Confidence: {company['confidence']}")
        print(f"   Rationale: {company['rationale']}")
        print(f"   Article relevance: {company['article_relevance']}")
        print(f"   Key catalysts: {', '.join(company['key_catalysts'])}")
        print(f"   Risks: {', '.join(company['risks'])}")
        print()


def print_ohlcv_result(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]
    market_data = result["market_data"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(
        f"Price history: period={market_data['period']}, interval={market_data['interval']}"
    )
    print()
    print(selection["summary"])
    print()

    companies = market_data["companies"]
    if not companies:
        print("No OHLCV data was fetched because no companies were selected.")
        return

    for index, company in enumerate(companies, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']} -> {company['yahoo_symbol']}"
        )
        if company.get("error"):
            print(f"   Error: {company['error']}")
            print()
            continue

        print(f"   Rows: {company['row_count']}")
        print(
            f"   Range: {company['start_date'] or 'N/A'} -> "
            f"{company['end_date'] or 'N/A'}"
        )
        print(f"   Latest close: {company['latest_close']}")
        print(f"   Latest volume: {company['latest_volume']}")
        print(f"   Currency: {company['currency'] or 'N/A'}")
        print()


def print_indicator_result(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]
    technical = result["technical_analysis"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Indicators: {', '.join(technical['indicators'])}")
    print()
    print(selection["summary"])
    print()

    companies = technical["companies"]
    if not companies:
        print("No technical analysis was produced because no companies were selected.")
        return

    for index, company in enumerate(companies, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']} -> {company['yahoo_symbol']}"
        )
        if company.get("error"):
            print(f"   Error: {company['error']}")
            print()
            continue

        indicators = company["latest_indicators"]
        context = company["signal_context"]
        latest_signal = company.get("latest_signal", {})
        print(f"   Latest date: {company['latest_date']}")
        print(f"   Close: {indicators['close']}")
        print(
            f"   SMA20/SMA50: {indicators['sma_20']} / {indicators['sma_50']}"
        )
        print(f"   RSI14: {indicators['rsi_14']} ({context['rsi_state']})")
        print(
            f"   MACD vs signal: {indicators['macd']} / {indicators['macd_signal']} "
            f"({context['macd_vs_signal']})"
        )
        print(
            f"   Price vs trend: SMA20={context['price_vs_sma20']}, "
            f"SMA50={context['price_vs_sma50']}, "
            f"SMA20 vs SMA50={context['sma20_vs_sma50']}"
        )
        print(
            f"   Bollinger: {context['bollinger_position']}, "
            f"ADX strength: {context['trend_strength']}"
        )
        print(f"   Market regime: {context['market_regime']}")
        print_indicator_values(indicators)
        if latest_signal:
            print(
                f"   Signal: {latest_signal['signal']} "
                f"(score={latest_signal['score']}, regime={latest_signal.get('regime', 'unknown')})"
            )
        print()


def print_fundamentals_result(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]
    fundamentals = result["fundamentals"]["companies"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print()
    print(selection["summary"])
    print()

    if not fundamentals:
        print("선정된 종목이 없어 재무지표를 생성하지 못했습니다.")
        return

    for index, company in enumerate(fundamentals, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']} -> {company['report_name'] or 'N/A'}"
        )
        if company.get("error"):
            print(f"   Error: {company['error']}")
            print()
            continue

        print(f"   재무연도: {company['business_year']}")
        print(f"   기준일자: {company['statement_date'] or 'N/A'}")
        print(f"   최신 종가: {company['latest_close']}")
        print(f"   출처: {company['source']}")
        print_fundamental_values(company["valuation_metrics"])
        print()


def print_opinion_result(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]
    opinions = result["opinions"]["companies"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Method: {result['opinions']['method']}")
    print()
    print(selection["summary"])
    print()

    if not opinions:
        print("선정된 종목이 없어 의견을 생성하지 못했습니다.")
        return

    for index, company in enumerate(opinions, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']} -> {company['opinion']}"
        )
        if company.get("error"):
            print(f"   Error: {company['error']}")
            print()
            continue

        print(
            f"   점수: {company['score']} | 신뢰도: {company['confidence']} "
            f"| 위험도: {company['risk_level']}"
        )
        print(f"   근거: {company['rationale']}")
        print_indicator_values(
            result["technical_analysis"]["companies"][index - 1]["latest_indicators"]
        )
        print()


def print_plot_result(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]
    plots = result["plots"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Output directory: {plots['output_dir']}")
    print(f"Chart history: period={plots.get('period', 'N/A')}, interval={plots.get('interval', 'N/A')}")
    print(f"Recent points per chart: {plots['recent_points']}")
    print(f"Clear output dir: {plots['clear_output_dir']}")
    print()
    print(selection["summary"])
    print()

    companies = plots["companies"]
    if not companies:
        print("No price plots were generated because no companies were selected.")
        return

    for index, company in enumerate(companies, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']}"
        )
        if company.get("error"):
            print(f"   Error: {company['error']}")
            print()
            continue

        print(
            f"   Daily range: {company.get('daily_start_date') or company.get('start_date') or 'N/A'} -> "
            f"{company.get('daily_end_date') or company.get('end_date') or 'N/A'}"
        )
        print(
            f"   Intraday range: {company.get('intraday_start_date') or 'N/A'} -> "
            f"{company.get('intraday_end_date') or 'N/A'}"
        )
        print(f"   Daily plot: {company.get('daily_plot_path') or company.get('plot_path')}")
        print(f"   Intraday plot: {company.get('intraday_plot_path') or 'N/A'}")
        print()


def print_report_result(result: dict) -> None:
    article = result["article"]
    selection = result["selection"]
    fundamentals = result["fundamentals"]["companies"]
    opinions = result["opinions"]["companies"]
    plots = result["plots"]["companies"]

    print(f"Title: {article['title'] or 'N/A'}")
    print(f"Published at: {article['published_at'] or 'N/A'}")
    print(f"Source: {article['source'] or 'N/A'}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Opinion method: {result['opinions']['method']}")
    print(f"Plot output directory: {result['plots']['output_dir']}")
    print(
        "Chart history: "
        f"daily={result['plots'].get('daily_period', 'N/A')}/{result['plots'].get('daily_interval', 'N/A')}, "
        f"intraday={result['plots'].get('intraday_period', result['plots'].get('period', 'N/A'))}/"
        f"{result['plots'].get('intraday_interval', result['plots'].get('interval', 'N/A'))}"
    )
    print(f"Clear output dir: {result['plots']['clear_output_dir']}")
    print()
    print(selection["summary"])
    print()

    print("재무지표:")
    if not fundamentals:
        print("선정된 종목이 없어 재무지표를 생성하지 못했습니다.")
    else:
        for index, company in enumerate(fundamentals, start=1):
            print(
                f"{index}. {company['company_name_ko']} ({company['company_name']}) "
                f"[{company['market']}] {company['ticker']} -> {company['report_name'] or 'N/A'}"
            )
            if company.get("error"):
                print(f"   Error: {company['error']}")
                print()
                continue

            print(f"   재무연도: {company['business_year']}")
            print(f"   기준일자: {company['statement_date'] or 'N/A'}")
            print(f"   최신 종가: {company['latest_close']}")
            print_fundamental_values(company["valuation_metrics"])
            print()

    print("의견:")
    if not opinions:
        print("선정된 종목이 없어 의견을 생성하지 못했습니다.")
    else:
        for index, company in enumerate(opinions, start=1):
            print(
                f"{index}. {company['company_name_ko']} ({company['company_name']}) "
                f"[{company['market']}] {company['ticker']} -> {company['opinion']}"
            )
            if company.get("error"):
                print(f"   Error: {company['error']}")
                print()
                continue

            print(
                f"   점수: {company['score']} | 신뢰도: {company['confidence']} "
                f"| 위험도: {company['risk_level']}"
            )
            print(f"   근거: {company['rationale']}")
            print_indicator_values(
                result["technical_analysis"]["companies"][index - 1]["latest_indicators"]
            )
            print()

    print("Plots:")
    if not plots:
        print("No price plots were generated because no companies were selected.")
        return

    for index, company in enumerate(plots, start=1):
        print(
            f"{index}. {company['company_name_ko']} ({company['company_name']}) "
            f"[{company['market']}] {company['ticker']}"
        )
        if company.get("error"):
            print(f"   Error: {company['error']}")
            print()
            continue

        print(
            f"   Range: {company['start_date'] or 'N/A'} -> "
            f"{company['end_date'] or 'N/A'}"
        )
        print(f"   Latest close: {company['latest_close']}")
        print(f"   Plot: {company['plot_path']}")
        print()


def print_research_report_result(result: dict) -> None:
    print(result["llm_report"]["body"])


def print_word_report_result(result: dict) -> None:
    print(f"Word report: {result['word_report']['document_path']}")
    if result["word_report"].get("template_path"):
        print(f"Template: {result['word_report']['template_path']}")
    print(f"Generated at: {result['word_report']['generated_at']}")
    print(f"Plot directory: {result['plots']['output_dir']}")
    print(
        "Chart history: "
        f"daily={result['plots'].get('daily_period', 'N/A')}/{result['plots'].get('daily_interval', 'N/A')}, "
        f"intraday={result['plots'].get('intraday_period', result['plots'].get('period', 'N/A'))}/"
        f"{result['plots'].get('intraday_interval', result['plots'].get('interval', 'N/A'))}"
    )


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)

        if args.command is None:
            build_parser().print_help()
            return 1

        if args.command == "select":
            result = select_companies_from_url(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_selection(result)
            return 0

        if args.command == "ohlcv":
            result = fetch_selection_market_data(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_ohlcv_result(result)
            return 0

        if args.command == "indicators":
            result = fetch_selection_technical_analysis(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
                recent_rows=args.recent_rows,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_indicator_result(result)
            return 0

        if args.command == "fundamentals":
            result = fetch_selection_fundamentals(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_fundamentals_result(result)
            return 0

        if args.command == "opinion":
            result = fetch_selection_opinions(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
                recent_rows=args.recent_rows,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_opinion_result(result)
            return 0

        if args.command == "plot":
            result = fetch_selection_price_plots(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
                output_dir=args.output_dir,
                recent_points=args.recent_points,
                clear_output_dir=args.clear_output_dir,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_plot_result(result)
            return 0

        if args.command == "report":
            result = fetch_selection_report(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
                recent_rows=args.recent_rows,
                output_dir=args.output_dir,
                recent_points=args.recent_points,
                daily_plot_period=args.daily_plot_period,
                daily_plot_interval=args.daily_plot_interval,
                daily_recent_points=args.daily_recent_points,
                plot_period=args.plot_period,
                plot_interval=args.plot_interval,
                clear_output_dir=args.clear_output_dir,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_report_result(result)
            return 0

        if args.command == "research":
            result = fetch_selection_research_report(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
                recent_rows=args.recent_rows,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_research_report_result(result)
            return 0

        if args.command == "word-report":
            result = fetch_selection_word_report(
                url=args.url,
                provider=args.provider,
                model=args.model,
                max_companies=args.max_companies,
                article_char_limit=args.article_char_limit,
                period=args.period,
                interval=args.interval,
                recent_rows=args.recent_rows,
                output_dir=args.output_dir,
                recent_points=args.recent_points,
                daily_plot_period=args.daily_plot_period,
                daily_plot_interval=args.daily_plot_interval,
                daily_recent_points=args.daily_recent_points,
                plot_period=args.plot_period,
                plot_interval=args.plot_interval,
                clear_output_dir=args.clear_output_dir,
                template_path=args.template_path,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            print_word_report_result(result)
            return 0

        article = scrape_article(args.url)
        if args.json:
            print(json.dumps(article, ensure_ascii=False, indent=2))
            return 0

        print_article(article)
        return 0
    except (LLMConfigurationError, requests.RequestException, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
