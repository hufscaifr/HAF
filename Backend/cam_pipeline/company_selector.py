from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from cam_pipeline.article_scraper import scrape_article

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def load_project_dotenv() -> None:
    if load_dotenv is None:
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path)


load_project_dotenv()

DEFAULT_PROVIDER = os.getenv("CAM_LLM_PROVIDER", "openai").lower()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_ARTICLE_CHAR_LIMIT = 12000


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM provider is not configured correctly."""


def select_companies_from_url(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    require_exact_count: bool = False,
) -> dict[str, Any]:
    article = scrape_article(url)
    return select_companies_from_article(
        article=article,
        provider=provider,
        model=model,
        max_companies=max_companies,
        article_char_limit=article_char_limit,
        require_exact_count=require_exact_count,
    )


def select_companies_from_article(
    article: dict[str, Any],
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    require_exact_count: bool = False,
) -> dict[str, Any]:
    provider = provider.lower()
    schema = build_selection_schema(
        max_companies=max_companies,
        require_exact_count=require_exact_count,
    )
    prompt = build_company_selection_prompt(
        article=article,
        max_companies=max_companies,
        article_char_limit=article_char_limit,
        require_exact_count=require_exact_count,
    )

    if provider == "openai":
        chosen_model = model or DEFAULT_OPENAI_MODEL
        selection = run_openai_selection(prompt=prompt, schema=schema, model=chosen_model)
    elif provider == "gemini":
        chosen_model = model or DEFAULT_GEMINI_MODEL
        selection = run_gemini_selection(prompt=prompt, schema=schema, model=chosen_model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return {
        "article": article,
        "provider": provider,
        "model": chosen_model,
        "selection": normalize_selection_payload(selection),
    }


def run_openai_selection(prompt: str, schema: dict[str, Any], model: str) -> dict[str, Any]:
    openai_client_class = get_openai_client_class()
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not set.")

    client = openai_client_class(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=prompt,
        store=False,
        text={
            "format": {
                "type": "json_schema",
                "name": "company_selection",
                "strict": True,
                "schema": schema,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError("OpenAI returned an empty response.")

    return json.loads(response.output_text)


def run_gemini_selection(prompt: str, schema: dict[str, Any], model: str) -> dict[str, Any]:
    genai_module, genai_types_module = get_gemini_modules()
    api_key = normalize_env_api_key(os.getenv("GEMINI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("GEMINI_API_KEY is not set.")

    client = genai_module.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai_types_module.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return json.loads(response.text)


def build_company_selection_prompt(
    article: dict[str, Any],
    max_companies: int,
    article_char_limit: int,
    require_exact_count: bool = False,
) -> str:
    article_text = truncate_article_text(article.get("text", ""), article_char_limit)
    count_instruction = (
        f"Identify exactly {max_companies} companies that are listed on KOSPI or KOSDAQ and are promising investment candidates because of this news."
        if require_exact_count
        else f"Identify up to {max_companies} companies that are listed on KOSPI or KOSDAQ and are promising investment candidates because of this news."
    )
    inclusion_instruction = (
        "Include the three most relevant listed companies even when the connection is indirect; rank them by confidence and explain weaker connections honestly."
        if require_exact_count
        else "Only include companies when there is a clear, explainable connection between the article and the company."
    )
    listing_instruction = (
        "Every selected company must be listed on KOSPI or KOSDAQ. If direct beneficiaries are fewer than three, fill the remaining slots with the most relevant indirect beneficiaries or closely exposed listed companies."
        if require_exact_count
        else "If you are not reasonably confident that a company is listed on KOSPI or KOSDAQ, do not include it."
    )
    empty_instruction = (
        f"`companies` must contain exactly {max_companies} items."
        if require_exact_count
        else "`companies` may be empty."
    )
    return f"""
You are a Korean equity analyst.

Your task:
1. Read the news article below.
2. {count_instruction}
3. {inclusion_instruction}
4. {listing_instruction}
5. Prefer companies that could benefit directly or indirectly from the news catalyst.
6. Return only valid JSON that matches the schema.

