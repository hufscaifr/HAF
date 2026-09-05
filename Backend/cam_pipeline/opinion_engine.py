from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from cam_pipeline.company_selector import (
    DEFAULT_ARTICLE_CHAR_LIMIT,
    DEFAULT_PROVIDER,
)
from cam_pipeline.market_data import DEFAULT_INTERVAL, DEFAULT_PERIOD
from cam_pipeline.technical_analysis import (
    DEFAULT_RECENT_ROWS,
    fetch_selection_technical_analysis,
)

DETAIL_TRANSLATIONS = {
    "SMA20 is above SMA50, which confirms a medium-term uptrend.": "SMA20이 SMA50 위에 있어 중기 상승 추세가 확인됩니다.",
    "SMA20 is below SMA50, which confirms a medium-term downtrend.": "SMA20이 SMA50 아래에 있어 중기 하락 추세가 확인됩니다.",
    "Close is above EMA20, so short-term price action is bullish.": "종가가 EMA20 위에 있어 단기 흐름이 강세입니다.",
    "Close is below EMA20, so short-term price action is bearish.": "종가가 EMA20 아래에 있어 단기 흐름이 약세입니다.",
    "MACD is above the signal line, which shows upward momentum.": "MACD가 시그널선 위에 있어 상승 모멘텀이 나타납니다.",
    "MACD is below the signal line, which shows downward momentum.": "MACD가 시그널선 아래에 있어 하락 모멘텀이 나타납니다.",
    "MACD histogram is positive, which strengthens the bullish momentum.": "MACD 히스토그램이 양수여서 강세 모멘텀이 강화됩니다.",
    "MACD histogram is negative, which strengthens the bearish momentum.": "MACD 히스토그램이 음수여서 약세 모멘텀이 강화됩니다.",
    "In a trend regime, +DI is above -DI, so the uptrend has the edge.": "추세장에서 +DI가 -DI보다 높아 상승 추세가 우세합니다.",
    "In a trend regime, -DI is above +DI, so the downtrend has the edge.": "추세장에서 -DI가 +DI보다 높아 하락 추세가 우세합니다.",
    "ADX is above 30, which reinforces the strong bullish trend.": "ADX가 30 이상으로 강한 상승 추세를 뒷받침합니다.",
    "ADX is above 30, which reinforces the strong bearish trend.": "ADX가 30 이상으로 강한 하락 추세를 뒷받침합니다.",
    "RSI is above 60, which supports trend-following strength.": "RSI가 60 이상으로 추세 추종 관점의 강세를 지지합니다.",
    "RSI is below 40, which supports trend-following weakness.": "RSI가 40 이하로 추세 추종 관점의 약세를 지지합니다.",
    "RSI is staying above 70, which is consistent with a strong bullish trend.": "RSI가 70 이상을 유지해 강한 상승 추세와 일치합니다.",
    "RSI is staying below 30, which is consistent with a strong bearish trend.": "RSI가 30 이하를 유지해 강한 하락 추세와 일치합니다.",
    "Volume is at least 20% above average, confirming the bullish trend.": "거래량이 평균 대비 20% 이상 높아 상승 추세를 확인해 줍니다.",
    "Volume is at least 20% above average, confirming the bearish trend.": "거래량이 평균 대비 20% 이상 높아 하락 추세를 확인해 줍니다.",
    "Volume is not elevated enough to strongly confirm the current trend.": "거래량이 현재 추세를 강하게 확인할 만큼 크지는 않습니다.",
    "OBV short-term average is above the long-term average, which supports accumulation.": "OBV 단기 평균이 장기 평균 위에 있어 수급상 매수 우위가 나타납니다.",
    "OBV short-term average is below the long-term average, which suggests weaker flow.": "OBV 단기 평균이 장기 평균 아래에 있어 수급이 약한 편입니다.",
    "Close is below the lower Bollinger Band, which suggests oversold conditions.": "종가가 볼린저밴드 하단 아래에 있어 과매도 가능성이 있습니다.",
    "Close is above the upper Bollinger Band, which suggests overbought conditions.": "종가가 볼린저밴드 상단 위에 있어 과매수 가능성이 있습니다.",
    "Close is below the Bollinger middle band, so price is leaning toward the lower end of the range.": "종가가 볼린저 중단 아래에 있어 박스권 하단에 가까운 위치입니다.",
    "Close is above the Bollinger middle band, so price is leaning toward the upper end of the range.": "종가가 볼린저 중단 위에 있어 박스권 상단에 가까운 위치입니다.",
    "RSI is at or below 30, which suggests oversold conditions.": "RSI가 30 이하로 과매도 구간입니다.",
    "RSI is at or above 70, which suggests overbought conditions.": "RSI가 70 이상으로 과매수 구간입니다.",
    "RSI is at or below 40, so price is leaning toward the lower end of the range.": "RSI가 40 이하로 박스권 저점 쪽에 가깝습니다.",
    "RSI is at or above 60, so price is leaning toward the upper end of the range.": "RSI가 60 이상으로 박스권 고점 쪽에 가깝습니다.",
    "Stochastic is rebounding from an oversold zone.": "스토캐스틱이 과매도권에서 반등 신호를 보입니다.",
    "Stochastic is rolling over from an overbought zone.": "스토캐스틱이 과매수권에서 하락 전환 신호를 보입니다.",
    "Stochastic is still in an oversold zone.": "스토캐스틱이 여전히 과매도권에 머물고 있습니다.",
    "Stochastic is still in an overbought zone.": "스토캐스틱이 여전히 과매수권에 머물고 있습니다.",
    "MACD is mildly bullish and supports a rebound case.": "MACD가 보조적으로 강세를 보여 반등 시나리오를 지지합니다.",
    "MACD is mildly bearish and supports a pullback case.": "MACD가 보조적으로 약세를 보여 조정 시나리오를 지지합니다.",
    "Volume is spiking and strengthens the rebound setup.": "거래량 급증이 반등 시나리오를 강화합니다.",
    "Volume is spiking and strengthens the downside reversal setup.": "거래량 급증이 하락 전환 시나리오를 강화합니다.",
    "Volume is not spiking enough to strengthen the range-reversal setup.": "거래량이 박스권 반전 시나리오를 강화할 만큼 크지는 않습니다.",
    "OBV supports the bullish reversal case.": "OBV가 상승 반전 시나리오를 지지합니다.",
    "OBV supports the bearish reversal case.": "OBV가 하락 반전 시나리오를 지지합니다.",
    "Not enough data is available to classify the current market regime.": "현재 시장 국면을 판단하기에 데이터가 충분하지 않습니다.",
}


