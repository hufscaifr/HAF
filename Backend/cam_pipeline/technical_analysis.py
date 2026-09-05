from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
)
from cam_pipeline.market_data import (
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    fetch_selection_market_data,
)

try:
    import pandas_ta_classic as ta  # noqa: F401
except ImportError:  # pragma: no cover
    ta = None


DEFAULT_RECENT_ROWS = 5
DEFAULT_INDICATORS = [
    "sma_20",
    "sma_50",
    "ema_20",
    "rsi_14",
    "macd_12_26_9",
    "bbands_20_2",
    "atr_14",
    "adx_14",
    "stoch_14_3_3",
    "obv",
    "volume_sma_20",
    "obv_sma_5",
    "obv_sma_20",
    "return_3",
    "return_5",
]
REQUIRED_ANALYSIS_COLUMNS = [
    "close",
    "sma_20",
    "sma_50",
    "ema_20",
    "rsi_14",
    "macd_line",
    "macd_signal",
    "macd_hist",
    "bb_lower",
    "bb_middle",
    "bb_upper",
    "bb_width",
    "atr_14",
    "adx_14",
    "dmp_14",
    "dmn_14",
    "stoch_k",
    "stoch_d",
    "obv",
    "volume_sma_20",
    "obv_sma_5",
    "obv_sma_20",
]


class TechnicalAnalysisError(RuntimeError):
    """Raised when technical indicators cannot be calculated."""


@dataclass
class CompanyTechnicalAnalysis:
    company_name: str
    company_name_ko: str
    ticker: str
    market: str
    yahoo_symbol: str
    row_count: int
    latest_date: Optional[str]
    latest_close: Optional[float]
    latest_indicators: dict[str, Any]
    signal_context: dict[str, Any]
    latest_signal: dict[str, Any]
    recent_rows: list[dict[str, Any]]
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_name_ko": self.company_name_ko,
            "ticker": self.ticker,
            "market": self.market,
            "yahoo_symbol": self.yahoo_symbol,
            "row_count": self.row_count,
            "latest_date": self.latest_date,
            "latest_close": self.latest_close,
            "latest_indicators": self.latest_indicators,
            "signal_context": self.signal_context,
            "latest_signal": self.latest_signal,
            "recent_rows": self.recent_rows,
            "error": self.error,
        }


