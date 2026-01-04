"""Service for fetching PTAX exchange rates from BCB (Banco Central do Brasil)."""

from datetime import date, timedelta
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, cast

from bcb import sgs

if TYPE_CHECKING:
    import pandas as pd

# PTAX sell rate series code in BCB SGS
PTAX_SELL_RATE_CODE = 1


@lru_cache(maxsize=1)
def _get_ptax_series(start_date: date, end_date: date) -> dict[date, Decimal]:
    """
    Fetch PTAX sell rates for a date range and cache the result.

    Args:
        start_date: Start date for the series.
        end_date: End date for the series.

    Returns:
        Dict mapping dates to PTAX sell rates.
    """
    df = cast("pd.DataFrame", sgs.get({"ptax": PTAX_SELL_RATE_CODE}, start=start_date, end=end_date))

    rates: dict[date, Decimal] = {}
    for idx, row in df.iterrows():
        rate_date: date = idx.date() if hasattr(idx, "date") else idx  # type: ignore[union-attr]
        rates[rate_date] = Decimal(str(row["ptax"]))

    return rates


def get_ptax_rates_for_dates(dates: list[date]) -> dict[date, Decimal]:
    """
    Get PTAX sell rates for multiple dates efficiently.

    Fetches the entire range at once to minimize API calls.

    Args:
        dates: List of dates to get rates for.

    Returns:
        Dict mapping each input date to its PTAX sell rate.
    """
    if not dates:
        return {}

    # Clear cache to fetch fresh data for the new range
    _get_ptax_series.cache_clear()

    # Determine the date range needed
    min_date = min(dates) - timedelta(days=10)
    max_date = max(dates)

    rates = _get_ptax_series(min_date, max_date)

    result: dict[date, Decimal] = {}
    for trade_date in dates:
        # Find the rate for this date or the most recent previous date
        for days_back in range(11):
            check_date = trade_date - timedelta(days=days_back)
            if check_date in rates:
                result[trade_date] = rates[check_date]
                break
        else:
            raise ValueError(f"No PTAX rate found for {trade_date}")

    return result
