from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
)
from cam_pipeline.chart_analysis import add_chart_analysis_to_plots
from cam_pipeline.fundamentals_data import analyze_market_data_fundamentals
from cam_pipeline.market_data import (
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    fetch_market_data_for_companies,
    fetch_selection_market_data,
)
from cam_pipeline.opinion_engine import derive_company_opinions
from cam_pipeline.price_plot import (
    DEFAULT_DAILY_PLOT_INTERVAL,
    DEFAULT_DAILY_PLOT_PERIOD,
    DEFAULT_DAILY_RECENT_POINTS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PLOT_INTERVAL,
    DEFAULT_PLOT_PERIOD,
    DEFAULT_RECENT_POINTS,
    generate_report_price_plots,
)
from cam_pipeline.technical_analysis import (
    DEFAULT_INDICATORS,
    DEFAULT_RECENT_ROWS,
    analyze_market_data_companies,
)


def fetch_selection_report(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
    recent_rows: int = DEFAULT_RECENT_ROWS,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    recent_points: int = DEFAULT_RECENT_POINTS,
    daily_plot_period: str = DEFAULT_DAILY_PLOT_PERIOD,
    daily_plot_interval: str = DEFAULT_DAILY_PLOT_INTERVAL,
    daily_recent_points: int = DEFAULT_DAILY_RECENT_POINTS,
    plot_period: str = DEFAULT_PLOT_PERIOD,
    plot_interval: str = DEFAULT_PLOT_INTERVAL,
    clear_output_dir: bool = False,
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
    daily_plot_companies = fetch_market_data_for_companies(
        companies=market_result["selection"].get("companies", []),
        period=daily_plot_period,
        interval=daily_plot_interval,
    )
    intraday_plot_companies = fetch_market_data_for_companies(
        companies=market_result["selection"].get("companies", []),
        period=plot_period,
        interval=plot_interval,
    )
    plots = generate_report_price_plots(
        daily_companies=daily_plot_companies,
        intraday_companies=intraday_plot_companies,
        output_dir=output_dir,
        daily_recent_points=daily_recent_points,
        intraday_recent_points=recent_points,
        clear_output_dir=clear_output_dir,
    )
    chart_analysis_model = model if str(provider).lower() == "openai" else None
    plots = add_chart_analysis_to_plots(plots, model=chart_analysis_model)

    return {
        "article": market_result["article"],
        "provider": market_result["provider"],
        "model": market_result["model"],
        "selection": market_result["selection"],
        "market_data": market_result["market_data"],
        "technical_analysis": {
            "indicators": list(DEFAULT_INDICATORS),
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
        "plots": {
            "output_dir": str(Path(output_dir).resolve()),
            "daily_period": daily_plot_period,
            "daily_interval": daily_plot_interval,
            "intraday_period": plot_period,
            "intraday_interval": plot_interval,
            "recent_points": recent_points,
            "daily_recent_points": daily_recent_points,
            "clear_output_dir": clear_output_dir,
            "companies": plots,
        },
    }