def fetch_selection_technical_analysis(
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

    analyses = analyze_market_data_companies(
        market_result["market_data"]["companies"],
        recent_rows=recent_rows,
    )

    return {
        "article": market_result["article"],
        "provider": market_result["provider"],
        "model": market_result["model"],
        "selection": market_result["selection"],
        "market_data": market_result["market_data"],
        "technical_analysis": {
            "indicators": list(DEFAULT_INDICATORS),
            "recent_rows": recent_rows,
            "companies": analyses,
        },
    }


def analyze_market_data_companies(
    companies: list[dict[str, Any]],
    recent_rows: int = DEFAULT_RECENT_ROWS,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for company in companies:
        try:
            analysis = analyze_company_market_data(company, recent_rows=recent_rows)
            results.append(analysis.to_dict())
        except TechnicalAnalysisError as exc:
            results.append(
                CompanyTechnicalAnalysis(
                    company_name=str(company.get("company_name", "")).strip(),
                    company_name_ko=str(company.get("company_name_ko", "")).strip(),
                    ticker=str(company.get("ticker", "")).strip(),
                    market=str(company.get("market", "")).strip(),
                    yahoo_symbol=str(company.get("yahoo_symbol", "")).strip(),
                    row_count=0,
                    latest_date=None,
                    latest_close=None,
                    latest_indicators={},
                    signal_context={},
                    latest_signal={},
                    recent_rows=[],
                    error=str(exc),
                ).to_dict()
            )

    return results


def analyze_company_market_data(
    company: dict[str, Any],
    recent_rows: int = DEFAULT_RECENT_ROWS,
) -> CompanyTechnicalAnalysis:
    ensure_pandas_ta_available()

    if company.get("error"):
        raise TechnicalAnalysisError(str(company["error"]))

    ohlcv = company.get("ohlcv", [])
    if not isinstance(ohlcv, list) or not ohlcv:
        raise TechnicalAnalysisError("No OHLCV data available for technical analysis.")

    frame = pd.DataFrame(ohlcv).copy()
    required_columns = {"date", "open", "high", "low", "close", "volume"}
    if not required_columns.issubset(frame.columns):
        raise TechnicalAnalysisError("OHLCV data is missing required columns.")

    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").reset_index(drop=True)
    frame = frame.set_index("date")

    apply_indicators(frame)
    normalize_indicator_columns(frame)
    frame["volume_sma_20"] = frame["volume"].rolling(20).mean()
    add_obv_support_columns(frame)
    add_return_columns(frame)
    add_signal_columns(frame)

    frame = frame.reset_index()
    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")

    indicator_frame = frame.dropna(subset=REQUIRED_ANALYSIS_COLUMNS).reset_index(drop=True)
    if indicator_frame.empty:
        raise TechnicalAnalysisError(
            "Not enough price history to compute the configured indicators."
        )

    latest = indicator_frame.iloc[-1]
    latest_indicators = extract_latest_indicators(latest)
    signal_context = build_signal_context(latest_indicators)
    latest_signal = evaluate_signal_values(row_to_signal_input(latest))
    recent = indicator_frame.tail(recent_rows)

    return CompanyTechnicalAnalysis(
        company_name=str(company.get("company_name", "")).strip(),
        company_name_ko=str(company.get("company_name_ko", "")).strip(),
        ticker=str(company.get("ticker", "")).strip(),
        market=str(company.get("market", "")).strip(),
        yahoo_symbol=str(company.get("yahoo_symbol", "")).strip(),
        row_count=len(indicator_frame),
        latest_date=str(latest["date"]),
        latest_close=float(latest["close"]),
        latest_indicators=latest_indicators,
        signal_context=signal_context,
        latest_signal=latest_signal,
        recent_rows=recent_to_records(recent),
    )


def apply_indicators(frame: pd.DataFrame) -> None:
    frame.ta.sma(length=20, append=True)
    frame.ta.sma(length=50, append=True)
    frame.ta.ema(length=20, append=True)
    frame.ta.rsi(length=14, append=True)
    frame.ta.macd(fast=12, slow=26, signal=9, append=True)
    frame.ta.bbands(length=20, std=2, append=True)
    frame.ta.atr(length=14, append=True)
    frame.ta.adx(length=14, append=True)
    frame.ta.stoch(k=14, d=3, smooth_k=3, append=True)
    frame.ta.obv(append=True)


def normalize_indicator_columns(frame: pd.DataFrame) -> None:
    frame["sma_20"] = frame.get("SMA_20")
    frame["sma_50"] = frame.get("SMA_50")
    frame["ema_20"] = frame.get("EMA_20")
    frame["rsi_14"] = frame.get("RSI_14")
    frame["macd_line"] = frame.get("MACD_12_26_9")
    frame["macd_signal"] = frame.get("MACDs_12_26_9")
    frame["macd_hist"] = frame.get("MACDh_12_26_9")
    frame["bb_lower"] = frame.get("BBL_20_2.0")
    frame["bb_middle"] = frame.get("BBM_20_2.0")
    frame["bb_upper"] = frame.get("BBU_20_2.0")
    frame["bb_width"] = frame.get("BBB_20_2.0")

    atr_source = "ATRr_14" if "ATRr_14" in frame.columns else "ATR_14"
    frame["atr_14"] = frame.get(atr_source)

    frame["adx_14"] = frame.get("ADX_14")
    frame["dmp_14"] = frame.get("DMP_14")
    frame["dmn_14"] = frame.get("DMN_14")
    frame["stoch_k"] = frame.get("STOCHk_14_3_3")
    frame["stoch_d"] = frame.get("STOCHd_14_3_3")
    frame["obv"] = frame.get("OBV")


def add_obv_support_columns(frame: pd.DataFrame) -> None:
    frame["obv_sma_5"] = frame["obv"].rolling(5).mean()
    frame["obv_sma_20"] = frame["obv"].rolling(20).mean()
    frame["obv_trend_score"] = 0
    frame.loc[frame["obv_sma_5"] > frame["obv_sma_20"], "obv_trend_score"] = 1
    frame.loc[frame["obv_sma_5"] < frame["obv_sma_20"], "obv_trend_score"] = -1


def add_return_columns(frame: pd.DataFrame) -> None:
    frame["return_3"] = frame["close"].pct_change(3)
    frame["return_5"] = frame["close"].pct_change(5)


def add_signal_columns(frame: pd.DataFrame) -> None:
    regimes: list[str] = []
    signals: list[str] = []
    scores: list[float] = []

    for _, row in frame.iterrows():
        result = evaluate_signal_values(row_to_signal_input(row))
        regimes.append(result["regime"])
        signals.append(result["signal"])
        scores.append(result["score"])

    frame["market_regime"] = regimes
    frame["signal"] = signals
    frame["signal_score"] = scores


def row_to_signal_input(row: pd.Series) -> dict[str, Any]:
    return {
        "close": row.get("close"),
        "sma_20": row.get("sma_20"),
        "sma_50": row.get("sma_50"),
        "ema_20": row.get("ema_20"),
        "rsi_14": row.get("rsi_14"),
        "macd_line": row.get("macd_line"),
        "macd_signal": row.get("macd_signal"),
        "macd_hist": row.get("macd_hist"),
        "bb_lower": row.get("bb_lower"),
        "bb_middle": row.get("bb_middle"),
        "bb_upper": row.get("bb_upper"),
        "adx_14": row.get("adx_14"),
        "dmp_14": row.get("dmp_14"),
        "dmn_14": row.get("dmn_14"),
        "stoch_k": row.get("stoch_k"),
        "stoch_d": row.get("stoch_d"),
        "volume": row.get("volume"),
        "volume_sma_20": row.get("volume_sma_20"),
        "obv_sma_5": row.get("obv_sma_5"),
        "obv_sma_20": row.get("obv_sma_20"),
        "obv_trend_score": row.get("obv_trend_score"),
        "return_3": row.get("return_3"),
        "return_5": row.get("return_5"),
    }


def evaluate_signal_values(values: dict[str, Any]) -> dict[str, Any]:
    regime = detect_market_regime(values)

    if regime == "trend":
        score, reasons, score_breakdown = score_trend_following(values)
    elif regime == "range":
        score, reasons, score_breakdown = score_mean_reversion(values)
    else:
        score = 0.0
        detail = "Not enough data is available to classify the current market regime."
        reasons = [detail]
        score_breakdown = [
            {
                "signal": "regime",
                "score": 0.0,
                "detail": detail,
            }
        ]

    final_score = round(score, 2)
    return {
        "regime": regime,
        "signal": classify_trade_signal(final_score),
        "score": final_score,
        "reasons": reasons,
        "score_breakdown": score_breakdown,
    }


def detect_market_regime(values: dict[str, Any]) -> str:
    adx = values.get("adx_14")
    if not has_value(adx):
        return "unknown"
    if float(adx) >= 23:
        return "trend"
    return "range"


def score_trend_following(
    values: dict[str, Any],
) -> tuple[float, list[str], list[dict[str, Any]]]:
    score = 0.0
    reasons: list[str] = []
    score_breakdown: list[dict[str, Any]] = []
    close = values.get("close")

    if has_value(values.get("sma_20")) and has_value(values.get("sma_50")):
        if values["sma_20"] > values["sma_50"]:
            score += 2
            add_score_detail(
                score_breakdown,
                reasons,
                "trend",
                2.0,
                "SMA20 is above SMA50, which confirms a medium-term uptrend.",
            )
        else:
            score -= 2
            add_score_detail(
                score_breakdown,
                reasons,
                "trend",
                -2.0,
                "SMA20 is below SMA50, which confirms a medium-term downtrend.",
            )

    if has_value(close) and has_value(values.get("ema_20")):
        if close > values["ema_20"]:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "ema",
                1.0,
                "Close is above EMA20, so short-term price action is bullish.",
            )
        else:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "ema",
                -1.0,
                "Close is below EMA20, so short-term price action is bearish.",
            )

    if has_value(values.get("macd_line")) and has_value(values.get("macd_signal")):
        if values["macd_line"] > values["macd_signal"]:
            score += 2
            add_score_detail(
                score_breakdown,
                reasons,
                "macd",
                2.0,
                "MACD is above the signal line, which shows upward momentum.",
            )
            if has_value(values.get("macd_hist")) and values["macd_hist"] > 0:
                score += 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "macd_histogram",
                    1.0,
                    "MACD histogram is positive, which strengthens the bullish momentum.",
                )
        else:
            score -= 2
            add_score_detail(
                score_breakdown,
                reasons,
                "macd",
                -2.0,
                "MACD is below the signal line, which shows downward momentum.",
            )
            if has_value(values.get("macd_hist")) and values["macd_hist"] < 0:
                score -= 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "macd_histogram",
                    -1.0,
                    "MACD histogram is negative, which strengthens the bearish momentum.",
                )

    if (
        has_value(values.get("adx_14"))
        and has_value(values.get("dmp_14"))
        and has_value(values.get("dmn_14"))
    ):
        if values["dmp_14"] > values["dmn_14"]:
            score += 2
            add_score_detail(
                score_breakdown,
                reasons,
                "adx_di",
                2.0,
                "In a trend regime, +DI is above -DI, so the uptrend has the edge.",
            )
        else:
            score -= 2
            add_score_detail(
                score_breakdown,
                reasons,
                "adx_di",
                -2.0,
                "In a trend regime, -DI is above +DI, so the downtrend has the edge.",
            )

        if values["adx_14"] >= 30:
            if values["dmp_14"] > values["dmn_14"]:
                score += 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "adx_strength",
                    1.0,
                    "ADX is above 30, which reinforces the strong bullish trend.",
                )
            else:
                score -= 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "adx_strength",
                    -1.0,
                    "ADX is above 30, which reinforces the strong bearish trend.",
                )

    if has_value(values.get("rsi_14")):
        rsi = float(values["rsi_14"])
        if rsi >= 60:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi",
                1.0,
                "RSI is above 60, which supports trend-following strength.",
            )
        elif rsi <= 40:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi",
                -1.0,
                "RSI is below 40, which supports trend-following weakness.",
            )

        if rsi >= 70:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi_extreme",
                1.0,
                "RSI is staying above 70, which is consistent with a strong bullish trend.",
            )
        elif rsi <= 30:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi_extreme",
                -1.0,
                "RSI is staying below 30, which is consistent with a strong bearish trend.",
            )

    if has_value(values.get("volume")) and has_value(values.get("volume_sma_20")):
        if values["volume"] > values["volume_sma_20"] * 1.2:
            if score > 0:
                score += 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "volume",
                    1.0,
                    "Volume is at least 20% above average, confirming the bullish trend.",
                )
            elif score < 0:
                score -= 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "volume",
                    -1.0,
                    "Volume is at least 20% above average, confirming the bearish trend.",
                )
        else:
            add_score_detail(
                score_breakdown,
                reasons,
                "volume",
                0.0,
                "Volume is not elevated enough to strongly confirm the current trend.",
            )

    if has_value(values.get("obv_sma_5")) and has_value(values.get("obv_sma_20")):
        if values["obv_sma_5"] > values["obv_sma_20"]:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "obv",
                1.0,
                "OBV short-term average is above the long-term average, which supports accumulation.",
            )
        else:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "obv",
                -1.0,
                "OBV short-term average is below the long-term average, which suggests weaker flow.",
            )

    return score, reasons, score_breakdown


