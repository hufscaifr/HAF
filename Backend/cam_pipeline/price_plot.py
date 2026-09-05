from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
)
from cam_pipeline.market_data import (
    fetch_selection_market_data,
)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    mdates = None
    plt = None


DEFAULT_OUTPUT_DIR = "plots"
DEFAULT_DAILY_PLOT_PERIOD = "3mo"
DEFAULT_DAILY_PLOT_INTERVAL = "1d"
DEFAULT_PLOT_PERIOD = "1d"
DEFAULT_PLOT_INTERVAL = "1m"
DEFAULT_RECENT_POINTS = 80
DEFAULT_DAILY_RECENT_POINTS = 90
CHART_BACKGROUND = "#070b13"
CHART_PANEL = "#101827"
CHART_GRID = "#24344f"
CHART_BORDER = "#0b4f8d"
CHART_TEXT = "#f4f7fb"
CHART_MUTED_TEXT = "#98a8bf"
CHART_LINE = "#0b63d8"
CHART_LINE_GLOW = "#1c78ff"
CHART_FILL = "#0b63d8"
CHART_POSITIVE = "#28f28f"
CHART_NEGATIVE = "#ff6370"
CHART_REFERENCE = "#6f819b"


class PricePlotError(RuntimeError):
    """Raised when price charts cannot be generated."""


@dataclass
class CompanyPricePlot:
    company_name: str
    company_name_ko: str
    ticker: str
    market: str
    yahoo_symbol: str
    plot_path: Optional[str]
    recent_points: int
    latest_close: Optional[float]
    start_date: Optional[str]
    end_date: Optional[str]
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_name_ko": self.company_name_ko,
            "ticker": self.ticker,
            "market": self.market,
            "yahoo_symbol": self.yahoo_symbol,
            "plot_path": self.plot_path,
            "recent_points": self.recent_points,
            "latest_close": self.latest_close,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "error": self.error,
        }


