#!/usr/bin/env python
"""
Example script demonstrating how to use the MarketDataFetcher to retrieve
historical bars and option chain data from Interactive Brokers.

Usage:
    python fetch_market_data.py [symbol]

This script:
1. Loads config from config.yaml
2. Connects to TWS/Gateway
3. Retrieves historical data with SMA50 for the symbol
4. Retrieves the option chain for the symbol
5. Finds ATM and OTM options
6. Gets Greeks for one of the options
"""
import argparse
import logging
import os
import sys
import time

import pandas as pd

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.config import load_config
from src.ibkr.connector import IBConnector
from src.ibkr.market_data import MarketDataFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set pandas display options for better output
pd.set_option("display.max_rows", 20)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
pd.set_option("display.float_format", "{:.4f}".format)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch market data from Interactive Brokers"
    )
    parser.add_argument(
        "symbol",
        nargs="?",
        default="AAPL",
        help="Symbol to fetch data for (default: AAPL)",
    )
    return parser.parse_args()


def main():
    """Fetch market data and demonstrate usage."""
    args = parse_args()
    symbol = args.symbol

    print(f"Interactive Brokers Market Data Example - {symbol}")
    print("===================================================\n")

    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config()

        # Create connector
        print(
            f"Creating connector for {config['ibkr']['host']}:{config['ibkr']['port']}"
        )
        connector = IBConnector(
            config["ibkr"]["host"], config["ibkr"]["port"], config["ibkr"]["client_id"]
        )

        # Connect to TWS/Gateway
        print("Connecting to TWS/Gateway...")
        success = connector.connect()

        if not success:
            print("Failed to connect. Make sure TWS/Gateway is running.")
            return 1

        print("Connected to Interactive Brokers")

        # Create market data fetcher
        fetcher = MarketDataFetcher(connector.ib)

        # Get historical bars
        print(f"\nFetching 60 daily bars for {symbol}...")
        bars = fetcher.get_historical_bars(symbol, days=60)

        if bars.empty:
            print(f"No historical data available for {symbol}")
        else:
            print(f"Retrieved {len(bars)} bars")
            print("\nLast 5 bars with SMA50:")
            print(
                bars.tail()[
                    ["date", "open", "high", "low", "close", "sma50", "green_candle"]
                ]
            )

            # Count green candles in the last 10 days
            green_count = bars.tail(10)["green_candle"].sum()
            print(f"\nGreen candles in last 10 days: {green_count}")

            # Check if price is above SMA50
            if not pd.isna(bars.iloc[-1]["sma50"]):
                above_sma = bars.iloc[-1]["close"] > bars.iloc[-1]["sma50"]
                print(f"Price is {'above' if above_sma else 'below'} SMA50")

        # Get option chain
        print(f"\nFetching option chain for {symbol}...")
        chain = fetcher.get_option_chain(symbol)

        if not chain:
            print(f"No option chain available for {symbol}")
        else:
            # Count options
            total_options = sum(len(options) for options in chain.values())
            print(
                f"Retrieved option chain with {len(chain)} expirations and {total_options} total options"
            )

            # Show available expirations
            print("\nAvailable expirations:")
            for i, expiry in enumerate(sorted(chain.keys())):
                print(f"  {i+1}. {expiry}")

            # Get ATM options
            print(f"\nFinding ATM options for {symbol}...")
            atm_options = fetcher.get_atm_options(symbol)

            if not atm_options:
                print(f"No ATM options found for {symbol}")
            else:
                print("ATM Options:")
                for opt in atm_options:
                    print(
                        f"  {opt.right} {opt.strike} {opt.lastTradeDateOrContractMonth}"
                    )

                # Get OTM options
                print(f"\nFinding OTM options for {symbol} (1 strike OTM)...")
                otm_calls = fetcher.get_atm_options(
                    symbol, call_put="CALL", otm_offset=1
                )
                otm_puts = fetcher.get_atm_options(symbol, call_put="PUT", otm_offset=1)

                print("OTM Call Options:")
                for opt in otm_calls:
                    print(
                        f"  {opt.right} {opt.strike} {opt.lastTradeDateOrContractMonth}"
                    )

                print("OTM Put Options:")
                for opt in otm_puts:
                    print(
                        f"  {opt.right} {opt.strike} {opt.lastTradeDateOrContractMonth}"
                    )

                # Get Greeks for an option
                if atm_options:
                    sample_option = atm_options[0]  # Take the first option (a call)
                    print(
                        f"\nFetching Greeks for {sample_option.symbol} {sample_option.right} {sample_option.strike} {sample_option.lastTradeDateOrContractMonth}..."
                    )
                    greeks = fetcher.get_option_greeks(sample_option)

                    if greeks:
                        print("Option Greeks:")
                        print(f"  Implied Volatility: {greeks['impliedVol']:.4f}")
                        print(f"  Delta: {greeks['delta']:.4f}")
                        print(f"  Gamma: {greeks['gamma']:.4f}")
                        print(f"  Theta: {greeks['theta']:.4f}")
                        print(f"  Vega: {greeks['vega']:.4f}")
                        print(f"  Option Price: {greeks['optPrice']:.2f}")
                        print(
                            f"  Bid/Ask: {greeks['bidPrice']:.2f}/{greeks['askPrice']:.2f}"
                        )

        # Disconnect
        print("\nDisconnecting from Interactive Brokers...")
        connector.disconnect()
        print("Disconnected")

        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