def score_mean_reversion(
    values: dict[str, Any],
) -> tuple[float, list[str], list[dict[str, Any]]]:
    score = 0.0
    reasons: list[str] = []
    score_breakdown: list[dict[str, Any]] = []
    close = values.get("close")

    if (
        has_value(close)
        and has_value(values.get("bb_lower"))
        and has_value(values.get("bb_middle"))
        and has_value(values.get("bb_upper"))
    ):
        if close < values["bb_lower"]:
            score += 3
            add_score_detail(
                score_breakdown,
                reasons,
                "bollinger",
                3.0,
                "Close is below the lower Bollinger Band, which suggests oversold conditions.",
            )
        elif close > values["bb_upper"]:
            score -= 3
            add_score_detail(
                score_breakdown,
                reasons,
                "bollinger",
                -3.0,
                "Close is above the upper Bollinger Band, which suggests overbought conditions.",
            )
        elif close < values["bb_middle"]:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "bollinger",
                1.0,
                "Close is below the Bollinger middle band, so price is leaning toward the lower end of the range.",
            )
        elif close > values["bb_middle"]:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "bollinger",
                -1.0,
                "Close is above the Bollinger middle band, so price is leaning toward the upper end of the range.",
            )

    if has_value(values.get("rsi_14")):
        rsi = float(values["rsi_14"])
        if rsi <= 30:
            score += 3
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi",
                3.0,
                "RSI is at or below 30, which suggests oversold conditions.",
            )
        elif rsi >= 70:
            score -= 3
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi",
                -3.0,
                "RSI is at or above 70, which suggests overbought conditions.",
            )
        elif rsi <= 40:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi",
                1.0,
                "RSI is at or below 40, so price is leaning toward the lower end of the range.",
            )
        elif rsi >= 60:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "rsi",
                -1.0,
                "RSI is at or above 60, so price is leaning toward the upper end of the range.",
            )

    if has_value(values.get("stoch_k")) and has_value(values.get("stoch_d")):
        if values["stoch_k"] < 20 and values["stoch_k"] > values["stoch_d"]:
            score += 2
            add_score_detail(
                score_breakdown,
                reasons,
                "stochastic",
                2.0,
                "Stochastic is rebounding from an oversold zone.",
            )
        elif values["stoch_k"] > 80 and values["stoch_k"] < values["stoch_d"]:
            score -= 2
            add_score_detail(
                score_breakdown,
                reasons,
                "stochastic",
                -2.0,
                "Stochastic is rolling over from an overbought zone.",
            )
        elif values["stoch_k"] < 20:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "stochastic",
                1.0,
                "Stochastic is still in an oversold zone.",
            )
        elif values["stoch_k"] > 80:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "stochastic",
                -1.0,
                "Stochastic is still in an overbought zone.",
            )

    if has_value(values.get("macd_line")) and has_value(values.get("macd_signal")):
        if values["macd_line"] > values["macd_signal"]:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "macd",
                1.0,
                "MACD is mildly bullish and supports a rebound case.",
            )
        else:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "macd",
                -1.0,
                "MACD is mildly bearish and supports a pullback case.",
            )

    if has_value(values.get("volume")) and has_value(values.get("volume_sma_20")):
        if values["volume"] > values["volume_sma_20"] * 1.3:
            if score >= 2:
                score += 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "volume",
                    1.0,
                    "Volume is spiking and strengthens the rebound setup.",
                )
            elif score <= -2:
                score -= 1
                add_score_detail(
                    score_breakdown,
                    reasons,
                    "volume",
                    -1.0,
                    "Volume is spiking and strengthens the downside reversal setup.",
                )
        else:
            add_score_detail(
                score_breakdown,
                reasons,
                "volume",
                0.0,
                "Volume is not spiking enough to strengthen the range-reversal setup.",
            )

    if has_value(values.get("obv_sma_5")) and has_value(values.get("obv_sma_20")):
        if score > 0 and values["obv_sma_5"] > values["obv_sma_20"]:
            score += 1
            add_score_detail(
                score_breakdown,
                reasons,
                "obv",
                1.0,
                "OBV supports the bullish reversal case.",
            )
        elif score < 0 and values["obv_sma_5"] < values["obv_sma_20"]:
            score -= 1
            add_score_detail(
                score_breakdown,
                reasons,
                "obv",
                -1.0,
                "OBV supports the bearish reversal case.",
            )

    return score, reasons, score_breakdown