def fetch_selection_price_plots(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    period: str = DEFAULT_PLOT_PERIOD,
    interval: str = DEFAULT_PLOT_INTERVAL,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    recent_points: int = DEFAULT_RECENT_POINTS,
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

    plots = generate_price_plots(
        companies=market_result["market_data"]["companies"],
        output_dir=output_dir,
        recent_points=recent_points,
        clear_output_dir=clear_output_dir,
    )

    return {
        "article": market_result["article"],
        "provider": market_result["provider"],
        "model": market_result["model"],
        "selection": market_result["selection"],
        "market_data": market_result["market_data"],
        "plots": {
            "output_dir": str(Path(output_dir).resolve()),
            "period": period,
            "interval": interval,
            "recent_points": recent_points,
            "clear_output_dir": clear_output_dir,
            "companies": plots,
        },
    }


def generate_price_plots(
    companies: list[dict[str, Any]],
    output_dir: str = DEFAULT_OUTPUT_DIR,
    recent_points: int = DEFAULT_RECENT_POINTS,
    clear_output_dir: bool = False,
    chart_kind: str = "intraday",
    filename_suffix: str = "intraday",
) -> list[dict[str, Any]]:
    ensure_matplotlib_available()

    if recent_points <= 0:
        raise PricePlotError("recent_points must be greater than 0.")

    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    if clear_output_dir:
        clear_existing_plot_files(output_path)

    results: list[dict[str, Any]] = []
    for company in companies:
        try:
            plot_result = generate_company_price_plot(
                company=company,
                output_dir=output_path,
                recent_points=recent_points,
                chart_kind=chart_kind,
                filename_suffix=filename_suffix,
            )
            results.append(plot_result.to_dict())
        except PricePlotError as exc:
            results.append(
                CompanyPricePlot(
                    company_name=str(company.get("company_name", "")).strip(),
                    company_name_ko=str(company.get("company_name_ko", "")).strip(),
                    ticker=str(company.get("ticker", "")).strip(),
                    market=str(company.get("market", "")).strip(),
                    yahoo_symbol=str(company.get("yahoo_symbol", "")).strip(),
                    plot_path=None,
                    recent_points=recent_points,
                    latest_close=company.get("latest_close"),
                    start_date=company.get("start_date"),
                    end_date=company.get("end_date"),
                    error=str(exc),
                ).to_dict()
            )

    return results


def generate_company_price_plot(
    company: dict[str, Any],
    output_dir: Path,
    recent_points: int,
    chart_kind: str = "intraday",
    filename_suffix: str = "intraday",
) -> CompanyPricePlot:
    if company.get("error"):
        raise PricePlotError(str(company["error"]))

    ohlcv = company.get("ohlcv", [])
    if not isinstance(ohlcv, list) or not ohlcv:
        raise PricePlotError("No OHLCV data is available to plot.")

    frame = pd.DataFrame(ohlcv).copy()
    required_columns = {"date", "open", "close", "volume"}
    if not required_columns.issubset(frame.columns):
        raise PricePlotError("OHLCV data is missing required columns for plotting.")

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["open"] = pd.to_numeric(frame["open"], errors="coerce")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if "high" in frame.columns:
        frame["high"] = pd.to_numeric(frame["high"], errors="coerce")
    if "low" in frame.columns:
        frame["low"] = pd.to_numeric(frame["low"], errors="coerce")
    frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce").fillna(0)
    frame = frame.dropna(subset=["date", "open", "close"]).sort_values("date").reset_index(drop=True)
    if frame.empty:
        raise PricePlotError("Price series is empty after normalization.")

    frame = frame.tail(recent_points).reset_index(drop=True)
    if frame.empty:
        raise PricePlotError("No recent price points are available to plot.")

    file_name = build_plot_filename(company, filename_suffix=filename_suffix)
    plot_path = output_dir / file_name
    render_price_plot(frame, company, plot_path, chart_kind=chart_kind)

    start_date = format_plot_datetime(frame.iloc[0]["date"])
    end_date = format_plot_datetime(frame.iloc[-1]["date"])
    latest_close = round(float(frame.iloc[-1]["close"]), 4)

    return CompanyPricePlot(
        company_name=str(company.get("company_name", "")).strip(),
        company_name_ko=str(company.get("company_name_ko", "")).strip(),
        ticker=str(company.get("ticker", "")).strip(),
        market=str(company.get("market", "")).strip(),
        yahoo_symbol=str(company.get("yahoo_symbol", "")).strip(),
        plot_path=str(plot_path),
        recent_points=len(frame),
        latest_close=latest_close,
        start_date=start_date,
        end_date=end_date,
    )


def render_price_plot(
    frame: pd.DataFrame,
    company: dict[str, Any],
    plot_path: Path,
    chart_kind: str = "intraday",
) -> None:
    if chart_kind == "daily":
        render_daily_price_plot(frame, company, plot_path)
        return
    render_intraday_price_plot(frame, company, plot_path)


def render_daily_price_plot(frame: pd.DataFrame, company: dict[str, Any], plot_path: Path) -> None:
    display_name = (
        str(company.get("company_name", "")).strip()
        or str(company.get("company_name_ko", "")).strip()
        or "Company"
    )
    ticker = str(company.get("ticker", "")).strip()
    symbol = str(company.get("yahoo_symbol", "")).strip() or ticker

    figure, axis = plt.subplots(figsize=(12.8, 5.8), facecolor=CHART_BACKGROUND)
    axis.set_facecolor(CHART_PANEL)
    axis.grid(True, color=CHART_GRID, linewidth=0.8, alpha=0.55)
    axis.spines["left"].set_visible(False)
    axis.spines["top"].set_visible(False)
    axis.spines["bottom"].set_color(CHART_BORDER)
    axis.spines["right"].set_color(CHART_BORDER)
    axis.tick_params(axis="both", colors=CHART_MUTED_TEXT, labelsize=10)
    axis.yaxis.tick_right()
    axis.yaxis.set_label_position("right")

    x_values = frame["date"]
    closes = frame["close"].astype(float)
    axis.plot(x_values, closes, color=CHART_LINE_GLOW, linewidth=4.2, alpha=0.12, zorder=2)
    axis.plot(x_values, closes, color=CHART_LINE, linewidth=2.4, zorder=3)
    axis.fill_between(x_values, closes, closes.min(), color=CHART_FILL, alpha=0.22, zorder=1)

    latest = frame.iloc[-1]
    latest_close = float(latest["close"])
    axis.axhline(latest_close, color=CHART_REFERENCE, linestyle=(0, (3, 3)), linewidth=0.9, alpha=0.75)
    axis.annotate(
        f"{latest_close:,.2f}",
        xy=(x_values.iloc[-1], latest_close),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        ha="left",
        fontsize=11,
        fontweight="bold",
        color=CHART_BACKGROUND,
        bbox={"boxstyle": "round,pad=0.35", "fc": CHART_POSITIVE, "ec": "none"},
        clip_on=False,
    )
    axis.set_title(
        f"{display_name} ({symbol}) 3M Daily Trend",
        loc="left",
        fontsize=15,
        fontweight="bold",
        color=CHART_TEXT,
        pad=12,
    )
    axis.set_ylabel("Close", color=CHART_MUTED_TEXT)
    axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:,.2f}"))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    figure.autofmt_xdate(rotation=0)
    figure.tight_layout(pad=1.2)
    figure.savefig(plot_path, dpi=160)
    plt.close(figure)


