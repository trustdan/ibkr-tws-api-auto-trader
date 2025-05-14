# 04-strategy-engine.md

## 1. Overview

The Strategy Engine sits at the heart of our orchestrator: it ingests pre-processed market data (historical bars with SMA50 and candle colors) and option-chain metadata (IV, Greeks), then emits high-level trade signals. It implements the "old-school" vertical-spread rules:

* **Bullish (Call Debit):** two consecutive green candles closing above a *rising* 50-day SMA → ATM or 1-strike OTM call debit spread
* **Bearish (Put Debit):** two red candles closing below a *falling* 50-day SMA → ATM or 1-strike OTM put debit spread
* **Volatility-Driven (Credit Spreads):** if IV percentile ≥ configured threshold (e.g. pre-earnings spikes or morning IV) → call or put credit spread
* **Reward-to-Risk Enforcement:** ensure each spread's `maxProfit / maxLoss ≥ min_reward_risk`

This module encapsulates pattern detection, spread type selection, and reward-risk validation in a reusable `StrategyEngine` class.

## 2. Implementation

Create `src/strategies/engine.py`:

```python
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from src.config.loader import load_config
from src.orders.option_selector import OptionSelector
from src.ibkr.market_data import MarketDataFetcher

class StrategyEngine:
    def __init__(self, market_data: MarketDataFetcher, option_selector: OptionSelector, config_path: str = 'config.yaml'):
        self.config = load_config(config_path)['strategy']
        self.market_data = market_data
        self.selector = option_selector
        self.logger = logging.getLogger('StrategyEngine')

    def evaluate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Runs all pattern checks and returns a trade signal dict or None.
        { 'type': 'CALL_DEBIT', 'symbol': 'AAPL', 'legs': OptionSpread }
        """
        # Fetch historical bars with enough lookback for SMA calculation
        days_needed = self.config['sma_period'] + self.config['candle_count']
        df = self.market_data.get_historical_bars(symbol, days=days_needed)
        
        # Verify we have enough data
        if len(df) < days_needed:
            self.logger.warning(f"Insufficient historical data for {symbol}: {len(df)} bars < {days_needed} required")
            return None
            
        # Get the last two bars and SMA values
        last = df.iloc[-1]
        prev = df.iloc[-2]
        sma_today = last['sma50']
        sma_yesterday = prev['sma50']
        
        # Determine candle pattern
        two_green = bool(prev['green_candle'] and last['green_candle'])
        two_red = bool(not prev['green_candle'] and not last['green_candle'])

        # Determine trend
        sma_rising = sma_today > sma_yesterday
        sma_falling = sma_today < sma_yesterday
        
        # Check above/below SMA
        price_above_sma = last['close'] > sma_today
        price_below_sma = last['close'] < sma_today

        # Check IV condition
        iv_pct = self.market_data.get_iv_percentile(symbol)
        high_iv = iv_pct >= self.config['iv_threshold']

        # Log the evaluation factors
        self.logger.debug(
            f"{symbol} evaluation: two_green={two_green}, two_red={two_red}, "
            f"sma_rising={sma_rising}, sma_falling={sma_falling}, "
            f"price_above_sma={price_above_sma}, price_below_sma={price_below_sma}, "
            f"iv_pct={iv_pct:.2f}, high_iv={high_iv}"
        )

        # Bullish debit
        if two_green and sma_rising and price_above_sma and not high_iv:
            self.logger.debug(f"Bullish pattern detected on {symbol}")
            return self._build_signal(symbol, 'CALL_DEBIT')
            
        # Bearish debit
        if two_red and sma_falling and price_below_sma and not high_iv:
            self.logger.debug(f"Bearish pattern detected on {symbol}")
            return self._build_signal(symbol, 'PUT_DEBIT')
            
        # Volatility credit spreads
        if high_iv:
            # Use market bias to determine direction of credit spread
            spread_type = 'CALL_CREDIT' if sma_falling else 'PUT_CREDIT'
            self.logger.debug(f"High IV {iv_pct:.2f} on {symbol}, generating {spread_type}")
            return self._build_signal(symbol, spread_type)
            
        self.logger.debug(f"No signal generated for {symbol}")
        return None

    def _build_signal(self, symbol: str, signal_type: str) -> Optional[Dict[str, Any]]:
        """
        Builds a trade signal with specific spread details.
        """
        # Extract direction from signal type (CALL or PUT)
        direction = signal_type.split('_')[0]
        
        # Get current price for the symbol
        current_price = self.market_data.get_last_price(symbol)
        
        # Use OptionSelector to pick an optimal spread
        spread = self.selector.select_vertical_spread(
            symbol=symbol,
            direction=direction,
            spread_type=signal_type.split('_')[1],  # DEBIT or CREDIT
            current_price=current_price
        )
        
        if spread is None:
            self.logger.warning(f"No valid spread found for {signal_type} on {symbol}")
            return None
            
        # Enforce reward/risk
        if spread.reward_risk_ratio < self.config['min_reward_risk']:
            self.logger.info(
                f"Discarded {symbol} {signal_type} spread: R:R {spread.reward_risk_ratio:.2f} < "
                f"{self.config['min_reward_risk']}"
            )
            return None
            
        return {
            'type': signal_type,
            'symbol': symbol,
            'spread': spread,
            'current_price': current_price,
            'timestamp': pd.Timestamp.now()
        }
        
    def scan_symbols(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Batch process a list of symbols and return all valid signals.
        """
        signals = []
        for symbol in symbols:
            try:
                signal = self.evaluate(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                self.logger.error(f"Error evaluating {symbol}: {str(e)}")
        
        self.logger.info(f"Scan complete: {len(signals)} signals from {len(symbols)} symbols")
        return signals
```