def add_score_detail(
    score_breakdown: list[dict[str, Any]],
    reasons: list[str],
    signal: str,
    score: float,
    detail: str,
) -> None:
    score_breakdown.append(
        {
            "signal": signal,
            "score": round(score, 2),
            "detail": detail,
        }
    )
    reasons.append(detail)


def classify_trade_signal(score: float) -> str:
    if score >= 5:
        return "STRONG_BUY"
    if score >= 3:
        return "BUY"
    if score <= -5:
        return "STRONG_SELL"
    if score <= -3:
        return "SELL"
    return "HOLD"


def extract_latest_indicators(row: pd.Series) -> dict[str, Any]:
    return {
        "close": round_float(row.get("close")),
        "sma_20": round_float(row.get("sma_20")),
        "sma_50": round_float(row.get("sma_50")),
        "ema_20": round_float(row.get("ema_20")),
        "rsi_14": round_float(row.get("rsi_14")),
        "macd": round_float(row.get("macd_line")),
        "macd_signal": round_float(row.get("macd_signal")),
        "macd_histogram": round_float(row.get("macd_hist")),
        "bb_lower": round_float(row.get("bb_lower")),
        "bb_middle": round_float(row.get("bb_middle")),
        "bb_upper": round_float(row.get("bb_upper")),
        "bb_width": round_float(row.get("bb_width")),
        "atr_14": round_float(row.get("atr_14")),
        "adx_14": round_float(row.get("adx_14")),
        "dmp_14": round_float(row.get("dmp_14")),
        "dmn_14": round_float(row.get("dmn_14")),
        "stoch_k": round_float(row.get("stoch_k")),
        "stoch_d": round_float(row.get("stoch_d")),
        "obv": round_float(row.get("obv")),
        "volume_sma_20": round_float(row.get("volume_sma_20")),
        "obv_sma_5": round_float(row.get("obv_sma_5")),
        "obv_sma_20": round_float(row.get("obv_sma_20")),
        "obv_trend_score": int(row.get("obv_trend_score", 0)),
        "return_3": round_float(row.get("return_3")),
        "return_5": round_float(row.get("return_5")),
    }


