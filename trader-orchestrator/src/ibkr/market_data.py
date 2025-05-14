"""
Market data retrieval from Interactive Brokers.
Provides historical bars and option chain data.
"""
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from ib_insync import IB, Stock, Option, Contract, util, BarData

# Configure logger
logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """
    Retrieves and processes market data from Interactive Brokers.
    
    Features:
    - Historical price bars with technical indicators (SMA50, candle colors)
    - Option chain data including expirations, strikes, and Greeks
    - Support for custom bar sizes and lookback periods
    """
    
    def __init__(self, ib: IB):
        """
        Initialize the market data fetcher.
        
        Args:
            ib: An active ib_insync.IB instance that is already connected
        """
        self.ib = ib
        
    def get_historical_bars(self, symbol: str, days: int = 52, 
                           bar_size: str = '1 day', what_to_show: str = 'TRADES', 
                           use_rth: bool = True) -> pd.DataFrame:
        """
        Fetch historical bars for a symbol and compute technical indicators.
        
        Args:
            symbol: The ticker symbol
            days: Number of days of history to retrieve
            bar_size: Bar size (e.g., '1 day', '1 hour', '5 mins')
            what_to_show: Type of data ('TRADES', 'MIDPOINT', etc.)
            use_rth: Whether to use regular trading hours only
            
        Returns:
            DataFrame with price data and technical indicators
        """
        logger.info(f"Fetching {days} {bar_size} bars for {symbol}")
        
        # Create a stock contract
        contract = Stock(symbol, 'SMART', 'USD')
        
        try:
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',  # '' means now
                durationStr=f'{days} D',
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=1
            )
            
            if not bars:
                logger.warning(f"No historical data returned for {symbol}")
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = util.df(bars)
            
            # Add technical indicators
            if len(df) > 0:
                # SMA50 calculation (will be NaN for first 49 rows)
                df['sma50'] = df['close'].rolling(window=50).mean()
                
                # Identify green/red candles (close > open = green)
                df['green_candle'] = df['close'] > df['open']
                
                # Calculate daily returns
                df['daily_return'] = df['close'].pct_change()
                
                # Calculate volatility (20-day rolling standard deviation of returns)
                df['volatility_20d'] = df['daily_return'].rolling(window=20).std()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_option_chain(self, symbol: str, exchange: str = 'SMART') -> Dict[str, List[Option]]:
        """
        Retrieve the complete option chain for a symbol.
        
        Args:
            symbol: The underlying ticker symbol
            exchange: The exchange to use
            
        Returns:
            Dictionary mapping expiration dates to lists of Option contracts
        """
        logger.info(f"Fetching option chain for {symbol}")
        
        try:
            # Create a stock contract for the underlying
            underlying = Stock(symbol, exchange, 'USD')
            
            # Step 1: Get valid strikes and expirations
            chains = self.ib.reqSecDefOptParams(
                underlyingSymbol=symbol,
                futFopExchange='',
                underlyingSecType='STK',
                underlyingConId=0
            )
            
            if not chains:
                logger.warning(f"No option chain data returned for {symbol}")
                return {}
                
            # Group contracts by expiration
            option_chains = {}
            
            # Get the first chains result (usually the primary exchange)
            chain = chains[0]
            
            # Step 2: Create option contracts for each expiration/strike
            for expiration in chain.expirations:
                logger.debug(f"Processing expiration {expiration} for {symbol}")
                
                # Determine which strikes to include
                # We use the full strike range from the chain data
                strikes = chain.strikes
                
                # Limit number of strikes to avoid overloading
                if len(strikes) > 20:
                    # Get ATM price to center our strikes
                    # Skip this if we can't get a current price
                    try:
                        ticker = self.ib.reqMktData(underlying)
                        self.ib.sleep(0.5)  # Wait for market data
                        last_price = ticker.last if hasattr(ticker, 'last') and ticker.last else ticker.close
                        self.ib.cancelMktData(underlying)
                        
                        if last_price:
                            # Find closest strikes to current price
                            strikes = sorted(strikes, key=lambda x: abs(x - last_price))
                            strikes = strikes[:20]  # Take 20 closest strikes
                    except Exception as e:
                        logger.warning(f"Could not get current price for {symbol}: {str(e)}")
                        # Take strikes around the middle of the range
                        if len(strikes) > 20:
                            strikes = sorted(strikes)
                            middle = len(strikes) // 2
                            strikes = strikes[middle-10:middle+10]
                
                # Create option contracts
                options = []
                for strike in sorted(strikes):
                    # Create call and put options
                    call = Option(symbol, expiration, strike, 'C', exchange)
                    put = Option(symbol, expiration, strike, 'P', exchange)
                    options.extend([call, put])
                
                option_chains[expiration] = options
            
            return option_chains
            
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {str(e)}")
            return {}
    
    def get_atm_options(self, symbol: str, expiration: Optional[str] = None,
                        call_put: str = 'BOTH', exchange: str = 'SMART',
                        otm_offset: int = 0) -> List[Option]:
        """
        Get at-the-money (ATM) options for a symbol, with optional OTM offset.
        
        Args:
            symbol: The underlying ticker symbol
            expiration: Specific expiration date (if None, picks closest standard monthly)
            call_put: 'CALL', 'PUT', or 'BOTH'
            exchange: The exchange to use
            otm_offset: Number of strikes OTM to offset (0 = ATM, 1 = one strike OTM)
            
        Returns:
            List of Option contracts (calls, puts, or both)
        """
        logger.info(f"Finding ATM options for {symbol}")
        
        try:
            # Get underlying price
            underlying = Stock(symbol, exchange, 'USD')
            ticker = self.ib.reqMktData(underlying)
            self.ib.sleep(0.5)  # Wait for market data to arrive
            
            # Use last price, or close if last not available
            last_price = ticker.last if hasattr(ticker, 'last') and ticker.last else ticker.close
            self.ib.cancelMktData(underlying)
            
            if not last_price:
                logger.warning(f"Could not determine current price for {symbol}")
                return []
                
            logger.debug(f"Current price for {symbol}: {last_price}")
            
            # Get option chain parameters
            chains = self.ib.reqSecDefOptParams(
                underlyingSymbol=symbol,
                futFopExchange='',
                underlyingSecType='STK',
                underlyingConId=0
            )
            
            if not chains:
                logger.warning(f"No option chain data returned for {symbol}")
                return []
                
            chain = chains[0]
            
            # Determine expiration date
            if not expiration:
                # Get available expirations
                expirations = sorted(chain.expirations)
                
                if not expirations:
                    logger.warning(f"No expirations available for {symbol}")
                    return []
                    
                # Choose the closest expiration date at least 30 days out
                today = datetime.now().date()
                valid_exps = []
                
                for exp in expirations:
                    exp_date = datetime.strptime(exp, '%Y%m%d').date()
                    days_to_exp = (exp_date - today).days
                    if days_to_exp >= 30:
                        valid_exps.append((exp, days_to_exp))
                
                if not valid_exps:
                    # Just take the furthest expiration
                    expiration = expirations[-1]
                else:
                    # Sort by days to expiration
                    valid_exps.sort(key=lambda x: x[1])
                    expiration = valid_exps[0][0]
                
                logger.debug(f"Selected expiration {expiration} for {symbol}")
            
            # Find the strike closest to the current price
            strikes = sorted(chain.strikes)
            if not strikes:
                logger.warning(f"No strikes available for {symbol}")
                return []
                
            # Find closest strike to current price
            atm_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - last_price))
            
            # Apply OTM offset
            if otm_offset > 0:
                if call_put == 'CALL' or call_put == 'BOTH':
                    call_idx = min(atm_idx + otm_offset, len(strikes) - 1)
                else:
                    call_idx = atm_idx
                    
                if call_put == 'PUT' or call_put == 'BOTH':
                    put_idx = max(atm_idx - otm_offset, 0)
                else:
                    put_idx = atm_idx
            else:
                call_idx = put_idx = atm_idx
            
            # Create option contracts
            result = []
            if call_put == 'CALL' or call_put == 'BOTH':
                call = Option(symbol, expiration, strikes[call_idx], 'C', exchange)
                result.append(call)
                
            if call_put == 'PUT' or call_put == 'BOTH':
                put = Option(symbol, expiration, strikes[put_idx], 'P', exchange)
                result.append(put)
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding ATM options for {symbol}: {str(e)}")
            return []
            
    def get_option_greeks(self, option: Option) -> dict:
        """
        Get Greeks and implied volatility for an option contract.
        
        Args:
            option: The Option contract
            
        Returns:
            Dictionary with Greek values and other option metrics
        """
        logger.info(f"Fetching Greeks for {option.symbol} {option.right} {option.strike} {option.lastTradeDateOrContractMonth}")
        
        try:
            # Request market data for full option details
            option_ticker = self.ib.reqMktData(option, '', False, False)
            self.ib.sleep(1)  # Wait for market data
            
            # Extract Greeks
            greeks = {
                'impliedVol': option_ticker.impliedVol,
                'delta': option_ticker.delta,
                'gamma': option_ticker.gamma,
                'vega': option_ticker.vega,
                'theta': option_ticker.theta,
                'optPrice': option_ticker.last if option_ticker.last else option_ticker.close,
                'bidPrice': option_ticker.bid,
                'askPrice': option_ticker.ask,
                'bidSize': option_ticker.bidSize,
                'askSize': option_ticker.askSize,
                'volume': option_ticker.volume,
                'openInterest': option_ticker.openInterest
            }
            
            # Cancel market data subscription
            self.ib.cancelMktData(option)
            
            return greeks
            
        except Exception as e:
            logger.error(f"Error fetching Greeks for {option.symbol}: {str(e)}")
            return {} 