## 3. Testing & Validation

### Unit Tests

Create `tests/strategies/test_engine.py`:

```python
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.strategies.engine import StrategyEngine

@pytest.fixture
def mock_market_data():
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_option_selector():
    mock = MagicMock()
    mock.select_vertical_spread.return_value = MagicMock(reward_risk_ratio=1.5)
    return mock

@pytest.fixture
def strategy_engine(mock_market_data, mock_option_selector):
    with patch('src.config.loader.load_config') as mock_load:
        mock_load.return_value = {
            'strategy': {
                'sma_period': 50,
                'candle_count': 2,
                'iv_threshold': 0.8,
                'min_reward_risk': 1.0
            }
        }
        return StrategyEngine(mock_market_data, mock_option_selector)

def create_test_df(green_candles, sma_values, closes):
    """Helper to create test dataframes with specific patterns"""
    df = pd.DataFrame({
        'open': np.ones(len(green_candles) + 1),
        'high': np.ones(len(green_candles) + 1) * 1.1,
        'low': np.ones(len(green_candles) + 1) * 0.9,
        'close': closes,
        'green_candle': green_candles,
        'sma50': sma_values
    })
    return df

def test_bullish_pattern(strategy_engine, mock_market_data):
    """Test bullish pattern detection"""
    # Mock historical data: two green candles, rising SMA, price above SMA
    green_candles = [True, True]
    sma_values = [100.0, 101.0]
    closes = [102.0, 103.0]
    
    mock_market_data.get_historical_bars.return_value = create_test_df(
        green_candles, sma_values, closes
    )
    mock_market_data.get_iv_percentile.return_value = 0.5  # Below threshold
    mock_market_data.get_last_price.return_value = 103.0
    
    # Execute and verify
    signal = strategy_engine.evaluate("AAPL")
    assert signal is not None
    assert signal['type'] == 'CALL_DEBIT'
    assert signal['symbol'] == 'AAPL'

def test_bearish_pattern(strategy_engine, mock_market_data):
    """Test bearish pattern detection"""
    # Mock historical data: two red candles, falling SMA, price below SMA
    green_candles = [False, False]
    sma_values = [100.0, 99.0]
    closes = [98.0, 97.0]
    
    mock_market_data.get_historical_bars.return_value = create_test_df(
        green_candles, sma_values, closes
    )
    mock_market_data.get_iv_percentile.return_value = 0.5  # Below threshold
    mock_market_data.get_last_price.return_value = 97.0
    
    # Execute and verify
    signal = strategy_engine.evaluate("MSFT")
    assert signal is not None
    assert signal['type'] == 'PUT_DEBIT'
    assert signal['symbol'] == 'MSFT'

def test_high_iv_pattern(strategy_engine, mock_market_data):
    """Test high IV pattern detection"""
    # Mock historical data: mixed pattern, high IV
    green_candles = [True, False]
    sma_values = [100.0, 99.0]
    closes = [98.0, 97.0]
    
    mock_market_data.get_historical_bars.return_value = create_test_df(
        green_candles, sma_values, closes
    )
    mock_market_data.get_iv_percentile.return_value = 0.9  # Above threshold
    mock_market_data.get_last_price.return_value = 97.0
    
    # Execute and verify
    signal = strategy_engine.evaluate("GOOG")
    assert signal is not None
    assert signal['type'] == 'CALL_CREDIT'  # Since SMA is falling
    assert signal['symbol'] == 'GOOG'

def test_reward_risk_below_threshold(strategy_engine, mock_market_data, mock_option_selector):
    """Test that spreads below min_reward_risk are discarded"""
    # Setup a valid bullish pattern
    green_candles = [True, True]
    sma_values = [100.0, 101.0]
    closes = [102.0, 103.0]
    
    mock_market_data.get_historical_bars.return_value = create_test_df(
        green_candles, sma_values, closes
    )
    mock_market_data.get_iv_percentile.return_value = 0.5
    mock_market_data.get_last_price.return_value = 103.0
    
    # But make the reward_risk_ratio below threshold
    mock_option_selector.select_vertical_spread.return_value = MagicMock(reward_risk_ratio=0.8)
    
    # Execute and verify no signal is generated
    signal = strategy_engine.evaluate("AMD")
    assert signal is None
```

