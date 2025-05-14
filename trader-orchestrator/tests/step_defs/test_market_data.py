"""Step definitions for the market data feature."""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from ib_insync import IB, BarData, Option, Stock
from pytest_bdd import given, parsers, scenarios, then, when
from src.ibkr.market_data import MarketDataFetcher

# Import the scenarios from the feature file
scenarios("../features/market_data.feature")


# Shared fixtures and variables
@pytest.fixture
def mock_ib():
    """Create a mocked IB instance that appears connected."""
    with patch("ib_insync.IB") as mock:
        mock_instance = mock.return_value
        mock_instance.isConnected.return_value = True

        # Mock event handlers
        mock_instance.connectedEvent = []
        mock_instance.disconnectedEvent = []
        mock_instance.errorEvent = []

        yield mock_instance


# Store context between steps
class Context:
    """Store context between test steps."""

    def __init__(self):
        self.fetcher = None
        self.historical_data = None
        self.option_chain = None
        self.options = None
        self.option_contract = None
        self.greeks = None
        self.stock_price = 150.0  # Default stock price for tests


# Create a context for each scenario
@pytest.fixture
def context():
    """Create a new context for the scenario."""
    return Context()


@given("an active IBKR connection")
def active_connection(mock_ib):
    """Ensure we have an active IBKR connection."""
    assert mock_ib.isConnected()
    return mock_ib


@given("a MarketDataFetcher instance")
def market_data_fetcher(mock_ib, context):
    """Create a MarketDataFetcher with the mocked IB connection."""
    context.fetcher = MarketDataFetcher(mock_ib)
    return context.fetcher


@when(parsers.parse('I request {days:d} daily bars for "{symbol}"'))
def request_historical_bars(days, symbol, context):
    """Request historical bars for a symbol."""
    # Create sample bar data
    bars = []
    for i in range(days):
        # Create a simple uptrend
        close_price = 100 + i
        open_price = close_price - (
            1 if i % 3 == 0 else -1
        )  # Alternate green/red candles

        bar = MagicMock(spec=BarData)
        bar.date = f"2023-01-{(i % 30) + 1}"
        bar.open = open_price
        bar.high = max(open_price, close_price) + 1
        bar.low = min(open_price, close_price) - 1
        bar.close = close_price
        bar.volume = 1000 + i * 10

        bars.append(bar)

    # Mock the response
    context.fetcher.ib.reqHistoricalData.return_value = bars

    # Call the method
    context.historical_data = context.fetcher.get_historical_bars(symbol, days=days)


@when(parsers.parse('I request the option chain for "{symbol}"'))
def request_option_chain(symbol, context):
    """Request the option chain for a symbol."""
    # Mock chain data response
    mock_chain = MagicMock()
    mock_chain.expirations = ["20230616", "20230721", "20230915"]
    mock_chain.strikes = [140, 145, 150, 155, 160]
    mock_chain.exchange = "SMART"

    context.fetcher.ib.reqSecDefOptParams.return_value = [mock_chain]

    # Create sample ticker for the underlying
    mock_ticker = MagicMock()
    mock_ticker.last = context.stock_price
    mock_ticker.close = context.stock_price - 1
    context.fetcher.ib.reqMktData.return_value = mock_ticker

    # Call the method
    context.option_chain = context.fetcher.get_option_chain(symbol)


@when(parsers.parse('I request ATM options for "{symbol}"'))
def request_atm_options(symbol, context):
    """Request ATM options for a symbol."""
    # Mock current price
    mock_ticker = MagicMock()
    mock_ticker.last = context.stock_price
    mock_ticker.close = context.stock_price - 1
    context.fetcher.ib.reqMktData.return_value = mock_ticker

    # Mock chain data
    mock_chain = MagicMock()
    mock_chain.expirations = ["20230616", "20230721"]
    mock_chain.strikes = [140, 145, 150, 155, 160]

    context.fetcher.ib.reqSecDefOptParams.return_value = [mock_chain]

    # Call the method
    context.options = context.fetcher.get_atm_options(symbol)


@when(parsers.parse('I request OTM call options for "{symbol}" with offset {offset:d}'))
def request_otm_call_options(symbol, offset, context):
    """Request OTM call options for a symbol with a specific offset."""
    # Mock current price
    mock_ticker = MagicMock()
    mock_ticker.last = context.stock_price
    mock_ticker.close = context.stock_price - 1
    context.fetcher.ib.reqMktData.return_value = mock_ticker

    # Mock chain data
    mock_chain = MagicMock()
    mock_chain.expirations = ["20230616", "20230721"]
    mock_chain.strikes = [140, 145, 150, 155, 160]

    context.fetcher.ib.reqSecDefOptParams.return_value = [mock_chain]

    # Call the method
    context.options = context.fetcher.get_atm_options(
        symbol, call_put="CALL", otm_offset=offset
    )


