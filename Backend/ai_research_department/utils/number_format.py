from __future__ import annotations

from typing import Any


def format_korean_number(value: Any, unit: str | None = None, decimals: int = 1) -> str:
    """Format large display numbers with Korean units while keeping small values readable."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A" if value is None else str(value)

    suffix = _display_unit(unit)
    abs_value = abs(number)
    if suffix in {"원", "주"}:
        scaled, korean_unit = _scale_korean(abs_value)
        sign = "-" if number < 0 else ""
        if korean_unit:
            return f"{sign}{_trim_decimal(scaled, decimals)}{korean_unit}{suffix}"
        return f"{number:,.0f}{suffix}"
    if suffix:
        return f"{_trim_decimal(number, decimals)}{suffix}"
    scaled, korean_unit = _scale_korean(abs_value)
    sign = "-" if number < 0 else ""
    if korean_unit:
        return f"{sign}{_trim_decimal(scaled, decimals)}{korean_unit}"
    return f"{number:,.0f}"


def _scale_korean(abs_value: float) -> tuple[float, str]:
    if abs_value >= 1_0000_0000_0000:
        return abs_value / 1_0000_0000_0000, "조"
    if abs_value >= 1_0000_0000:
        return abs_value / 1_0000_0000, "억"
    if abs_value >= 1_0000:
        return abs_value / 1_0000, "만"
    return abs_value, ""


def _display_unit(unit: str | None) -> str:
    normalized = (unit or "").strip()
    lower = normalized.lower()
    if lower in {"krw", "krw/share"}:
        return "원"
    if lower in {"shares", "share"}:
        return "주"
    if normalized in {"%", "x"}:
        return normalized
    return normalized


def _trim_decimal(value: float, decimals: int) -> str:
    text = f"{value:,.{decimals}f}"
    if "." not in text:
        return text
    return text.rstrip("0").rstrip(".")