### Integration Tests

Create `tests/integration/test_strategy_integration.py`:

```python
import pytest
from ib_insync import IB
from src.ibkr.connector import IBConnector
from src.ibkr.market_data import MarketDataFetcher
from src.orders.option_selector import OptionSelector
from src.strategies.engine import StrategyEngine
from src.config.loader import load_config

@pytest.mark.integration
def test_strategy_integration_with_paper_tws():
    """Integration test with paper TWS - requires running TWS instance"""
    # Load real config
    config = load_config('config.yaml')
    
    # Create real components
    ib_connector = IBConnector()
    ib = ib_connector.connect(
        host=config['ibkr']['host'],
        port=config['ibkr']['port'],
        client_id=config['ibkr']['client_id']
    )
    
    market_data = MarketDataFetcher(ib)
    option_selector = OptionSelector(ib, market_data)
    strategy = StrategyEngine(market_data, option_selector)
    
    # Test with a known liquid symbol
    symbol = "AAPL"
    signal = strategy.evaluate(symbol)
    
    # We don't know what the signal will be (could be none),
    # but the process should complete without errors
    if signal:
        print(f"Signal generated: {signal['type']} for {symbol}")
    else:
        print(f"No signal generated for {symbol}")
    
    # Clean up
    ib_connector.disconnect()
```

## 4. Cucumber Scenarios

Create `tests/bdd/features/strategy_engine.feature`:

```gherkin
Feature: Strategy Engine Signals
  Background:
    Given a loaded config with sma_period=50, candle_count=2, iv_threshold=0.8, min_reward_risk=1.0
    And a mock MarketDataFetcher and OptionSelector

  Scenario: Bullish call debit when two green above rising SMA
    Given historical bars for "AAPL" with two green candles and sma50 rising
    And iv_percentile=0.5
    When strategy.evaluate("AAPL")
    Then result.type == "CALL_DEBIT"

  Scenario: Bearish put debit when two red below falling SMA
    Given historical bars for "MSFT" with two red candles and sma50 falling
    And iv_percentile=0.3
    When strategy.evaluate("MSFT")
    Then result.type == "PUT_DEBIT"

  Scenario: Call credit on high IV with falling SMA
    Given historical bars for "GOOG" with mixed candles and sma50 falling
    And iv_percentile=0.9
    When strategy.evaluate("GOOG")
    Then result.type == "CALL_CREDIT"

  Scenario: Put credit on high IV with rising SMA
    Given historical bars for "AMZN" with mixed candles and sma50 rising
    And iv_percentile=0.85
    When strategy.evaluate("AMZN")
    Then result.type == "PUT_CREDIT"

  Scenario: Discard spread below min reward/risk
    Given a valid CALL_DEBIT pattern for "NVDA"
    And OptionSelector returns a spread with reward_risk_ratio=0.8
    When strategy.evaluate("NVDA")
    Then result is None
```

Create `tests/bdd/steps/strategy_steps.py`:

```python
import pandas as pd
import numpy as np
from pytest_bdd import given, when, then, parsers
from unittest.mock import MagicMock, patch

@given(parsers.parse('a loaded config with sma_period={sma}, candle_count={candles}, iv_threshold={iv}, min_reward_risk={rr}'))
def config_loaded(sma, candles, iv, rr):
    config = {
        'strategy': {
            'sma_period': int(sma),
            'candle_count': int(candles),
            'iv_threshold': float(iv),
            'min_reward_risk': float(rr)
        }
    }
    return config

@given('a mock MarketDataFetcher and OptionSelector')
def mock_dependencies():
    market_data = MagicMock()
    option_selector = MagicMock()
    option_selector.select_vertical_spread.return_value = MagicMock(reward_risk_ratio=1.5)
    return {
        'market_data': market_data,
        'option_selector': option_selector
    }

@given(parsers.parse('historical bars for "{symbol}" with two green candles and sma50 rising'))
def bullish_bars(mock_dependencies, symbol):
    df = pd.DataFrame({
        'open': [100, 101],
        'high': [105, 106],
        'low': [99, 100],
        'close': [103, 104],
        'green_candle': [True, True],
        'sma50': [100, 101]
    })
    mock_dependencies['market_data'].get_historical_bars.return_value = df
    mock_dependencies['market_data'].get_last_price.return_value = 104.0
    mock_dependencies['symbol'] = symbol

@given(parsers.parse('historical bars for "{symbol}" with two red candles and sma50 falling'))
def bearish_bars(mock_dependencies, symbol):
    df = pd.DataFrame({
        'open': [100, 99],
        'high': [101, 100],
        'low': [97, 96],
        'close': [98, 97],
        'green_candle': [False, False],
        'sma50': [100, 99]
    })
    mock_dependencies['market_data'].get_historical_bars.return_value = df
    mock_dependencies['market_data'].get_last_price.return_value = 97.0
    mock_dependencies['symbol'] = symbol

@given(parsers.parse('historical bars for "{symbol}" with mixed candles and sma50 falling'))
def mixed_bars_falling_sma(mock_dependencies, symbol):
    df = pd.DataFrame({
        'open': [100, 99],
        'high': [101, 100],
        'low': [97, 96],
        'close': [98, 97],
        'green_candle': [True, False],
        'sma50': [100, 99]
    })
    mock_dependencies['market_data'].get_historical_bars.return_value = df
    mock_dependencies['market_data'].get_last_price.return_value = 97.0
    mock_dependencies['symbol'] = symbol

@given(parsers.parse('historical bars for "{symbol}" with mixed candles and sma50 rising'))
def mixed_bars_rising_sma(mock_dependencies, symbol):
    df = pd.DataFrame({
        'open': [99, 100],
        'high': [100, 101],
        'low': [96, 97],
        'close': [97, 98],
        'green_candle': [False, True],
        'sma50': [95, 96]
    })
    mock_dependencies['market_data'].get_historical_bars.return_value = df
    mock_dependencies['market_data'].get_last_price.return_value = 98.0
    mock_dependencies['symbol'] = symbol

@given(parsers.parse('iv_percentile={iv}'))
def set_iv_percentile(mock_dependencies, iv):
    mock_dependencies['market_data'].get_iv_percentile.return_value = float(iv)

@given(parsers.parse('a valid CALL_DEBIT pattern for "{symbol}"'))
def valid_call_debit_pattern(mock_dependencies, symbol):
    df = pd.DataFrame({
        'open': [100, 101],
        'high': [105, 106],
        'low': [99, 100],
        'close': [103, 104],
        'green_candle': [True, True],
        'sma50': [100, 101]
    })
    mock_dependencies['market_data'].get_historical_bars.return_value = df
    mock_dependencies['market_data'].get_iv_percentile.return_value = 0.5
    mock_dependencies['market_data'].get_last_price.return_value = 104.0
    mock_dependencies['symbol'] = symbol

@given(parsers.parse('OptionSelector returns a spread with reward_risk_ratio={rr}'))
def set_reward_risk_ratio(mock_dependencies, rr):
    mock_dependencies['option_selector'].select_vertical_spread.return_value = MagicMock(reward_risk_ratio=float(rr))

@when(parsers.parse('strategy.evaluate("{symbol}")'))
def evaluate_strategy(mock_dependencies, config_loaded, symbol, monkeypatch):
    with patch('src.config.loader.load_config', return_value=config_loaded):
        from src.strategies.engine import StrategyEngine
        strategy = StrategyEngine(
            mock_dependencies['market_data'],
            mock_dependencies['option_selector']
        )
        mock_dependencies['result'] = strategy.evaluate(symbol)

@then(parsers.parse('result.type == "{expected_type}"'))
def check_result_type(mock_dependencies, expected_type):
    assert mock_dependencies['result'] is not None
    assert mock_dependencies['result']['type'] == expected_type

@then('result is None')
def check_result_none(mock_dependencies):
    assert mock_dependencies['result'] is None
```

## 5. Pseudocode Outline

```python
# Example usage in app/main.py
from src.ibkr.connector import IBConnector
from src.ibkr.market_data import MarketDataFetcher
from src.orders.option_selector import OptionSelector
from src.strategies.engine import StrategyEngine

# Initialize components
ib_connector = IBConnector()
ib = ib_connector.connect(host='localhost', port=7497, client_id=1)

market_data = MarketDataFetcher(ib)
option_selector = OptionSelector(ib, market_data)
strategy_engine = StrategyEngine(market_data, option_selector)

# Evaluate a specific symbol
symbol = 'NFLX'
signal = strategy_engine.evaluate(symbol)

if signal:
    print(f"Signal: {signal['type']} for {signal['symbol']}")
    print(f"Spread: {signal['spread']}")
    print(f"Current price: {signal['current_price']}")
    print(f"Timestamp: {signal['timestamp']}")
else:
    print(f"No trade signal for {symbol}")

# Process a watchlist
watchlist = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA']
signals = strategy_engine.scan_symbols(watchlist)
print(f"Generated {len(signals)} signals from {len(watchlist)} symbols")
```