def build_signal_context(indicators: dict[str, Any]) -> dict[str, Any]:
    close = indicators.get("close")
    sma_20 = indicators.get("sma_20")
    sma_50 = indicators.get("sma_50")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macd_signal")
    rsi = indicators.get("rsi_14")

    return {
        "price_vs_sma20": compare_values(close, sma_20),
        "price_vs_sma50": compare_values(close, sma_50),
        "sma20_vs_sma50": compare_values(sma_20, sma_50),
        "macd_vs_signal": compare_values(macd, macd_signal),
        "rsi_state": classify_rsi(rsi),
        "bollinger_position": classify_bollinger_position(indicators),
        "trend_strength": classify_trend_strength(indicators.get("adx_14")),
        "obv_trend": classify_obv_trend(indicators.get("obv_trend_score")),
        "market_regime": detect_market_regime(indicators),
    }


def recent_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        records.append(
            {
                "date": str(row["date"]),
                "close": round_float(row.get("close")),
                "sma_20": round_float(row.get("sma_20")),
                "sma_50": round_float(row.get("sma_50")),
                "ema_20": round_float(row.get("ema_20")),
                "rsi_14": round_float(row.get("rsi_14")),
                "macd": round_float(row.get("macd_line")),
                "macd_signal": round_float(row.get("macd_signal")),
                "macd_histogram": round_float(row.get("macd_hist")),
                "bb_lower": round_float(row.get("bb_lower")),
                "bb_middle": round_float(row.get("bb_middle")),
                "bb_upper": round_float(row.get("bb_upper")),
                "bb_width": round_float(row.get("bb_width")),
                "atr_14": round_float(row.get("atr_14")),
                "adx_14": round_float(row.get("adx_14")),
                "dmp_14": round_float(row.get("dmp_14")),
                "dmn_14": round_float(row.get("dmn_14")),
                "stoch_k": round_float(row.get("stoch_k")),
                "stoch_d": round_float(row.get("stoch_d")),
                "obv": round_float(row.get("obv")),
                "volume_sma_20": round_float(row.get("volume_sma_20")),
                "obv_sma_5": round_float(row.get("obv_sma_5")),
                "obv_sma_20": round_float(row.get("obv_sma_20")),
                "obv_trend_score": int(row.get("obv_trend_score", 0)),
                "return_3": round_float(row.get("return_3")),
                "return_5": round_float(row.get("return_5")),
                "market_regime": str(row.get("market_regime", "unknown")),
                "signal": str(row.get("signal", "HOLD")),
                "signal_score": round_float(row.get("signal_score")),
            }
        )
    return records