@given(parsers.parse('an option contract for "{symbol}"'))
def option_contract(symbol, context, active_connection, market_data_fetcher):
    """Create an option contract for testing."""
    context.option_contract = Option(symbol, "20230616", 150, "C", "SMART")


@when("I request option Greeks")
def request_option_greeks(context):
    """Request Greeks for the option contract."""
    # Mock ticker response with Greeks
    mock_ticker = MagicMock()
    mock_ticker.impliedVol = 0.3
    mock_ticker.delta = 0.65
    mock_ticker.gamma = 0.03
    mock_ticker.vega = 0.12
    mock_ticker.theta = -0.05
    mock_ticker.last = 5.4
    mock_ticker.close = 5.3
    mock_ticker.bid = 5.2
    mock_ticker.ask = 5.5
    mock_ticker.bidSize = 10
    mock_ticker.askSize = 15
    mock_ticker.volume = 500
    mock_ticker.openInterest = 2000

    context.fetcher.ib.reqMktData.return_value = mock_ticker

    # Call the method
    context.greeks = context.fetcher.get_option_greeks(context.option_contract)


@then("a DataFrame should be returned")
def check_dataframe_returned(context):
    """Verify that a DataFrame was returned."""
    assert isinstance(context.historical_data, pd.DataFrame)
    assert not context.historical_data.empty


@then(parsers.parse("it should have columns {columns}"))
def check_dataframe_columns(columns, context):
    """Verify that the DataFrame has the expected columns."""
    # Parse the column names from the string [col1, col2, ...]
    expected_columns = columns.strip("[]").split(", ")
    for col in expected_columns:
        assert col in context.historical_data.columns


@then("the SMA50 value at index 50 should equal the mean of the first 50 close prices")
def check_sma_calculation(context):
    """Verify that the SMA50 calculation is correct."""
    if len(context.historical_data) > 50:
        expected_sma = context.historical_data["close"][:50].mean()
        actual_sma = context.historical_data.loc[49, "sma50"]
        # Allow for small floating point differences
        assert abs(expected_sma - actual_sma) < 0.001


@then("the result should contain at least one expiration date")
def check_option_chain_expirations(context):
    """Verify that the option chain has at least one expiration date."""
    assert len(context.option_chain) > 0


@then("each expiration should map to a list of Option contracts")
def check_option_chain_contracts(context):
    """Verify that each expiration date maps to a list of Option contracts."""
    for expiration, options in context.option_chain.items():
        assert isinstance(options, list)
        assert len(options) > 0
        assert all(isinstance(opt, Option) for opt in options)


@then("the options should include both calls and puts")
def check_option_chain_call_puts(context):
    """Verify that the option chain includes both calls and puts."""
    for expiration, options in context.option_chain.items():
        call_count = sum(1 for opt in options if opt.right == "C")
        put_count = sum(1 for opt in options if opt.right == "P")
        assert call_count > 0
        assert put_count > 0


@then("I should receive option contracts")
def check_options_returned(context):
    """Verify that option contracts were returned."""
    assert context.options is not None
    assert len(context.options) > 0
    assert all(isinstance(opt, Option) for opt in context.options)


@then("the strike price should be near the current price")
def check_strike_near_price(context):
    """Verify that the strike price is near the current price."""
    for option in context.options:
        # ATM should be closest to current price
        assert abs(option.strike - context.stock_price) <= 5


@then("I should receive call option contracts")
def check_call_options(context):
    """Verify that call option contracts were returned."""
    assert all(opt.right == "C" for opt in context.options)


@then("the strike price should be higher than the current price")
def check_strike_higher_than_price(context):
    """Verify that the strike price is higher than the current price (for OTM calls)."""
    for option in context.options:
        assert option.strike > context.stock_price


@then("I should receive implied volatility")
def check_implied_vol(context):
    """Verify that implied volatility was returned."""
    assert "impliedVol" in context.greeks
    assert context.greeks["impliedVol"] is not None


@then("delta, gamma, theta, and vega values")
def check_greeks(context):
    """Verify that Greek values were returned."""
    for greek in ["delta", "gamma", "theta", "vega"]:
        assert greek in context.greeks
        assert context.greeks[greek] is not None
