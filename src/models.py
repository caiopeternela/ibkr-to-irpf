from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Trade:
    """Represents a single trade from IBKR statement."""

    symbol: str
    trade_date: date
    quantity: Decimal
    price_usd: Decimal
    commission_usd: Decimal

    @property
    def total_usd(self) -> Decimal:
        """Total cost in USD including commission."""
        return self.quantity * self.price_usd + self.commission_usd

    @property
    def is_buy(self) -> bool:
        """True if this is a buy trade."""
        return self.quantity > 0


@dataclass(frozen=True)
class TradeWithPtax:
    """A trade enriched with PTAX exchange rate and BRL values."""

    trade: Trade
    ptax_sell_rate: Decimal

    @property
    def total_brl(self) -> Decimal:
        """Total acquisition value in BRL."""
        return self.trade.total_usd * self.ptax_sell_rate


@dataclass(frozen=True)
class Holding:
    """Aggregated holding for a symbol with all buy trades."""

    symbol: str
    description: str
    trades: tuple[TradeWithPtax, ...]

    @property
    def total_quantity(self) -> Decimal:
        """Total quantity of shares held."""
        return sum((t.trade.quantity for t in self.trades), Decimal(0))

    @property
    def total_acquisition_usd(self) -> Decimal:
        """Total acquisition value in USD."""
        return sum((t.trade.total_usd for t in self.trades), Decimal(0))

    @property
    def total_acquisition_brl(self) -> Decimal:
        """Total acquisition value in BRL."""
        return sum((t.total_brl for t in self.trades), Decimal(0))

    @property
    def average_price_usd(self) -> Decimal:
        """Average acquisition price per share in USD."""
        if self.total_quantity == 0:
            return Decimal(0)
        return self.total_acquisition_usd / self.total_quantity

    @property
    def average_price_brl(self) -> Decimal:
        """Average acquisition price per share in BRL."""
        if self.total_quantity == 0:
            return Decimal(0)
        return self.total_acquisition_brl / self.total_quantity
