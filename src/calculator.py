"""Calculator for IRPF declaration values."""

from src.models import Holding, Trade, TradeWithPtax
from src.parser import group_trades_by_symbol
from src.ptax import get_ptax_rates_for_dates


def calculate_holdings(trades: list[Trade], instrument_info: dict[str, str]) -> list[Holding]:
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
        trades_with_ptax = tuple(
            TradeWithPtax(trade=trade, ptax_sell_rate=ptax_rates[trade.trade_date]) for trade in symbol_trades
        )

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
