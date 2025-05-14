Feature: Market Data Retrieval
  As a trader
  I want to retrieve market data and option chains from IBKR
  So that I can make informed trading decisions

  Background:
    Given an active IBKR connection
    And a MarketDataFetcher instance

  Scenario: Fetch historical bars with SMA50
    When I request 52 daily bars for "AAPL"
    Then a DataFrame should be returned
    And it should have columns [open, high, low, close, sma50, green_candle]
    And the SMA50 value at index 50 should equal the mean of the first 50 close prices

  Scenario: Fetch option chain
    When I request the option chain for "MSFT"
    Then the result should contain at least one expiration date
    And each expiration should map to a list of Option contracts
    And the options should include both calls and puts

  Scenario: Find ATM options
    When I request ATM options for "GOOGL"
    Then I should receive option contracts
    And the strike price should be near the current price

  Scenario: Find OTM call options
    When I request OTM call options for "AMZN" with offset 1
    Then I should receive call option contracts
    And the strike price should be higher than the current price

  Scenario: Retrieve option Greeks
    Given an option contract for "AAPL"
    When I request option Greeks
    Then I should receive implied volatility
    And delta, gamma, theta, and vega values 