@dataclass
class CompanyOpinion:
    company_name: str
    company_name_ko: str
    ticker: str
    market: str
    yahoo_symbol: str
    opinion: str
    score: float
    confidence: float
    risk_level: str
    rationale: str
    positives: list[str]
    negatives: list[str]
    score_breakdown: list[dict[str, Any]]
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_name_ko": self.company_name_ko,
            "ticker": self.ticker,
            "market": self.market,
            "yahoo_symbol": self.yahoo_symbol,
            "opinion": self.opinion,
            "score": self.score,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "rationale": self.rationale,
            "positives": self.positives,
            "negatives": self.negatives,
            "score_breakdown": self.score_breakdown,
            "error": self.error,
        }


def fetch_selection_opinions(
    url: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    max_companies: int = 3,
    article_char_limit: int = DEFAULT_ARTICLE_CHAR_LIMIT,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
    recent_rows: int = DEFAULT_RECENT_ROWS,
) -> dict[str, Any]:
    technical_result = fetch_selection_technical_analysis(
        url=url,
        provider=provider,
        model=model,
        max_companies=max_companies,
        article_char_limit=article_char_limit,
        period=period,
        interval=interval,
        recent_rows=recent_rows,
    )

    opinions = derive_company_opinions(
        technical_companies=technical_result["technical_analysis"]["companies"],
    )

    return {
        "article": technical_result["article"],
        "provider": technical_result["provider"],
        "model": technical_result["model"],
        "selection": technical_result["selection"],
        "market_data": technical_result["market_data"],
        "technical_analysis": technical_result["technical_analysis"],
        "opinions": {
            "method": "regime_aware_technical_score_engine_v3",
            "companies": opinions,
        },
    }


def derive_company_opinions(
    technical_companies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        derive_company_opinion(company).to_dict()
        for company in technical_companies
    ]