def round_float(value: Any) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 4)


def has_value(value: Any) -> bool:
    return value is not None and not pd.isna(value)


def compare_values(left: Optional[float], right: Optional[float]) -> str:
    if left is None or right is None:
        return "unknown"
    if left > right:
        return "above"
    if left < right:
        return "below"
    return "equal"


def classify_rsi(rsi: Optional[float]) -> str:
    if rsi is None:
        return "unknown"
    if rsi >= 70:
        return "overbought"
    if rsi <= 30:
        return "oversold"
    if rsi >= 60:
        return "bullish"
    if rsi <= 40:
        return "bearish"
    return "neutral"


def classify_bollinger_position(indicators: dict[str, Any]) -> str:
    close = indicators.get("close")
    lower = indicators.get("bb_lower")
    upper = indicators.get("bb_upper")
    middle = indicators.get("bb_middle")
    if close is None or lower is None or upper is None or middle is None:
        return "unknown"
    if close > upper:
        return "above_upper_band"
    if close < lower:
        return "below_lower_band"
    if close >= middle:
        return "upper_half"
    return "lower_half"


def classify_trend_strength(adx: Optional[float]) -> str:
    if adx is None:
        return "unknown"
    if adx >= 30:
        return "strong"
    if adx >= 23:
        return "moderate"
    return "weak"


def classify_obv_trend(obv_trend_score: Optional[int]) -> str:
    if obv_trend_score == 1:
        return "bullish"
    if obv_trend_score == -1:
        return "bearish"
    return "neutral"


def ensure_pandas_ta_available() -> None:
    if ta is None:
        raise TechnicalAnalysisError(
            "The 'pandas-ta-classic' package is not installed. "
            "Run `pip install -r requirements.txt`."
        )
