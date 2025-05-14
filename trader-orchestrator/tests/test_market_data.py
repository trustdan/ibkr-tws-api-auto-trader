"""Unit tests for the MarketDataFetcher class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from ib_insync import IB, BarData, Option, Stock
from src.ibkr.market_data import MarketDataFetcher


class TestMarketDataFetcher:
    """Test suite for MarketDataFetcher class."""

    @pytest.fixture
    def mock_ib(self):
        """Create a mocked IB instance."""
        mock = MagicMock(spec=IB)
        return mock

    @pytest.fixture
    def fetcher(self, mock_ib):
        """Create a MarketDataFetcher with a mocked IB."""
        return MarketDataFetcher(mock_ib)

    def test_init(self, fetcher, mock_ib):
        """Test initializing the fetcher."""
        assert fetcher.ib == mock_ib

    def test_get_historical_bars(self, fetcher, mock_ib):
        """Test fetching historical bars with SMA50 calculation."""
        # Create sample bar data
        bars = []
        for i in range(60):
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
        mock_ib.reqHistoricalData.return_value = bars

        # Call the method
        result = fetcher.get_historical_bars("AAPL", days=60)

        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 60
        assert "sma50" in result.columns
        assert "green_candle" in result.columns
        assert "daily_return" in result.columns
        assert "volatility_20d" in result.columns

        # Verify SMA calculation is correct
        # The SMA50 at index 49 should be the mean of closes[0:49]
        expected_sma = np.mean([100 + i for i in range(50)])
        assert abs(result.loc[49, "sma50"] - expected_sma) < 0.001

        # Verify green candle identification
        for i in range(60):
            is_green = result.loc[i, "open"] < result.loc[i, "close"]
            assert result.loc[i, "green_candle"] == is_green

    def test_get_historical_bars_empty(self, fetcher, mock_ib):
        """Test handling of empty historical data."""
        # Mock empty response
        mock_ib.reqHistoricalData.return_value = []

        # Call the method
        result = fetcher.get_historical_bars("NONEXISTENT")

        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_get_historical_bars_error(self, fetcher, mock_ib):
        """Test error handling in historical bars retrieval."""
        # Mock an exception
        mock_ib.reqHistoricalData.side_effect = Exception("Connection error")

        # Call the method
        result = fetcher.get_historical_bars("AAPL")

        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_get_option_chain(self, fetcher, mock_ib):
        """Test fetching option chain data."""
        # Mock chain data response
        mock_chain = MagicMock()
        mock_chain.expirations = ["20230616", "20230721"]
        mock_chain.strikes = [100, 110, 120, 130, 140]
        mock_chain.exchange = "SMART"

        mock_ib.reqSecDefOptParams.return_value = [mock_chain]

        # Create sample ticker for the underlying
        mock_ticker = MagicMock()
        mock_ticker.last = 120
        mock_ticker.close = 119
        mock_ib.reqMktData.return_value = mock_ticker

        # Call the method
        result = fetcher.get_option_chain("AAPL")

        # Verify the result
        assert isinstance(result, dict)
        assert "20230616" in result
        assert "20230721" in result

        # Check that we have both calls and puts for each strike
        for expiration, options in result.items():
            assert len(options) == 10  # 5 strikes * 2 (call/put)

            # Verify some option contracts
            call_strikes = set()
            put_strikes = set()

            for option in options:
                assert option.symbol == "AAPL"
                assert option.lastTradeDateOrContractMonth == expiration

                if option.right == "C":
                    call_strikes.add(option.strike)
                else:
                    put_strikes.add(option.strike)

            # Verify we have calls and puts at each strike
            assert call_strikes == put_strikes
            assert call_strikes == {100, 110, 120, 130, 140}

    def test_get_option_chain_empty(self, fetcher, mock_ib):
        """Test handling of empty option chain data."""
        # Mock empty response
        mock_ib.reqSecDefOptParams.return_value = []

        # Call the method
        result = fetcher.get_option_chain("NONEXISTENT")

        # Verify the result
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_atm_options(self, fetcher, mock_ib):
        """Test finding ATM options."""
        # Mock current price
        mock_ticker = MagicMock()
        mock_ticker.last = 120
        mock_ticker.close = 119
        mock_ib.reqMktData.return_value = mock_ticker

        # Mock chain data
        mock_chain = MagicMock()
        mock_chain.expirations = ["20230616", "20230721"]
        mock_chain.strikes = [100, 110, 120, 130, 140]

        mock_ib.reqSecDefOptParams.return_value = [mock_chain]

        # Call the method - default behavior (BOTH, ATM)
        result = fetcher.get_atm_options("AAPL", expiration="20230616")

        # Verify the result
        assert len(result) == 2  # Call and put
        assert result[0].right == "C"
        assert result[0].strike == 120  # ATM should be closest to current price
        assert result[1].right == "P"
        assert result[1].strike == 120

        # Test with OTM offset for calls only
        result = fetcher.get_atm_options(
            "AAPL", expiration="20230616", call_put="CALL", otm_offset=1
        )

        # Verify the result
        assert len(result) == 1  # Call only
        assert result[0].right == "C"
        assert result[0].strike == 130  # One strike OTM for calls = higher strike

        # Test with OTM offset for puts only
        result = fetcher.get_atm_options(
            "AAPL", expiration="20230616", call_put="PUT", otm_offset=1
        )

        # Verify the result
        assert len(result) == 1  # Put only
        assert result[0].right == "P"
        assert result[0].strike == 110  # One strike OTM for puts = lower strike

    def test_get_option_greeks(self, fetcher, mock_ib):
        """Test fetching option Greeks."""
        # Create an option contract
        option = Option("AAPL", "20230616", 120, "C", "SMART")

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

        mock_ib.reqMktData.return_value = mock_ticker

        # Call the method
        greeks = fetcher.get_option_greeks(option)

        # Verify the result
        assert greeks["impliedVol"] == 0.3
        assert greeks["delta"] == 0.65
        assert greeks["gamma"] == 0.03
        assert greeks["vega"] == 0.12
        assert greeks["theta"] == -0.05
        assert greeks["optPrice"] == 5.4
        assert greeks["bidPrice"] == 5.2
        assert greeks["askPrice"] == 5.5
        assert greeks["bidSize"] == 10
        assert greeks["askSize"] == 15
        assert greeks["volume"] == 500
        assert greeks["openInterest"] == 2000
