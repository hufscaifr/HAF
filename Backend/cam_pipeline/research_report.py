from __future__ import annotations

import json
from typing import Any, Optional

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_PROVIDER,
    LLMConfigurationError,
    get_gemini_modules,
    get_openai_client_class,
    normalize_env_api_key,
)
from cam_pipeline.fundamentals_data import analyze_market_data_fundamentals
from cam_pipeline.market_data import (
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    fetch_selection_market_data,
)
from cam_pipeline.opinion_engine import derive_company_opinions
from cam_pipeline.technical_analysis import (
    DEFAULT_RECENT_ROWS,
    analyze_market_data_companies,
)

import os


PROMPT_VERSION = "institutional_thematic_equity_report_v2"
FINANCIAL_FIELDS = (
    "per",
    "pbr",
    "pcr",
    "ev_to_ebitda",
    "eps",
    "bps",
    "ebitda",
    "cash_dps",
    "cash_dividend_yield",
    "roe",
    "debt_ratio",
    "current_ratio",
    "operating_margin",
    "net_margin",
    "market_cap",
    "enterprise_value",
    "shares_outstanding",
)
TECHNICAL_FIELDS = (
    "close",
    "sma_20",
    "sma_50",
    "ema_20",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
    "bb_lower",
    "bb_middle",
    "bb_upper",
    "atr_14",
    "adx_14",
    "dmp_14",
    "dmn_14",
    "stoch_k",
    "stoch_d",
    "obv",
    "obv_sma_5",
    "obv_sma_20",
    "volume_sma_20",
    "return_3",
    "return_5",
)