def derive_company_opinion(
    technical_company: dict[str, Any],
) -> CompanyOpinion:
    identity = {
        "company_name": str(technical_company.get("company_name", "")).strip(),
        "company_name_ko": str(technical_company.get("company_name_ko", "")).strip(),
        "ticker": str(technical_company.get("ticker", "")).strip(),
        "market": str(technical_company.get("market", "")).strip(),
        "yahoo_symbol": str(technical_company.get("yahoo_symbol", "")).strip(),
    }

    if technical_company.get("error"):
        return CompanyOpinion(
            **identity,
            opinion="분석 불가",
            score=0.0,
            confidence=0.0,
            risk_level="알 수 없음",
            rationale=str(technical_company["error"]),
            positives=[],
            negatives=[],
            score_breakdown=[],
            error=str(technical_company["error"]),
        )

    indicators = technical_company.get("latest_indicators", {})
    latest_signal = technical_company.get("latest_signal", {})
    regime = str(latest_signal.get("regime", "unknown")).strip()
    breakdown = normalize_breakdown(latest_signal.get("score_breakdown", []))

    if not latest_signal:
        return CompanyOpinion(
            **identity,
            opinion="분석 불가",
            score=0.0,
            confidence=0.0,
            risk_level="알 수 없음",
            rationale="최신 기술적 신호를 계산할 수 없습니다.",
            positives=[],
            negatives=[],
            score_breakdown=[],
            error="최신 기술적 신호를 계산할 수 없습니다.",
        )

    score = round(float(latest_signal.get("score", 0.0)), 2)
    opinion = normalize_opinion_label(latest_signal.get("signal"))
    confidence = estimate_confidence(score, breakdown)
    risk_level = classify_risk_level(indicators)

    positives = collect_details(breakdown, positive=True)
    negatives = collect_details(breakdown, positive=False)
    neutral_notes = collect_neutral_details(breakdown)
    rationale = build_rationale(
        opinion=opinion,
        regime=regime,
        positives=positives,
        negatives=negatives,
        neutral_notes=neutral_notes,
        risk_level=risk_level,
    )

    return CompanyOpinion(
        **identity,
        opinion=opinion,
        score=score,
        confidence=confidence,
        risk_level=risk_level,
        rationale=rationale,
        positives=positives,
        negatives=negatives,
        score_breakdown=breakdown,
    )


def normalize_breakdown(raw_breakdown: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_breakdown, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_breakdown:
        if not isinstance(item, dict):
            continue
        detail = str(item.get("detail", "")).strip()
        if not detail:
            continue
        normalized.append(
            {
                "signal": str(item.get("signal", "")).strip(),
                "score": round(float(item.get("score", 0.0)), 2),
                "detail": translate_detail(detail),
            }
        )
    return normalized


def collect_details(
    breakdown: list[dict[str, Any]],
    *,
    positive: bool,
) -> list[str]:
    filtered: list[str] = []

    for item in breakdown:
        score = float(item["score"])
        if positive and score <= 0:
            continue
        if not positive and score >= 0:
            continue
        detail = item["detail"]
        if detail not in filtered:
            filtered.append(detail)

    return filtered


def collect_neutral_details(breakdown: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    for item in breakdown:
        if float(item["score"]) != 0:
            continue
        detail = item["detail"]
        if detail not in notes:
            notes.append(detail)
    return notes


def normalize_opinion_label(raw_signal: Any) -> str:
    signal = str(raw_signal or "").strip().upper()
    if signal == "STRONG_BUY":
        return "강력 매수"
    if signal == "BUY":
        return "매수"
    if signal == "STRONG_SELL":
        return "강력 매도"
    if signal == "SELL":
        return "매도"
    if signal == "HOLD":
        return "보유"
    return "분석 불가"


def estimate_confidence(score: float, breakdown: list[dict[str, Any]]) -> float:
    aligned = sum(1 for item in breakdown if abs(float(item["score"])) >= 1)
    confidence = 0.45 + min(abs(score), 6) * 0.06 + min(aligned, 5) * 0.03
    return round(min(confidence, 0.95), 3)


def classify_risk_level(indicators: dict[str, Any]) -> str:
    close = indicators.get("close")
    atr = indicators.get("atr_14")
    rsi = indicators.get("rsi_14")
    if close is None or atr is None or close == 0:
        return "알 수 없음"

    atr_ratio = atr / close
    if atr_ratio >= 0.06 or (rsi is not None and (rsi >= 70 or rsi <= 30)):
        return "높음"
    if atr_ratio >= 0.03:
        return "보통"
    return "낮음"


def build_rationale(
    opinion: str,
    regime: str,
    positives: list[str],
    negatives: list[str],
    neutral_notes: list[str],
    risk_level: str,
) -> str:
    if positives:
        positive_text = "; ".join(positives[:2])
    else:
        positive_text = "강한 매수 근거는 많지 않습니다."

    if negatives:
        negative_text = "; ".join(negatives[:2])
    else:
        negative_text = "강한 매도 근거는 많지 않습니다."

    regime_text = translate_regime(regime)
    rationale = (
        f"{regime_text} 국면 기준 가중 기술적 점수에 따른 최종 의견은 {opinion}입니다. "
        f"긍정 요인: {positive_text} "
        f"주의 요인: {negative_text} "
    )

    if neutral_notes:
        rationale += f"추가 참고: {neutral_notes[0]} "

    rationale += f"예상 위험도는 {risk_level}입니다."
    return rationale


def translate_detail(detail: str) -> str:
    return DETAIL_TRANSLATIONS.get(detail, detail)


def translate_regime(regime: str) -> str:
    if regime == "trend":
        return "추세장"
    if regime == "range":
        return "횡보장"
    return "미확인"