def render_intraday_price_plot(frame: pd.DataFrame, company: dict[str, Any], plot_path: Path) -> None:
    display_name = (
        str(company.get("company_name", "")).strip()
        or str(company.get("company_name_ko", "")).strip()
        or "Company"
    )
    ticker = str(company.get("ticker", "")).strip()
    symbol = str(company.get("yahoo_symbol", "")).strip() or ticker

    figure = plt.figure(figsize=(12.8, 7.2), facecolor=CHART_BACKGROUND)
    grid = figure.add_gridspec(nrows=5, ncols=1, hspace=0.0)
    price_axis = figure.add_subplot(grid[:4, 0])
    volume_axis = figure.add_subplot(grid[4, 0], sharex=price_axis)

    for axis in (price_axis, volume_axis):
        axis.set_facecolor(CHART_PANEL)
        axis.grid(True, color=CHART_GRID, linewidth=0.8, alpha=0.55)
        axis.spines["left"].set_visible(False)
        axis.spines["top"].set_visible(False)
        axis.spines["bottom"].set_color(CHART_BORDER)
        axis.spines["right"].set_color(CHART_BORDER)
        axis.tick_params(axis="both", colors=CHART_MUTED_TEXT, labelsize=10)
        axis.yaxis.tick_right()
        axis.yaxis.set_label_position("right")

    x_values = frame["date"]
    closes = frame["close"].astype(float)
    opens = frame["open"].astype(float)
    volumes = frame["volume"].astype(float)

    price_axis.plot(x_values, closes, color=CHART_LINE_GLOW, linewidth=4.0, alpha=0.12, zorder=2)
    price_axis.plot(x_values, closes, color=CHART_LINE, linewidth=2.1, zorder=3)
    price_axis.fill_between(x_values, closes, closes.min(), color=CHART_FILL, alpha=0.24, zorder=1)

    up_color = CHART_POSITIVE
    down_color = CHART_NEGATIVE
    bar_colors = [up_color if close >= open_ else down_color for open_, close in zip(opens, closes)]
    bar_width = estimate_bar_width(x_values)
    volume_axis.bar(x_values, volumes, width=bar_width, color=bar_colors, align="center", alpha=0.72)
    volume_axis.set_ylim(0, max(float(volumes.max()) * 1.35, 1.0))

    latest = frame.iloc[-1]
    first = frame.iloc[0]
    high = float(frame["high"].max()) if "high" in frame.columns and frame["high"].notna().any() else float(closes.max())
    low = float(frame["low"].min()) if "low" in frame.columns and frame["low"].notna().any() else float(closes.min())
    latest_close = float(latest["close"])
    latest_volume = int(float(latest["volume"]))
    price_axis.axhline(latest_close, color=CHART_REFERENCE, linestyle=(0, (3, 3)), linewidth=0.9, alpha=0.8)
    price_axis.annotate(
        f"{latest_close:,.2f}",
        xy=(x_values.iloc[-1], latest_close),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        ha="left",
        fontsize=11,
        fontweight="bold",
        color=CHART_BACKGROUND,
        bbox={"boxstyle": "round,pad=0.35", "fc": CHART_POSITIVE, "ec": "none"},
        clip_on=False,
    )

    ohlcv_label = (
        f"O:{float(first['open']):,.2f}  H:{high:,.2f}  "
        f"L:{low:,.2f}  C:{latest_close:,.2f}  V:{format_compact_number(latest_volume)}"
    )
    price_axis.text(
        0.02,
        0.93,
        ohlcv_label,
        transform=price_axis.transAxes,
        fontsize=12,
        color=CHART_TEXT,
        bbox={"boxstyle": "round,pad=0.3", "fc": "#151f32", "ec": "#243b63", "alpha": 0.88},
    )
    price_axis.text(
        0.985,
        0.965,
        "yahoo finance",
        transform=price_axis.transAxes,
        ha="right",
        va="top",
        fontsize=16,
        color=CHART_MUTED_TEXT,
        fontweight="bold",
        alpha=0.22,
    )
    price_axis.set_title(
        f"{display_name} ({symbol}) 1M Price / Volume",
        loc="left",
        fontsize=15,
        fontweight="bold",
        color=CHART_TEXT,
        pad=12,
    )

    price_axis.set_ylabel("Price", color=CHART_MUTED_TEXT)
    volume_axis.set_ylabel("Volume", color=CHART_MUTED_TEXT)
    volume_axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: format_compact_number(value)))
    price_axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:,.2f}"))
    volume_axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.setp(price_axis.get_xticklabels(), visible=False)
    figure.autofmt_xdate(rotation=0)
    figure.tight_layout(pad=1.2)
    figure.savefig(plot_path, dpi=160)
    plt.close(figure)


