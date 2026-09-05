from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any, Optional

from cam_pipeline.company_selector import (
    DEFAULT_OPENAI_MODEL,
    LLMConfigurationError,
    get_openai_client_class,
    normalize_env_api_key,
)


DEFAULT_CHART_ANALYSIS_MODEL = os.getenv("OPENAI_CHART_ANALYSIS_MODEL", DEFAULT_OPENAI_MODEL)
CHART_ANALYSIS_PROMPT = """You are a professional technical analyst.

Analyze the provided stock chart image using only visible chart information.

Focus on:
- trend structure
- momentum
- support/resistance
- price-volume relationship
- breakout/breakdown signals
- reversal probability

Do not hallucinate unseen indicators or fundamentals.

Return:
1. Trend assessment
2. Key support/resistance
3. Bullish scenario
4. Bearish scenario
5. Suggested trading bias (long/short/neutral)
6. Risk factors

Use professional equity research tone.
Avoid certainty.
Write the entire response in Korean."""


class ChartAnalysisError(RuntimeError):
    """Raised when chart-image analysis cannot be completed."""


def add_chart_analysis_to_plots(
    plots: list[dict[str, Any]],
    model: Optional[str] = None,
) -> list[dict[str, Any]]:
    return [add_chart_analysis_to_plot(plot, model=model) for plot in plots]


def add_chart_analysis_to_plot(
    plot: dict[str, Any],
    model: Optional[str] = None,
) -> dict[str, Any]:
    enriched = dict(plot)
    daily_path = str(plot.get("daily_plot_path") or plot.get("plot_path") or "").strip()
    intraday_path = str(plot.get("intraday_plot_path") or "").strip()

    enriched["daily_chart_comment"] = analyze_chart_path_safely(
        daily_path,
        model=model,
    )
    enriched["intraday_chart_comment"] = analyze_chart_path_safely(
        intraday_path,
        model=model,
    )
    return enriched


def analyze_chart_path_safely(path: str, model: Optional[str] = None) -> Optional[str]:
    if not path:
        return None
    try:
        return analyze_chart_image(Path(path), model=model)
    except (ChartAnalysisError, LLMConfigurationError, RuntimeError, OSError) as exc:
        return f"Chart analysis unavailable: {exc}"


def analyze_chart_image(image_path: Path, model: Optional[str] = None) -> str:
    if not image_path.exists():
        raise ChartAnalysisError(f"chart image not found: {image_path}")

    openai_client_class = get_openai_client_class()
    api_key = normalize_env_api_key(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not set.")

    client = openai_client_class(api_key=api_key)
    response = client.responses.create(
        model=model or DEFAULT_CHART_ANALYSIS_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": CHART_ANALYSIS_PROMPT},
                    {"type": "input_image", "image_url": encode_image_as_data_url(image_path)},
                ],
            }
        ],
        store=False,
    )

    body = str(getattr(response, "output_text", "") or "").strip()
    if not body:
        raise ChartAnalysisError("OpenAI returned an empty chart analysis.")
    return body


def encode_image_as_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
