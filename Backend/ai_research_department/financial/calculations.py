from __future__ import annotations


def calculate_revenue(volume: float, asp: float) -> float:
    """Calculate revenue from shipment volume and ASP."""
    return volume * asp


def calculate_gross_profit(revenue: float, gross_margin: float) -> float:
    """Calculate gross profit from revenue and gross margin."""
    return revenue * gross_margin


def calculate_operating_profit(gross_profit: float, operating_expenses: float) -> float:
    """Calculate operating profit."""
    return gross_profit - operating_expenses


def calculate_eps(net_income: float, shares_outstanding: float) -> float:
    """Calculate EPS, guarding against division by zero."""
    if shares_outstanding == 0:
        raise ValueError("shares_outstanding must not be zero.")
    return net_income / shares_outstanding


def calculate_revision_pct(new_value: float, previous_value: float | None) -> float | None:
    """Calculate percentage revision if a previous value is available."""
    if previous_value in (None, 0):
        return None
    return (new_value - previous_value) / previous_value * 100


def calculate_earnings_surprise_pct(our_estimate: float, consensus: float | None) -> float | None:
    """Compare estimate with consensus only when consensus exists."""
    if consensus in (None, 0):
        return None
    return (our_estimate - consensus) / consensus * 100