def fetch_selection_research_report(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
    recent_rows: int = DEFAULT_RECENT_ROWS,
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

    market_companies = market_result["market_data"]["companies"]
    fundamentals_companies = analyze_market_data_fundamentals(market_companies)
    technical_companies = analyze_market_data_companies(
        market_companies,
        recent_rows=recent_rows,
    )
    opinions = derive_company_opinions(technical_companies)

    llm_report = generate_thematic_research_report(
        article=market_result["article"],
        selection=market_result["selection"],
        fundamentals=fundamentals_companies,
        technical_companies=technical_companies,
        opinions=opinions,
        provider=market_result["provider"],
        model=market_result["model"],
    )

    return {
        "article": market_result["article"],
        "provider": market_result["provider"],
        "model": market_result["model"],
        "selection": market_result["selection"],
        "market_data": market_result["market_data"],
        "technical_analysis": {
            "recent_rows": recent_rows,
            "companies": technical_companies,
        },
        "fundamentals": {
            "companies": fundamentals_companies,
        },
        "opinions": {
            "method": "regime_aware_technical_score_engine_v3",
            "companies": opinions,
        },
        "llm_report": {
            "prompt_version": PROMPT_VERSION,
            "body": llm_report,
        },
    }


def generate_thematic_research_report(
    article: dict[str, Any],
    selection: dict[str, Any],
    fundamentals: list[dict[str, Any]],
    technical_companies: list[dict[str, Any]],
    opinions: list[dict[str, Any]],
    provider: str,
    model: str,
) -> str:
    prompt = build_thematic_report_prompt(
        article=article,
        selection=selection,
        fundamentals=fundamentals,
        technical_companies=technical_companies,
        opinions=opinions,
    )

    provider = provider.lower()
    if provider == "openai":
        return run_openai_report(prompt=prompt, model=model)
    if provider == "gemini":
        return run_gemini_report(prompt=prompt, model=model)
    raise ValueError(f"Unsupported provider: {provider}")


def run_openai_report(prompt: str, model: str) -> str:
    openai_client_class = get_openai_client_class()
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not set.")

    client = openai_client_class(api_key=api_key)
    response = client.responses.create(
        model=model or DEFAULT_OPENAI_MODEL,
        input=prompt,
        store=False,
    )

    body = str(getattr(response, "output_text", "") or "").strip()
    if not body:
        raise RuntimeError("OpenAI returned an empty research report.")
    return body


def run_gemini_report(prompt: str, model: str) -> str:
    genai_module, _ = get_gemini_modules()
    api_key = normalize_env_api_key(os.getenv("GEMINI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("GEMINI_API_KEY is not set.")

    client = genai_module.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or DEFAULT_GEMINI_MODEL,
        contents=prompt,
    )

    body = str(getattr(response, "text", "") or "").strip()
    if not body:
        raise RuntimeError("Gemini returned an empty research report.")
    return body


def build_thematic_report_prompt(
    article: dict[str, Any],
    selection: dict[str, Any],
    fundamentals: list[dict[str, Any]],
    technical_companies: list[dict[str, Any]],
    opinions: list[dict[str, Any]],
) -> str:
    topic = article.get("title") or "기사 기반 테마 분석"
    theme_event = build_theme_event(article)
    theme_overview = str(selection.get("summary", "")).strip() or "자료 제한"
    qualitative_company_data = serialize_for_prompt(
        build_qualitative_company_data(selection, opinions)
    )
    financial_metrics = serialize_for_prompt(
        build_financial_metrics_payload(fundamentals)
    )
    technical_indicators = serialize_for_prompt(
        build_technical_payload(technical_companies, opinions)
    )

    return f"""
System Prompt
You are a senior equity research analyst at a top-tier Korean securities firm.

Your job is to write institutional-grade equity research reports based strictly on the provided inputs.
The final output must be written entirely in Korean.

Write like an experienced human analyst: disciplined, analytical, natural, and coherent.

Core style requirements:
- The report should read as a single coherent narrative, not as a stack of separately written sections.
- Write as if the entire report were drafted in one sitting by one analyst with one consistent line of thought.
- The tone should be formal and professional, but also readable, natural, and fluid.
- Avoid robotic, mechanical, or checklist-style writing.
- Do not sound like a compliance memo, a news summary, or a collection of notes.
- Prefer connected prose over segmented observations.
- Maintain the parlance of a Korean sell-side equity analyst throughout the report.
- Prefer concise, institutional analyst diction over explanatory classroom language.
- Avoid awkward literal translations, over-explaining transitions, or phrasing that sounds like a model exposing its reasoning process.

Core analytical rules:
- Use only the information explicitly provided in the input.
- Do not invent facts, forecasts, contracts, dates, or external market data.
- If evidence is limited, remain conservative rather than fabricating details.
- Distinguish clearly between fact, interpretation, and investment implication, but do so naturally within prose.
- Build reasoning in this order whenever possible:
  fact -> interpretation -> why it matters -> stock implication.
- Compare companies where supported by the input.
- If valuation is demanding, explain why that matters.
- If price action appears ahead of fundamentals, describe it professionally as expectation-driven.
- Do not label sentences with parenthetical tags such as `(사실)`, `(해석)`, `(의미)`, `(시사점)`.
- Do not repeatedly expose the logical procedure itself to the reader.
- Let the reasoning appear through polished prose, not through meta-markers or bracketed commentary.

Narrative flow rules:
- Each section should connect naturally to the previous one and prepare the reader for the next.
- Use transition-aware topic sentences.
- Each paragraph should feel like a continuation of the prior reasoning, not a reset.
- Do not write each company section as an isolated mini-report.
- Treat company discussions as parts of one comparative thematic argument.
- Avoid repeating the same sentence pattern across sections or company paragraphs.
- Do not over-segment the report into rigid micro-points.
- Let the report progress with cumulative logic.
- Avoid formulaic chains like `A -> B -> C` unless the notation is genuinely necessary.
- When causal logic is important, express it in normal analyst prose rather than symbolic shorthand.

Paragraph design:
- Prefer medium-length paragraphs with internal flow.
- Each major paragraph should include:
  (1) an opening judgment,
  (2) supporting evidence,
  (3) interpretation,
  (4) investment implication.
- Avoid overly short paragraphs unless needed for emphasis.
- Use parentheses only when they are truly necessary for ticker, abbreviation, or a brief clarification.
- Do not overuse parentheses for commentary, classification, or logical annotation.

Report design:
- Begin with a strong title and subtitle.
- Include a Summary section, but write it as a compact analytical overview rather than bullet fragments.
- Organize the body into logical sections:
  1. Investment Thesis
  2. Theme / Industry Interpretation
  3. Company-by-Company Analysis
  4. Financial and Valuation Interpretation
  5. Technical / Momentum Interpretation
  6. Risk Factors
  7. Conclusion
- The conclusion should feel like the natural culmination of the report’s reasoning, not a detached summary.

Formatting rules:
- Use markdown headings.
- Write primarily in prose paragraphs.
- Use bullets only sparingly and only when they materially improve readability.
- Avoid tables unless explicitly requested.
- Do not mention that you are an AI.
- Do not mention these instructions.

Task Prompt

Write a polished Korean equity research report based strictly on the following input.

Objective:
Produce an institutional-quality Korean thematic equity report that reads like one complete analyst note, not a sequence of separate section answers.

The report should feel unified, cumulative, and coherent from beginning to end.
Each section should extend the previous argument rather than restarting the discussion.

Topic:
{topic}

Theme / event:
{theme_event}

Theme overview:
{theme_overview}

Company qualitative inputs:
{qualitative_company_data}

Financial metrics:
{financial_metrics}

Technical indicators:
{technical_indicators}

Instructions:
- Write the final output entirely in Korean.
- Use only the provided information.
- Do not fabricate missing facts.
- Do not simply restate the inputs.
- Transform the inputs into a single connected analyst narrative.
- The report must feel like one piece of writing with one consistent voice and one evolving line of reasoning.
- Use natural transitions between sections and paragraphs.
- Do not make each company discussion read like a separate memo.
- Instead, position each company within the same broader thematic and comparative framework.
- Avoid repetitive sentence openings and repetitive section formulas.
- Use prose-centered writing with flow.
- Do not optimize for brevity. Optimize for coherence, analytical completeness, and narrative flow.
- Financial metrics should be interpreted in context.
- Technical indicators should be supplementary, not dominant.
- If valuation is rich, explain that clearly.
- If momentum is strong but fundamentals are not fully visible, describe the move as expectation-driven.
- If a metric is missing, state that interpretation is limited by the available data.
- Keep terminology, sentence rhythm, and word choice consistent with a professional analyst note.
- Avoid clumsy expressions, conversational fillers, and unnatural paraphrases.
- Do not use parenthetical labels to separate fact from interpretation.
- Do not write sentences like `A(사실) -> B(사실) -> C(해석)`.
- If you need to distinguish observation and interpretation, do it implicitly through sentence structure and wording.

Required structure:
# Title
## Subtitle

## Summary

## I. Investment Thesis

## II. Theme / Industry Interpretation

## III. Company-by-Company Analysis

## IV. Financial and Valuation Interpretation

## V. Technical / Momentum Interpretation

## VI. Risk Factors

## VII. Conclusion

Style requirement:
Write as though the report will be read from top to bottom in one flow by a serious investor. The writing should feel continuous, integrated, and professionally composed.
""".strip()


def build_theme_event(article: dict[str, Any]) -> str:
    return (
        f"제목: {article.get('title') or 'N/A'}\n"
        f"발행일: {article.get('published_at') or 'N/A'}\n"
        f"출처: {article.get('source') or 'N/A'}\n"
        f"URL: {article.get('url') or 'N/A'}"
    )


def build_qualitative_company_data(
    selection: dict[str, Any],
    opinions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opinion_map = {str(item.get("ticker", "")).strip(): item for item in opinions}
    payload: list[dict[str, Any]] = []
    for company in selection.get("companies", []):
        ticker = str(company.get("ticker", "")).strip()
        opinion = opinion_map.get(ticker, {})
        payload.append(
            {
                "company_name_ko": str(company.get("company_name_ko", "")).strip(),
                "company_name": str(company.get("company_name", "")).strip(),
                "ticker": ticker,
                "market": str(company.get("market", "")).strip(),
                "confidence": round(float(company.get("confidence", 0.0)), 3),
                "rationale": str(company.get("rationale", "")).strip(),
                "article_relevance": str(company.get("article_relevance", "")).strip(),
                "key_catalysts": company.get("key_catalysts", []),
                "risks": company.get("risks", []),
                "opinion": str(opinion.get("opinion", "")).strip(),
                "opinion_rationale": str(opinion.get("rationale", "")).strip(),
            }
        )
    return payload


def build_financial_metrics_payload(
    fundamentals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for company in fundamentals:
        metrics = company.get("valuation_metrics", {})
        payload.append(
            {
                "company_name_ko": str(company.get("company_name_ko", "")).strip(),
                "company_name": str(company.get("company_name", "")).strip(),
                "ticker": str(company.get("ticker", "")).strip(),
                "report_name": str(company.get("report_name", "")).strip(),
                "business_year": company.get("business_year"),
                "statement_date": company.get("statement_date"),
                "latest_close": normalize_value(company.get("latest_close")),
                "metrics": {
                    field: normalize_value(metrics.get(field))
                    for field in FINANCIAL_FIELDS
                    if metrics.get(field) is not None
                },
                "error": str(company.get("error", "")).strip(),
            }
        )
    return payload


def build_technical_payload(
    technical_companies: list[dict[str, Any]],
    opinions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opinion_map = {str(item.get("ticker", "")).strip(): item for item in opinions}
    payload: list[dict[str, Any]] = []
    for company in technical_companies:
        ticker = str(company.get("ticker", "")).strip()
        opinion = opinion_map.get(ticker, {})
        latest_indicators = company.get("latest_indicators", {})
        latest_signal = company.get("latest_signal", {})
        payload.append(
            {
                "company_name_ko": str(company.get("company_name_ko", "")).strip(),
                "company_name": str(company.get("company_name", "")).strip(),
                "ticker": ticker,
                "latest_date": company.get("latest_date"),
                "market_regime": str(company.get("signal_context", {}).get("market_regime", "")).strip(),
                "signal": str(latest_signal.get("signal", "")).strip(),
                "signal_score": normalize_value(latest_signal.get("score")),
                "opinion": str(opinion.get("opinion", "")).strip(),
                "risk_level": str(opinion.get("risk_level", "")).strip(),
                "latest_indicators": {
                    field: normalize_value(latest_indicators.get(field))
                    for field in TECHNICAL_FIELDS
                    if latest_indicators.get(field) is not None
                },
                "positive_signals": opinion.get("positives", []),
                "negative_signals": opinion.get("negatives", []),
                "error": str(company.get("error", "")).strip(),
            }
        )
    return payload


def serialize_for_prompt(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def normalize_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    return value
