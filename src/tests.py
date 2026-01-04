"""Tests for the IBKR to IRPF application."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from src.calculator import calculate_holdings
from src.main import format_brl, format_usd
from src.models import Holding, Trade, TradeWithPtax
from src.parser import group_trades_by_symbol, parse_statement


class TestTrade:
    def test_total_usd_calculation(self):
        trade = Trade(
            symbol="VWRA",
            trade_date=date(2024, 1, 5),
            quantity=Decimal(2),
            price_usd=Decimal("115.94"),
            commission_usd=Decimal("1.91"),
        )

        expected = Decimal(2) * Decimal("115.94") + Decimal("1.91")
        assert trade.total_usd == expected

    def test_is_buy_positive_quantity(self):
        trade = Trade(
            symbol="VWRA",
            trade_date=date(2024, 1, 5),
            quantity=Decimal(2),
            price_usd=Decimal("115.94"),
            commission_usd=Decimal("1.91"),
        )

        assert trade.is_buy is True

    def test_is_buy_negative_quantity(self):
        trade = Trade(
            symbol="VWRA",
            trade_date=date(2024, 1, 5),
            quantity=Decimal(-2),
            price_usd=Decimal("115.94"),
            commission_usd=Decimal("1.91"),
        )

        assert trade.is_buy is False


class TestTradeWithPtax:
    def test_total_brl_calculation(self):
        trade = Trade(
            symbol="VWRA",
            trade_date=date(2024, 1, 5),
            quantity=Decimal(2),
            price_usd=Decimal("115.94"),
            commission_usd=Decimal("1.91"),
        )
        trade_with_ptax = TradeWithPtax(
            trade=trade,
            ptax_sell_rate=Decimal("4.8899"),
        )

        expected = trade.total_usd * Decimal("4.8899")
        assert trade_with_ptax.total_brl == expected


class TestHolding:
    def setup_method(self):
        trade1 = Trade(
            symbol="VWRA",
            trade_date=date(2024, 1, 5),
            quantity=Decimal(2),
            price_usd=Decimal("115.94"),
            commission_usd=Decimal("1.91"),
        )
        trade2 = Trade(
            symbol="VWRA",
            trade_date=date(2024, 2, 2),
            quantity=Decimal(3),
            price_usd=Decimal("120.00"),
            commission_usd=Decimal("1.91"),
        )

        self.holding = Holding(
            symbol="VWRA",
            description="VANG FTSE AW USDA",
            trades=(
                TradeWithPtax(trade=trade1, ptax_sell_rate=Decimal("4.8899")),
                TradeWithPtax(trade=trade2, ptax_sell_rate=Decimal("4.9471")),
            ),
        )

    def test_total_quantity(self):
        assert self.holding.total_quantity == Decimal(5)

    def test_total_acquisition_usd(self):
        trade1_usd = Decimal(2) * Decimal("115.94") + Decimal("1.91")
        trade2_usd = Decimal(3) * Decimal("120.00") + Decimal("1.91")
        expected = trade1_usd + trade2_usd
        assert self.holding.total_acquisition_usd == expected

    def test_total_acquisition_brl(self):
        trade1_brl = (Decimal(2) * Decimal("115.94") + Decimal("1.91")) * Decimal("4.8899")
        trade2_brl = (Decimal(3) * Decimal("120.00") + Decimal("1.91")) * Decimal("4.9471")
        expected = trade1_brl + trade2_brl
        assert self.holding.total_acquisition_brl == expected

    def test_average_price_usd(self):
        expected = self.holding.total_acquisition_usd / Decimal(5)
        assert self.holding.average_price_usd == expected

    def test_average_price_brl(self):
        expected = self.holding.total_acquisition_brl / Decimal(5)
        assert self.holding.average_price_brl == expected

    def test_average_price_with_zero_quantity(self):
        empty_holding = Holding(symbol="TEST", description="Test", trades=())
        assert empty_holding.average_price_usd == Decimal(0)
        assert empty_holding.average_price_brl == Decimal(0)


class TestParseStatement:
    def test_parse_buy_trades(self):
        # fmt: off
        csv_content = (
            "Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,"
            "Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,"
            "Realized P/L,MTM P/L,Code\n"
            'Trades,Data,Order,Stocks,USD,VWRA,"2024-01-05, 10:30:00",'
            "2,115.94,116.00,-231.88,-1.91,233.79,0,0.12,O\n"
            'Trades,Data,Order,Stocks,USD,VWRA,"2024-02-02, 14:45:30",'
            "3,120.00,120.50,-360.00,-1.91,361.91,0,1.50,O\n"
            "Financial Instrument Information,Data,Stocks,VWRA,VANG FTSE AW USDA\n"
        )
        # fmt: on
        trades, instrument_info = parse_statement(csv_content)

        assert len(trades) == 2
        assert trades[0].symbol == "VWRA"
        assert trades[0].quantity == Decimal(2)
        assert trades[0].price_usd == Decimal("115.94")
        assert trades[0].trade_date == date(2024, 1, 5)
        assert trades[1].quantity == Decimal(3)
        assert instrument_info["VWRA"] == "VANG FTSE AW USDA"

    def test_ignore_sell_trades(self):
        # fmt: off
        csv_content = (
            "Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,"
            "Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,"
            "Realized P/L,MTM P/L,Code\n"
            'Trades,Data,Order,Stocks,USD,VWRA,"2024-01-05, 10:30:00",'
            "-5,115.94,116.00,579.70,-1.91,0,50.00,0,C\n"
        )
        # fmt: on
        trades, _ = parse_statement(csv_content)

        assert len(trades) == 0

    def test_ignore_subtotal_and_total_rows(self):
        # fmt: off
        csv_content = (
            "Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,"
            "Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,"
            "Realized P/L,MTM P/L,Code\n"
            'Trades,Data,Order,Stocks,USD,VWRA,"2024-01-05, 10:30:00",'
            "2,115.94,116.00,-231.88,-1.91,233.79,0,0.12,O\n"
            "Trades,SubTotal,,Stocks,USD,VWRA,,2,,,-231.88,-1.91,233.79,0,0.12,\n"
            "Trades,Total,,Stocks,USD,,,,,,-231.88,-1.91,233.79,0,0.12,\n"
        )
        # fmt: on
        trades, _ = parse_statement(csv_content)

        assert len(trades) == 1

    def test_empty_statement(self):
        csv_content = "Statement,Header,Field Name,Field Value\n"
        trades, instrument_info = parse_statement(csv_content)

        assert len(trades) == 0
        assert len(instrument_info) == 0


class TestGroupTradesBySymbol:
    def test_grouping(self):
        trades = [
            Trade(
                symbol="VWRA",
                trade_date=date(2024, 1, 5),
                quantity=Decimal(2),
                price_usd=Decimal("115.94"),
                commission_usd=Decimal("1.91"),
            ),
            Trade(
                symbol="AAPL",
                trade_date=date(2024, 1, 6),
                quantity=Decimal(10),
                price_usd=Decimal("180.00"),
                commission_usd=Decimal("1.00"),
            ),
            Trade(
                symbol="VWRA",
                trade_date=date(2024, 2, 2),
                quantity=Decimal(3),
                price_usd=Decimal("120.00"),
                commission_usd=Decimal("1.91"),
            ),
        ]

        grouped = group_trades_by_symbol(trades)

        assert len(grouped) == 2
        assert len(grouped["VWRA"]) == 2
        assert len(grouped["AAPL"]) == 1


class TestCalculateHoldings:
    @patch("src.calculator.get_ptax_rates_for_dates")
    def test_calculate_holdings(self, mock_ptax):
        mock_ptax.return_value = {
            date(2024, 1, 5): Decimal("4.8899"),
            date(2024, 2, 2): Decimal("4.9471"),
        }

        trades = [
            Trade(
                symbol="VWRA",
                trade_date=date(2024, 1, 5),
                quantity=Decimal(2),
                price_usd=Decimal("115.94"),
                commission_usd=Decimal("1.91"),
            ),
            Trade(
                symbol="VWRA",
                trade_date=date(2024, 2, 2),
                quantity=Decimal(3),
                price_usd=Decimal("120.00"),
                commission_usd=Decimal("1.91"),
            ),
        ]
        instrument_info = {"VWRA": "VANG FTSE AW USDA"}

        holdings = calculate_holdings(trades, instrument_info)

        assert len(holdings) == 1
        assert holdings[0].symbol == "VWRA"
        assert holdings[0].total_quantity == Decimal(5)
        assert len(holdings[0].trades) == 2

    def test_calculate_holdings_empty(self):
        holdings = calculate_holdings([], {})

        assert len(holdings) == 0


class TestFormatters:
    def test_format_brl(self):
        assert format_brl(Decimal("1234.56")) == "R$ 1.234,56"
        assert format_brl(Decimal("1000000.00")) == "R$ 1.000.000,00"

    def test_format_usd(self):
        assert format_usd(Decimal("1234.56")) == "US$1,234.56"
        assert format_usd(Decimal("1000000.00")) == "US$1,000,000.00"