Output rules:
- `summary` should be 2 to 4 sentences in Korean.
- {empty_instruction}
- `company_name` should be the English name if known.
- `company_name_ko` should be the Korean name if known.
- `ticker` should be the Korean stock code when you know it.
- `market` must be either `KOSPI` or `KOSDAQ`.
- `confidence` must be a number between 0 and 1.
- `rationale` must be written in Korean.
- `article_relevance` must be written in Korean.
- `key_catalysts` and `risks` should each have 1 to 4 concise items written in Korean.
- `risk_analysis` must be a deeper Korean risk paragraph of 4 to 7 sentences.
- In `risk_analysis`, analyze why the news thesis could fail or be delayed. Cover at least three of these where relevant: execution risk, demand uncertainty, valuation burden, earnings translation risk, competitive pressure, policy/regulatory risk, supply-chain risk, margin risk, timing risk, or the risk that the company is only an indirect beneficiary.
- Write `risk_analysis` in a professional sell-side equity research style for finance professionals. Avoid generic warnings and do not simply repeat the short `risks` list.
- All explanatory text fields must be written in Korean.
- Use a warm Korean explanatory tone ending mostly with "~해요", "~이에요", "~일 수 있어요", or "~로 보여요".
- Avoid stiff report endings such as "~합니다", "~입니다", "~된다", and "~판단된다" unless they are unavoidable for a quoted term.
- Keep the content analytical and finance-professional friendly even with the softer tone.
- Do not invent facts that are not supported by the article or well-established market knowledge.

Article metadata:
- Title: {article.get("title") or "N/A"}
- Published at: {article.get("published_at") or "N/A"}
- Source: {article.get("source") or "N/A"}
- URL: {article.get("url") or "N/A"}

Article text:
{article_text}
""".strip()


def build_selection_schema(
    max_companies: int,
    require_exact_count: bool = False,
) -> dict[str, Any]:
    companies_schema: dict[str, Any] = {
        "type": "array",
        "maxItems": max_companies,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "company_name": {"type": "string"},
                "company_name_ko": {"type": "string"},
                "ticker": {"type": "string"},
                "market": {
                    "type": "string",
                    "enum": ["KOSPI", "KOSDAQ"],
                },
                "rationale": {"type": "string"},
                "article_relevance": {"type": "string"},
                "key_catalysts": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "risks": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "risk_analysis": {"type": "string"},
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": [
                "company_name",
                "company_name_ko",
                "ticker",
                "market",
                "rationale",
                "article_relevance",
                "key_catalysts",
                "risks",
                "risk_analysis",
                "confidence",
            ],
        },
    }
    if require_exact_count:
        companies_schema["minItems"] = max_companies

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "companies": companies_schema,
        },
        "required": ["summary", "companies"],
    }


def normalize_selection_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary = str(payload.get("summary", "")).strip()
    companies = payload.get("companies", [])
    if not isinstance(companies, list):
        companies = []

    normalized_companies: list[dict[str, Any]] = []
    for company in companies:
        normalized_companies.append(
            {
                "company_name": str(company.get("company_name", "")).strip(),
                "company_name_ko": str(company.get("company_name_ko", "")).strip(),
                "ticker": str(company.get("ticker", "")).strip(),
                "market": str(company.get("market", "")).strip(),
                "rationale": str(company.get("rationale", "")).strip(),
                "article_relevance": str(company.get("article_relevance", "")).strip(),
                "key_catalysts": normalize_string_list(company.get("key_catalysts", [])),
                "risks": normalize_string_list(company.get("risks", [])),
                "risk_analysis": str(company.get("risk_analysis", "")).strip(),
                "confidence": round(float(company.get("confidence", 0)), 3),
            }
        )

    return {
        "summary": summary,
        "companies": normalized_companies,
    }


def normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def truncate_article_text(text: str, article_char_limit: int) -> str:
    if len(text) <= article_char_limit:
        return text
    return text[:article_char_limit].rstrip() + "\n\n[Article truncated for LLM input]"


def normalize_env_api_key(value: Optional[str]) -> str:
    if value is None:
        return ""

    normalized = value.strip()
    if (
        len(normalized) >= 2
        and normalized[0] == normalized[-1]
        and normalized[0] in {"'", '"'}
    ):
        normalized = normalized[1:-1].strip()

    return normalized


def get_openai_client_class() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise LLMConfigurationError(
            "The 'openai' package is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    return OpenAI


def get_gemini_modules() -> tuple[Any, Any]:
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError as exc:  # pragma: no cover
        raise LLMConfigurationError(
            "The 'google-genai' package is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    return genai, genai_types
