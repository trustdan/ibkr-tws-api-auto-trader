# 03-market-data-and-chains.md

## 1. Overview

In this module, we implement market data retrieval both for historical price bars (to feed our technical indicators like SMA50 and two-candle patterns) and for live option chain data (to determine ATM vs. OTM strikes and implied volatility).  Using `ib_insync`, we encapsulate:

* **Historical Bars**: `reqHistoricalData` to fetch the past 52 daily bars for each symbol.  We convert the response into a Pandas DataFrame and compute rolling metrics (SMA, candle colors).
* **Option Chains**: `reqSecDefOptParams` to fetch available expirations and strike increments; followed by `reqContractDetails` to retrieve per-expiration option contracts, including Greeks and implied vol (`Ticker.greeks`).

By centralizing both data sources in a `MarketDataFetcher` class, downstream strategy and scanning modules can request consistent, pre-processed data.

## 2. Implementation

Create `src/ibkr/market_data.py`:

```python
from ib_insync import IB, Stock, util, Option
import pandas as pd

class MarketDataFetcher:
    def __init__(self, ib: IB):
        self.ib = ib

    def get_historical_bars(self, symbol: str, days: int = 52) -> pd.DataFrame:
        """
        Fetch the last `days` daily bars for `symbol` and compute SMA50 and candle colors.
        """
        contract = Stock(symbol, 'SMART', 'USD')
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=f'{days} D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True
        )
        df = util.df(bars)
        df['sma50'] = df['close'].rolling(window=50).mean()
        df['green_candle'] = df['close'] > df['open']
        return df

    def get_option_chain(self, symbol: str) -> dict:
        """
        Retrieve available expirations and option contracts for `symbol`, returning a dict:
            {
              expiration_str: [Option, Option, ...],
              ...
            }
        """
        # Step 1: retrieve chain parameters
        chains = self.ib.reqSecDefOptParams(symbol, '', 'STK', 0)
        option_chains = {}
        for chain in chains:
            for expiry in chain.expirations:
                strikes = chain.strikes
                opts = []
                for strike in strikes:
                    opt_call = Option(symbol, expiry, strike, 'C', chain.exchange)
                    opt_put = Option(symbol, expiry, strike, 'P', chain.exchange)
                    opts.extend([opt_call, opt_put])
                option_chains[expiry] = opts
        return option_chains
```

## 3. Testing & Validation

* **Unit tests**: monkeypatch `IB.reqHistoricalData` and `IB.reqSecDefOptParams` to return sample data; assert DataFrame columns and chain keys.
* **Integration test**: against a paper-TWS instance, fetch real bars for a liquid symbol (e.g., AAPL) and ensure non-empty results.

## 4. Cucumber Scenarios

```gherkin
Feature: Market Data Retrieval
  Scenario: Fetch historical bars with SMA50
    Given the IBKR connection is established
    When I request 52 daily bars for "AAPL"
    Then the returned DataFrame has columns [open, high, low, close, sma50, green_candle]
    And the SMA50 value at index 50 equals the mean of the first 50 closes

  Scenario: Fetch option chain
    Given the IBKR connection is established
    When I request the option chain for "MSFT"
    Then the result contains at least one expiration key
    And each expiration maps to a list of Option contracts
```

## 5. Pseudocode Outline

```python
# Usage example
fetcher = MarketDataFetcher(ib)
df = fetcher.get_historical_bars('GOOGL', days=52)
assert 'sma50' in df.columns

chains = fetcher.get_option_chain('GOOGL')
first_exp = list(chains.keys())[0]
assert isinstance(chains[first_exp][0], Option)
```
