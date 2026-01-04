"""Parser for IBKR CSV statement files."""

import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO

from src.models import Trade


def parse_statement(content: str) -> tuple[list[Trade], dict[str, str]]:
    """
    Parse an IBKR CSV statement and extract trades and instrument info.

    Args:
        content: The CSV file content as a string.

    Returns:
        A tuple of (trades, instrument_descriptions) where:
        - trades: List of Trade objects for all buy orders
        - instrument_descriptions: Dict mapping symbol to description
    """
    trades = []
    instrument_info: dict[str, str] = {}

    reader = csv.reader(StringIO(content))

    for row in reader:
        if len(row) < 2:
            continue

        section = row[0]
        row_type = row[1]

        # Parse trade data
        if section == "Trades" and row_type == "Data" and len(row) >= 14:
            trade = _parse_trade_row(row)
            if trade and trade.is_buy:
                trades.append(trade)

        # Parse instrument descriptions
        if section == "Financial Instrument Information" and row_type == "Data":
            if len(row) >= 4:
                symbol = row[3]
                description = row[4] if len(row) > 4 else symbol
                instrument_info[symbol] = description

    return trades, instrument_info


def _parse_trade_row(row: list[str]) -> Trade | None:
    """
    Parse a single trade row from the CSV.

    Expected columns (0-indexed):
    0: Section name (Trades)
    1: Row type (Data)
    2: DataDiscriminator (Order, SubTotal, Total)
    3: Asset Category
    4: Currency
    5: Symbol
    6: Date/Time
    7: Quantity
    8: T. Price (Trade Price)
    9: C. Price (Close Price)
    10: Proceeds
    11: Comm/Fee
    12: Basis
    13: Realized P/L
    14: MTM P/L
    15: Code
    """
    try:
        data_discriminator = row[2]

        # Only process actual orders, not subtotals or totals
        if data_discriminator != "Order":
            return None

        asset_category = row[3]
        if asset_category != "Stocks":
            return None

        symbol = row[5]
        datetime_str = row[6]
        quantity_str = row[7]
        price_str = row[8]
        commission_str = row[11]

        # Parse date/time (format: "2025-01-03, 07:52:59")
        trade_date = datetime.strptime(datetime_str, "%Y-%m-%d, %H:%M:%S").date()

        # Parse numeric values
        quantity = Decimal(quantity_str)
        price = Decimal(price_str)
        commission = abs(Decimal(commission_str))

        return Trade(
            symbol=symbol,
            trade_date=trade_date,
            quantity=quantity,
            price_usd=price,
            commission_usd=commission,
        )

    except (ValueError, IndexError, KeyError):
        return None


def group_trades_by_symbol(trades: list[Trade]) -> dict[str, list[Trade]]:
    """Group a list of trades by their symbol."""
    grouped: dict[str, list[Trade]] = {}

    for trade in trades:
        if trade.symbol not in grouped:
            grouped[trade.symbol] = []
        grouped[trade.symbol].append(trade)

    return grouped
