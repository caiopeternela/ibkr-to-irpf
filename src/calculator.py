"""Calculator for IRPF declaration values."""

from datetime import date

from src.models import Holding, Trade, TradeWithPtax
from src.parser import group_trades_by_symbol
from src.ptax import get_ptax_rates_for_dates


def calculate_holdings(
    trades: list[Trade],
    instrument_info: dict[str, str],
) -> list[Holding]:
    """
    Calculate holdings with PTAX-converted BRL values.

    Args:
        trades: List of buy trades from the statement.
        instrument_info: Dict mapping symbol to description.

    Returns:
        List of Holding objects with all trades enriched with PTAX rates.
    """
    if not trades:
        return []

    # Get all unique trade dates
    trade_dates = list({t.trade_date for t in trades})

    # Fetch PTAX rates for all dates at once
    ptax_rates = get_ptax_rates_for_dates(trade_dates)

    # Group trades by symbol
    grouped = group_trades_by_symbol(trades)

    holdings = []
    for symbol, symbol_trades in grouped.items():
        # Enrich trades with PTAX rates
        trades_with_ptax = [
            TradeWithPtax(
                trade=trade,
                ptax_sell_rate=ptax_rates[trade.trade_date],
            )
            for trade in symbol_trades
        ]

        # Get description from instrument info or use symbol as fallback
        description = instrument_info.get(symbol, symbol)

        holdings.append(
            Holding(
                symbol=symbol,
                description=description,
                trades=trades_with_ptax,
            )
        )

    return holdings


def extract_year_from_trades(trades: list[Trade]) -> int | None:
    """
    Extract the year from the trades.

    Returns the year of the most recent trade, or None if no trades.
    """
    if not trades:
        return None

    return max(t.trade_date for t in trades).year


def filter_trades_by_year(trades: list[Trade], year: int) -> list[Trade]:
    """
    Filter trades to only include those from a specific year.

    Args:
        trades: List of all trades.
        year: The year to filter for.

    Returns:
        List of trades from the specified year.
    """
    return [t for t in trades if t.trade_date.year == year]


def filter_trades_until_date(trades: list[Trade], end_date: date) -> list[Trade]:
    """
    Filter trades to only include those up to and including a specific date.

    Args:
        trades: List of all trades.
        end_date: The end date (inclusive).

    Returns:
        List of trades up to the specified date.
    """
    return [t for t in trades if t.trade_date <= end_date]