def estimate_bar_width(dates: pd.Series) -> float:
    if len(dates) < 2:
        return 0.00055
    deltas = dates.sort_values().diff().dropna().dt.total_seconds()
    if deltas.empty:
        return 0.00055
    return max(float(deltas.median()) / 86400 * 0.72, 0.00035)


def format_compact_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if abs_number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    if abs_number >= 1_000:
        return f"{number / 1_000:.1f}k"
    return f"{number:,.0f}"


def format_plot_datetime(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.hour or timestamp.minute:
        return timestamp.strftime("%Y-%m-%d %H:%M")
    return timestamp.strftime("%Y-%m-%d")


def generate_report_price_plots(
    daily_companies: list[dict[str, Any]],
    intraday_companies: list[dict[str, Any]],
    output_dir: str = DEFAULT_OUTPUT_DIR,
    daily_recent_points: int = DEFAULT_DAILY_RECENT_POINTS,
    intraday_recent_points: int = DEFAULT_RECENT_POINTS,
    clear_output_dir: bool = False,
) -> list[dict[str, Any]]:
    daily_plots = generate_price_plots(
        companies=daily_companies,
        output_dir=output_dir,
        recent_points=daily_recent_points,
        clear_output_dir=clear_output_dir,
        chart_kind="daily",
        filename_suffix="daily_3mo",
    )
    intraday_plots = generate_price_plots(
        companies=intraday_companies,
        output_dir=output_dir,
        recent_points=intraday_recent_points,
        clear_output_dir=False,
        chart_kind="intraday",
        filename_suffix="intraday_1m",
    )
    return merge_report_price_plots(daily_plots, intraday_plots)


def merge_report_price_plots(
    daily_plots: list[dict[str, Any]],
    intraday_plots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    tickers = []
    for item in [*daily_plots, *intraday_plots]:
        ticker = str(item.get("ticker", "")).strip()
        if ticker and ticker not in tickers:
            tickers.append(ticker)

    daily_map = {str(item.get("ticker", "")).strip(): item for item in daily_plots}
    intraday_map = {str(item.get("ticker", "")).strip(): item for item in intraday_plots}
    for ticker in tickers:
        daily = daily_map.get(ticker, {})
        intraday = intraday_map.get(ticker, {})
        base = daily or intraday
        daily_error = daily.get("error")
        intraday_error = intraday.get("error")
        both_failed = bool(daily_error) and bool(intraday_error)
        merged.append(
            {
                **base,
                "plot_path": daily.get("plot_path") or intraday.get("plot_path"),
                "daily_plot_path": daily.get("plot_path"),
                "intraday_plot_path": intraday.get("plot_path"),
                "daily_recent_points": daily.get("recent_points", 0),
                "intraday_recent_points": intraday.get("recent_points", 0),
                "daily_latest_close": daily.get("latest_close"),
                "intraday_latest_close": intraday.get("latest_close"),
                "daily_start_date": daily.get("start_date"),
                "daily_end_date": daily.get("end_date"),
                "intraday_start_date": intraday.get("start_date"),
                "intraday_end_date": intraday.get("end_date"),
                "daily_error": daily_error,
                "intraday_error": intraday_error,
                "error": "; ".join(
                    str(error)
                    for error in (daily_error, intraday_error)
                    if error
                ) if both_failed else None,
            }
        )
    return merged


def build_plot_filename(company: dict[str, Any], filename_suffix: str = "intraday") -> str:
    ticker = str(company.get("ticker", "")).strip() or "unknown"
    safe_ticker = "".join(ch for ch in ticker if ch.isalnum()) or "unknown"
    suffix = "".join(
        ch if ch.isascii() and ch.isalnum() else "_"
        for ch in filename_suffix
    ).strip("_") or "chart"
    return f"{safe_ticker}_{suffix}.png"


def ensure_matplotlib_available() -> None:
    if plt is None:
        raise PricePlotError(
            "The 'matplotlib' package is not installed. Run `pip install -r requirements.txt`."
        )


def clear_existing_plot_files(output_dir: Path) -> None:
    for file_path in output_dir.glob("*.png"):
        if file_path.is_file():
            file_path.unlink()
