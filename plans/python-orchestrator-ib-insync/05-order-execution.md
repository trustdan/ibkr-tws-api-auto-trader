# 05-order-execution.md

## 1. Overview

This module implements order placement, monitoring, and management for vertical option spreads via `ib_insync`.  It uses our `OptionSpread` model (long/short legs with strike, expiration, cost, P/L) and submits them either as a single combo order (if supported) or as two linked leg orders.  Key requirements:

* **Atomicity:** Both legs (buy/sell) should execute or gracefully roll back
* **Tracking:** Maintain order status, fills, and commissions
* **Environment modes:** Market orders for paper trading; limit orders with price-improvement for live
* **Cancellation & modification:** Ability to cancel or adjust orders before fill

## 2. Implementation

### 2.1 Option Spread Model

First, let's define our `OptionSpread` model in `src/models/option.py`:

```python
from dataclasses import dataclass
from typing import Optional, Literal
from ib_insync import Option

@dataclass
class OptionSpread:
    """Model for a two-legged vertical option spread"""
    symbol: str
    expiration: str  # Format: YYYYMMDD
    long_strike: float
    short_strike: float
    option_type: Literal['C', 'P']  # C for Call, P for Put
    spread_type: Literal['CALL_DEBIT', 'CALL_CREDIT', 'PUT_DEBIT', 'PUT_CREDIT']
    
    # Pricing data
    cost: Optional[float] = None
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    
    # Contract details
    long_leg: Optional[Option] = None
    short_leg: Optional[Option] = None
    
    @property
    def reward_risk_ratio(self) -> float:
        """Calculate reward to risk ratio"""
        if not self.max_profit or not self.max_loss or self.max_loss == 0:
            return 0
        return self.max_profit / self.max_loss
    
    @property
    def width(self) -> float:
        """Calculate the spread width in points"""
        return abs(self.short_strike - self.long_strike)
```

### 2.2 Order Executor Class

Now, let's implement the `OrderExecutor` in `src/orders/executor.py`:

```python
from ib_insync import IB, ComboLeg, Contract, Order, Trade, OrderStatus
from src.models.option import OptionSpread
import logging
from typing import Dict, List, Optional, Callable
import time
import uuid

class OrderExecutor:
    def __init__(self, ib: IB, paper: bool = True):
        self.ib = ib
        self.paper = paper
        self.logger = logging.getLogger('OrderExecutor')
        self.active_trades: Dict[str, Trade] = {}
        self.trade_callbacks: Dict[str, List[Callable]] = {}
        
        # Register for order status updates
        self.ib.orderStatusEvent += self._handle_order_status
        self.ib.execDetailsEvent += self._handle_execution_details

    def send_vertical_spread(self, spread: OptionSpread, quantity: int = 1) -> Optional[Trade]:
        """
        Places a vertical spread as a combo order.
        Returns a Trade object tracking both legs.
        """
        if not self.ib.isConnected():
            self.logger.error("Cannot place order: IB not connected")
            return None
            
        try:
            # Build combo contract
            combo = Contract()
            combo.symbol = spread.symbol
            combo.secType = 'BAG'
            combo.currency = 'USD'
            combo.exchange = 'SMART'
            
            # Determine actions based on spread type
            if spread.spread_type == 'CALL_DEBIT' or spread.spread_type == 'PUT_DEBIT':
                long_action = 'BUY'
                short_action = 'SELL'
            else:  # Credit spreads
                long_action = 'SELL'
                short_action = 'BUY'
                
            # Ensure we have contract IDs
            if not spread.long_leg or not spread.short_leg:
                self.logger.error("Spread legs not properly initialized with contract details")
                return None
                
            # Create combo legs
            long_leg = ComboLeg(
                conId=spread.long_leg.conId,
                ratio=1,
                action=long_action,
                exchange='SMART',
                openClose=0  # Open position
            )
            
            short_leg = ComboLeg(
                conId=spread.short_leg.conId,
                ratio=1,
                action=short_action,
                exchange='SMART',
                openClose=0  # Open position
            )
            
            combo.comboLegs = [long_leg, short_leg]
            
            # Choose order type based on environment
            if self.paper:
                order = Order(
                    orderType='MKT',
                    totalQuantity=quantity,
                    transmit=True,
                    orderId=self.ib.client.getReqId(),
                    account=self.ib.wrapper.accounts[0]
                )
            else:
                # Calculate midpoint price with small improvement
                if spread.spread_type.endswith('DEBIT'):
                    # For debit spreads, we want to pay less if possible
                    limit_price = (spread.long_leg.ask + spread.short_leg.bid) / 2
                    # Small improvement (pay a bit less)
                    limit_price = round(limit_price * 0.99, 2)
                else:
                    # For credit spreads, we want to receive more if possible
                    limit_price = (spread.long_leg.bid + spread.short_leg.ask) / 2
                    # Small improvement (receive a bit more)
                    limit_price = round(limit_price * 1.01, 2)
                
                order = Order(
                    orderType='LMT',
                    lmtPrice=limit_price,
                    totalQuantity=quantity,
                    transmit=True,
                    orderId=self.ib.client.getReqId(),
                    account=self.ib.wrapper.accounts[0],
                    tif='DAY'  # Time-in-force: day order
                )
            
            # Generate a unique ID for this trade
            trade_id = str(uuid.uuid4())
            
            # Place the order
            trade = self.ib.placeOrder(combo, order)
            
            # Store the trade for tracking
            self.active_trades[trade_id] = trade
            
            self.logger.info(
                f"Placed {quantity} {spread.spread_type} combo order for {spread.symbol} "
                f"{spread.option_type} {spread.expiration} {spread.long_strike}/{spread.short_strike}"
            )
            
            return trade
            
        except Exception as e:
            self.logger.error(f"Error placing vertical spread order: {str(e)}")
            return None

    def send_vertical_spread_as_legs(self, spread: OptionSpread, quantity: int = 1) -> Dict[str, Trade]:
        """
        Alternative implementation: Place spread as two separate orders with OCO linking.
        Useful when the exchange doesn't support combos directly.
        """
        if not self.ib.isConnected():
            self.logger.error("Cannot place order: IB not connected")
            return {}
            
        trades = {}
        
        try:
            # Determine actions and contracts based on spread type
            if spread.spread_type.endswith('DEBIT'):
                long_action = 'BUY'
                short_action = 'SELL'
            else:
                long_action = 'SELL'
                short_action = 'BUY'
            
            # Create orders for each leg
            if self.paper:
                long_order = Order(
                    orderType='MKT',
                    action=long_action,
                    totalQuantity=quantity,
                    transmit=True,
                    orderId=self.ib.client.getReqId(),
                    account=self.ib.wrapper.accounts[0]
                )
                
                short_order = Order(
                    orderType='MKT',
                    action=short_action,
                    totalQuantity=quantity,
                    transmit=True,
                    orderId=self.ib.client.getReqId(),
                    account=self.ib.wrapper.accounts[0]
                )
            else:
                # Use limit orders for live trading
                long_price = spread.long_leg.ask if long_action == 'BUY' else spread.long_leg.bid
                short_price = spread.short_leg.bid if short_action == 'SELL' else spread.short_leg.ask
                
                # Apply small price improvements
                if long_action == 'BUY':
                    long_price = round(long_price * 0.99, 2)  # Pay less when buying
                else:
                    long_price = round(long_price * 1.01, 2)  # Receive more when selling
                    
                if short_action == 'SELL':
                    short_price = round(short_price * 1.01, 2)  # Receive more when selling
                else:
                    short_price = round(short_price * 0.99, 2)  # Pay less when buying
                
                long_order = Order(
                    orderType='LMT',
                    action=long_action,
                    lmtPrice=long_price,
                    totalQuantity=quantity,
                    transmit=False,  # Don't transmit until both legs are submitted
                    orderId=self.ib.client.getReqId(),
                    account=self.ib.wrapper.accounts[0],
                    tif='DAY'
                )
                
                short_order = Order(
                    orderType='LMT',
                    action=short_action,
                    lmtPrice=short_price,
                    totalQuantity=quantity,
                    transmit=True,  # This will transmit both orders
                    orderId=self.ib.client.getReqId(),
                    account=self.ib.wrapper.accounts[0],
                    tif='DAY'
                )
            
            # Place the orders
            long_trade = self.ib.placeOrder(spread.long_leg, long_order)
            trades['long'] = long_trade
            
            short_trade = self.ib.placeOrder(spread.short_leg, short_order)
            trades['short'] = short_trade
            
            self.logger.info(
                f"Placed {quantity} {spread.spread_type} as two separate orders for {spread.symbol} "
                f"{spread.option_type} {spread.expiration} {spread.long_strike}/{spread.short_strike}"
            )
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Error placing spread as separate legs: {str(e)}")
            
            # Try to cancel any orders that went through
            for trade in trades.values():
                self.ib.cancelOrder(trade.order)
                
            return {}

    def cancel_order(self, trade: Trade) -> bool:
        """
        Cancels an order.
        Returns True if cancel request was submitted successfully.
        """
        try:
            self.ib.cancelOrder(trade.order)
            self.logger.info(f"Cancelled order {trade.order.orderId}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order {trade.order.orderId}: {str(e)}")
            return False

    def modify_order(self, trade: Trade, new_price: float) -> bool:
        """
        Modify an existing limit order's price.
        Returns True if modification was submitted successfully.
        """
        if trade.orderStatus.status in ['Filled', 'Cancelled', 'ApiCancelled']:
            self.logger.warning(f"Cannot modify order {trade.order.orderId} with status {trade.orderStatus.status}")
            return False
            
        try:
            # Make a copy of the order with the new price
            order = trade.order
            if order.orderType != 'LMT':
                self.logger.warning(f"Cannot modify non-limit order {order.orderId}")
                return False
                
            order.lmtPrice = new_price
            self.ib.placeOrder(trade.contract, order)
            self.logger.info(f"Modified order {order.orderId} to new price {new_price}")
            return True
        except Exception as e:
            self.logger.error(f"Error modifying order {trade.order.orderId}: {str(e)}")
            return False

    def register_callback(self, trade_id: str, callback: Callable) -> None:
        """
        Register a callback function to be called when trade status changes.
        The callback receives the Trade object as its argument.
        """
        if trade_id not in self.trade_callbacks:
            self.trade_callbacks[trade_id] = []
        self.trade_callbacks[trade_id].append(callback)

    def _handle_order_status(self, trade: Trade) -> None:
        """
        Private callback for order status updates.
        """
        order_id = trade.order.orderId
        status = trade.orderStatus.status
        
        self.logger.debug(f"Order {order_id} status: {status}")
        
        # Find the trade_id for this trade
        trade_id = None
        for tid, t in self.active_trades.items():
            if t.order.orderId == order_id:
                trade_id = tid
                break
                
        if trade_id and trade_id in self.trade_callbacks:
            for callback in self.trade_callbacks[trade_id]:
                try:
                    callback(trade)
                except Exception as e:
                    self.logger.error(f"Error in trade callback: {str(e)}")
        
        # Remove from active trades if completed
        if status in ['Filled', 'Cancelled', 'ApiCancelled']:
            if trade_id:
                self.active_trades.pop(trade_id, None)

    def _handle_execution_details(self, trade: Trade, fill) -> None:
        """
        Private callback for execution details (fills).
        """
        self.logger.info(
            f"Fill for order {trade.order.orderId}: {fill.execution.shares} @ {fill.execution.price}, "
            f"commission: {fill.commissionReport.commission}"
        )

    def get_active_orders(self) -> List[Trade]:
        """
        Returns a list of all currently active orders.
        """
        return list(self.active_trades.values())

    def wait_for_fill(self, trade: Trade, timeout: int = 30) -> bool:
        """
        Blocks until the order is filled or timeout is reached.
        Returns True if order was filled, False otherwise.
        
        Note: In general, async callbacks are preferred to blocking calls.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if trade.orderStatus.status == 'Filled':
                return True
            if trade.orderStatus.status in ['Cancelled', 'ApiCancelled']:
                return False
            self.ib.sleep(0.1)  # Non-blocking sleep
        
        # Timeout expired
        return False
```

### 2.3 Option Selector Class

We also need an `OptionSelector` class to help build appropriate spreads based on our strategy signals:

```python
from ib_insync import IB, Option, OptionChain
from src.models.option import OptionSpread
from src.ibkr.market_data import MarketDataFetcher
import logging
from typing import Optional
import datetime

class OptionSelector:
    def __init__(self, ib: IB, market_data: MarketDataFetcher):
        self.ib = ib
        self.market_data = market_data
        self.logger = logging.getLogger('OptionSelector')

    def select_vertical_spread(
        self, 
        symbol: str, 
        direction: str,  # 'CALL' or 'PUT'
        spread_type: str,  # 'DEBIT' or 'CREDIT'
        current_price: float,
        days_to_expiration: int = 30,
        width: int = 1
    ) -> Optional[OptionSpread]:
        """
        Selects a vertical spread based on strategy requirements.
        For ATM or 1-strike OTM spreads.
        """
        try:
            # Get option chains
            chains = self.market_data.get_option_chain(symbol)
            if not chains:
                self.logger.error(f"No option chain found for {symbol}")
                return None
                
            # Find an expiration close to our target days
            target_date = datetime.date.today() + datetime.timedelta(days=days_to_expiration)
            target_date_str = target_date.strftime("%Y%m%d")
            
            # Sort expirations and find closest
            expirations = sorted(chains.keys())
            if not expirations:
                self.logger.error(f"No expirations found for {symbol}")
                return None
                
            # Find closest expiration to our target
            closest_exp = min(expirations, key=lambda x: abs(datetime.datetime.strptime(x, "%Y%m%d").date() - target_date))
            
            # Get available strikes for this expiration
            options = chains[closest_exp]
            
            # Filter for our option type (call/put)
            type_filter = direction[0]  # 'C' for CALL, 'P' for PUT
            filtered_options = [opt for opt in options if opt.right == type_filter]
            
            if not filtered_options:
                self.logger.error(f"No {direction} options found for {symbol} expiring on {closest_exp}")
                return None
                
            # Find the ATM strike (closest to current price)
            atm_strike = min(
                [opt.strike for opt in filtered_options], 
                key=lambda x: abs(x - current_price)
            )
            
            # Get strike increment
            strikes = sorted([opt.strike for opt in filtered_options])
            if len(strikes) < 2:
                self.logger.error(f"Not enough strikes for {symbol} to create a spread")
                return None
                
            strike_increment = min([strikes[i+1] - strikes[i] for i in range(len(strikes)-1) if strikes[i+1] > strikes[i]])
            
            # Now determine if we're doing ATM or 1-strike OTM based on delta preference
            # For now, just use 1-strike OTM as a default
            if spread_type == 'DEBIT':
                if direction == 'CALL':
                    # For call debit, go ATM or slightly OTM
                    long_strike = atm_strike
                    short_strike = atm_strike + (strike_increment * width)
                else:  # PUT
                    # For put debit, go ATM or slightly OTM
                    long_strike = atm_strike
                    short_strike = atm_strike - (strike_increment * width)
            else:  # CREDIT
                if direction == 'CALL':
                    # For call credit, sell below current price, buy further OTM
                    short_strike = atm_strike
                    long_strike = atm_strike + (strike_increment * width)
                else:  # PUT
                    # For put credit, sell above current price, buy further OTM
                    short_strike = atm_strike
                    long_strike = atm_strike - (strike_increment * width)

            # Create the actual option contracts to get pricing
            long_option = Option(
                symbol=symbol, 
                lastTradeDateOrContractMonth=closest_exp,
                strike=long_strike,
                right=type_filter,
                exchange='SMART'
            )
            
            short_option = Option(
                symbol=symbol, 
                lastTradeDateOrContractMonth=closest_exp,
                strike=short_strike,
                right=type_filter,
                exchange='SMART'
            )
            
            # Qualify contracts to get conId and pricing
            long_details = self.ib.qualifyContracts(long_option)
            short_details = self.ib.qualifyContracts(short_option)
            
            if not long_details or not short_details:
                self.logger.error(f"Failed to qualify one or both option contracts for {symbol}")
                return None
                
            # Use the first contract from each (should be only one)
            long_option = long_details[0]
            short_option = short_details[0]
            
            # Request market data for pricing
            long_ticker = self.ib.reqMktData(long_option)
            short_ticker = self.ib.reqMktData(short_option)
            
            # Wait for data to arrive
            self.ib.sleep(1)
            
            # Cancel market data subscriptions
            self.ib.cancelMktData(long_option)
            self.ib.cancelMktData(short_option)
            
            # Create the spread object
            spread = OptionSpread(
                symbol=symbol,
                expiration=closest_exp,
                long_strike=long_strike,
                short_strike=short_strike,
                option_type=type_filter,
                spread_type=f"{direction}_{spread_type}",
                long_leg=long_option,
                short_leg=short_option
            )
            
            # Calculate pricing (cost and max profit/loss)
            if spread_type == 'DEBIT':
                # Cost = long ask - short bid
                cost = long_ticker.ask - short_ticker.bid
                # For call debit: Max profit = spread width - cost, Max loss = cost
                # For put debit: same formula
                max_profit = (spread.width * 100) - (cost * 100)
                max_loss = cost * 100
            else:  # CREDIT
                # Credit received = short ask - long bid
                cost = short_ticker.ask - long_ticker.bid
                # For call credit: Max profit = credit, Max loss = spread width - credit
                # For put credit: same formula 
                max_profit = cost * 100
                max_loss = (spread.width * 100) - (cost * 100)
            
            # Update the spread with pricing
            spread.cost = cost
            spread.max_profit = max_profit
            spread.max_loss = max_loss
            
            self.logger.info(
                f"Selected {spread.spread_type} for {symbol}: {closest_exp} {long_strike}/{short_strike}, "
                f"Cost: ${cost:.2f}, Max Profit: ${max_profit:.2f}, Max Loss: ${max_loss:.2f}, "
                f"R/R: {spread.reward_risk_ratio:.2f}"
            )
            
            return spread
            
        except Exception as e:
            self.logger.error(f"Error selecting vertical spread for {symbol}: {str(e)}")
            return None
```

## 3. Testing & Validation

### 3.1 Unit Tests

Create `tests/orders/test_executor.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from src.orders.executor import OrderExecutor
from src.models.option import OptionSpread
from ib_insync import IB, Contract, Order, Trade, OrderStatus, CommissionReport

@pytest.fixture
def mock_ib():
    mock = MagicMock(spec=IB)
    mock.wrapper.accounts = ['DU12345']
    mock.client.getReqId.return_value = 12345
    mock.isConnected.return_value = True
    return mock

@pytest.fixture
def sample_spread():
    """Create a sample option spread for testing"""
    # Create mock option contracts
    long_leg = MagicMock()
    long_leg.conId = 123456
    long_leg.ask = 2.50
    long_leg.bid = 2.30
    
    short_leg = MagicMock()
    short_leg.conId = 123457
    short_leg.ask = 1.50
    short_leg.bid = 1.30
    
    return OptionSpread(
        symbol='AAPL',
        expiration='20231215',
        long_strike=150.0,
        short_strike=155.0,
        option_type='C',
        spread_type='CALL_DEBIT',
        long_leg=long_leg,
        short_leg=short_leg,
        cost=1.20,
        max_profit=380.0,
        max_loss=120.0
    )

@pytest.fixture
def executor(mock_ib):
    return OrderExecutor(mock_ib, paper=True)

def test_send_vertical_spread_paper_mode(executor, mock_ib, sample_spread):
    """Test that market orders are used in paper mode"""
    # Setup mock return value for placeOrder
    mock_trade = MagicMock(spec=Trade)
    mock_ib.placeOrder.return_value = mock_trade
    
    # Call the method being tested
    trade = executor.send_vertical_spread(sample_spread)
    
    # Verify results
    assert trade == mock_trade
    
    # Check that the order was created correctly
    mock_ib.placeOrder.assert_called_once()
    args = mock_ib.placeOrder.call_args
    
    # First arg should be the contract
    contract = args[0][0]
    assert contract.symbol == 'AAPL'
    assert contract.secType == 'BAG'
    assert len(contract.comboLegs) == 2
    
    # Verify combo legs
    assert contract.comboLegs[0].action == 'BUY'
    assert contract.comboLegs[1].action == 'SELL'
    
    # Second arg should be the order
    order = args[0][1]
    assert order.orderType == 'MKT'
    assert order.totalQuantity == 1

def test_send_vertical_spread_live_mode(mock_ib, sample_spread):
    """Test that limit orders are used in live mode"""
    # Create executor in live mode
    executor = OrderExecutor(mock_ib, paper=False)
    
    # Setup mock return value for placeOrder
    mock_trade = MagicMock(spec=Trade)
    mock_ib.placeOrder.return_value = mock_trade
    
    # Call the method being tested
    trade = executor.send_vertical_spread(sample_spread)
    
    # Verify limit order was created
    mock_ib.placeOrder.assert_called_once()
    args = mock_ib.placeOrder.call_args
    
    # Check order type
    order = args[0][1]
    assert order.orderType == 'LMT'
    assert order.tif == 'DAY'
    
    # For a debit spread, expect price to be approximately (long.ask + short.bid)/2
    expected_price = (sample_spread.long_leg.ask + sample_spread.short_leg.bid) / 2
    expected_price = round(expected_price * 0.99, 2)  # With small improvement
    assert abs(order.lmtPrice - expected_price) < 0.01

def test_cancel_order(executor, mock_ib):
    """Test order cancellation"""
    # Setup mock trade
    mock_trade = MagicMock(spec=Trade)
    mock_trade.order.orderId = 12345
    
    # Call the method being tested
    result = executor.cancel_order(mock_trade)
    
    # Verify
    assert result is True
    mock_ib.cancelOrder.assert_called_once_with(mock_trade.order)

def test_modify_order(executor, mock_ib):
    """Test order price modification"""
    # Setup mock trade with status
    mock_trade = MagicMock(spec=Trade)
    mock_trade.order.orderId = 12345
    mock_trade.order.orderType = 'LMT'
    mock_trade.orderStatus.status = 'Submitted'
    
    # Call the method being tested
    result = executor.modify_order(mock_trade, 1.50)
    
    # Verify
    assert result is True
    mock_ib.placeOrder.assert_called_once()
    assert mock_trade.order.lmtPrice == 1.50

def test_cannot_modify_filled_order(executor, mock_ib):
    """Test that filled orders cannot be modified"""
    # Setup mock trade with filled status
    mock_trade = MagicMock(spec=Trade)
    mock_trade.order.orderId = 12345
    mock_trade.orderStatus.status = 'Filled'
    
    # Call the method being tested
    result = executor.modify_order(mock_trade, 1.50)
    
    # Verify
    assert result is False
    mock_ib.placeOrder.assert_not_called()

def test_order_status_callback(executor):
    """Test order status callback mechanism"""
    # Setup a mock callback
    callback = MagicMock()
    
    # Setup a mock trade
    mock_trade = MagicMock(spec=Trade)
    mock_trade.order.orderId = 12345
    mock_trade.orderStatus = MagicMock()
    mock_trade.orderStatus.status = 'Submitted'
    
    # Add trade to active trades
    trade_id = '123'
    executor.active_trades[trade_id] = mock_trade
    
    # Register callback
    executor.register_callback(trade_id, callback)
    
    # Trigger the status update
    executor._handle_order_status(mock_trade)
    
    # Verify callback was called
    callback.assert_called_once_with(mock_trade)
    
    # Change status to filled and test cleanup
    mock_trade.orderStatus.status = 'Filled'
    executor._handle_order_status(mock_trade)
    
    # Verify trade was removed from active trades
    assert trade_id not in executor.active_trades
```

### 3.2 Integration Tests

Create `tests/integration/test_order_integration.py`:

```python
import pytest
from ib_insync import IB
from src.ibkr.connector import IBConnector
from src.ibkr.market_data import MarketDataFetcher
from src.orders.option_selector import OptionSelector
from src.orders.executor import OrderExecutor
from src.config.loader import load_config

@pytest.mark.integration
def test_order_integration_with_paper_tws():
    """Integration test with paper TWS - requires running TWS instance"""
    # Skip if running in CI environment
    # Load config
    config = load_config('config.yaml')
    
    # Create real components
    ib_connector = IBConnector()
    ib = ib_connector.connect(
        host=config['ibkr']['host'],
        port=config['ibkr']['port'],
        client_id=config['ibkr']['client_id']
    )
    
    # Skip if not connected
    if not ib.isConnected():
        pytest.skip("TWS not available for integration testing")
    
    try:
        market_data = MarketDataFetcher(ib)
        option_selector = OptionSelector(ib, market_data)
        executor = OrderExecutor(ib, paper=True)
        
        # Test with a liquid symbol
        symbol = "SPY"
        current_price = market_data.get_last_price(symbol)
        
        # Create a sample spread
        spread = option_selector.select_vertical_spread(
            symbol=symbol,
            direction="CALL",
            spread_type="DEBIT",
            current_price=current_price,
            days_to_expiration=30,
            width=1
        )
        
        assert spread is not None, "Failed to create test spread"
        
        # Place the order
        trade = executor.send_vertical_spread(spread)
        assert trade is not None, "Failed to place test order"
        
        # Wait a moment for order to register
        ib.sleep(1)
        
        # Cancel the order
        result = executor.cancel_order(trade)
        assert result is True, "Failed to cancel test order"
        
    finally:
        # Clean up
        ib_connector.disconnect()
```

## 4. Cucumber Scenarios

Create `tests/bdd/features/order_execution.feature`:

```gherkin
Feature: Spread Order Execution
  Background:
    Given a connected IBKR instance
    And a valid OptionSpread for "AAPL"

  Scenario: Place a debit combo order in paper mode
    Given OrderExecutor in paper trading mode
    When I call send_vertical_spread(spread)
    Then IB.placeOrder is invoked with orderType == 'MKT'

  Scenario: Place a limit combo order in live mode
    Given OrderExecutor in live mode
    When I call send_vertical_spread(spread)
    Then IB.placeOrder is invoked with orderType == 'LMT'
    And order.lmtPrice == (long.ask + short.bid) / 2 * 0.99

  Scenario: Cancel an order
    Given a Trade with orderId
    When I call cancel_order(trade)
    Then IB.cancelOrder(trade.order) is called

  Scenario: Modify order price
    Given a submitted limit order
    When I call modify_order(trade, 1.50)
    Then the order's limit price is updated to 1.50

  Scenario: Order status callbacks
    Given a trade with a registered callback
    When the order status changes to 'Filled'
    Then the callback is invoked with the trade object
    And the trade is removed from active_trades
```

Create `tests/bdd/steps/order_steps.py`:

```python
import pytest
from pytest_bdd import given, when, then, parsers
from unittest.mock import MagicMock, patch
from src.orders.executor import OrderExecutor
from src.models.option import OptionSpread

@given('a connected IBKR instance')
def mock_ib():
    mock = MagicMock()
    mock.wrapper.accounts = ['DU12345']
    mock.client.getReqId.return_value = 12345
    mock.isConnected.return_value = True
    return mock

@given('a valid OptionSpread for "AAPL"')
def sample_spread():
    # Create mock option contracts
    long_leg = MagicMock()
    long_leg.conId = 123456
    long_leg.ask = 2.50
    long_leg.bid = 2.30
    
    short_leg = MagicMock()
    short_leg.conId = 123457
    short_leg.ask = 1.50
    short_leg.bid = 1.30
    
    return OptionSpread(
        symbol='AAPL',
        expiration='20231215',
        long_strike=150.0,
        short_strike=155.0,
        option_type='C',
        spread_type='CALL_DEBIT',
        long_leg=long_leg,
        short_leg=short_leg,
        cost=1.20,
        max_profit=380.0,
        max_loss=120.0
    )

@given('OrderExecutor in paper trading mode')
def executor_paper_mode(mock_ib):
    return OrderExecutor(mock_ib, paper=True)

@given('OrderExecutor in live mode')
def executor_live_mode(mock_ib):
    return OrderExecutor(mock_ib, paper=False)

@when('I call send_vertical_spread(spread)')
def call_send_vertical_spread(executor_paper_mode, sample_spread):
    # Setup mock return value for placeOrder
    mock_trade = MagicMock()
    executor_paper_mode.ib.placeOrder.return_value = mock_trade
    
    # Call the method
    executor_paper_mode.context = {}
    executor_paper_mode.context['trade'] = executor_paper_mode.send_vertical_spread(sample_spread)
    executor_paper_mode.context['placeOrder_args'] = executor_paper_mode.ib.placeOrder.call_args

@then('IB.placeOrder is invoked with orderType == \'MKT\'')
def verify_market_order(executor_paper_mode):
    assert executor_paper_mode.ib.placeOrder.called
    order = executor_paper_mode.context['placeOrder_args'][0][1]
    assert order.orderType == 'MKT'

@then('IB.placeOrder is invoked with orderType == \'LMT\'')
def verify_limit_order(executor_live_mode):
    assert executor_live_mode.ib.placeOrder.called
    order = executor_live_mode.context['placeOrder_args'][0][1]
    assert order.orderType == 'LMT'

@then(parsers.parse('order.lmtPrice == (long.ask + short.bid) / 2 * {factor:f}'))
def verify_limit_price(executor_live_mode, sample_spread, factor):
    order = executor_live_mode.context['placeOrder_args'][0][1]
    expected_price = (sample_spread.long_leg.ask + sample_spread.short_leg.bid) / 2 * factor
    expected_price = round(expected_price, 2)
    assert abs(order.lmtPrice - expected_price) < 0.01

@given('a Trade with orderId')
def mock_trade():
    mock = MagicMock()
    mock.order.orderId = 12345
    return mock

@when('I call cancel_order(trade)')
def call_cancel_order(executor_paper_mode, mock_trade):
    executor_paper_mode.cancel_order(mock_trade)

@then('IB.cancelOrder(trade.order) is called')
def verify_cancel_order(executor_paper_mode, mock_trade):
    executor_paper_mode.ib.cancelOrder.assert_called_once_with(mock_trade.order)

@given('a submitted limit order')
def submitted_limit_order():
    mock = MagicMock()
    mock.order.orderId = 12345
    mock.order.orderType = 'LMT'
    mock.order.lmtPrice = 1.25
    mock.orderStatus.status = 'Submitted'
    return mock

@when(parsers.parse('I call modify_order(trade, {new_price:f})'))
def call_modify_order(executor_paper_mode, submitted_limit_order, new_price):
    executor_paper_mode.modify_order(submitted_limit_order, new_price)

@then(parsers.parse('the order\'s limit price is updated to {expected_price:f}'))
def verify_modify_price(submitted_limit_order, expected_price):
    assert submitted_limit_order.order.lmtPrice == expected_price

@given('a trade with a registered callback')
def setup_callback(executor_paper_mode):
    # Create a mock trade
    mock_trade = MagicMock()
    mock_trade.order.orderId = 12345
    
    # Create a mock callback
    mock_callback = MagicMock()
    
    # Add to active trades and register callback
    trade_id = '123'
    executor_paper_mode.active_trades[trade_id] = mock_trade
    executor_paper_mode.register_callback(trade_id, mock_callback)
    
    # Store for later steps
    executor_paper_mode.context = {
        'trade': mock_trade,
        'callback': mock_callback,
        'trade_id': trade_id
    }

@when(parsers.parse('the order status changes to \'{status}\''))
def change_order_status(executor_paper_mode, status):
    # Update the order status
    executor_paper_mode.context['trade'].orderStatus.status = status
    
    # Trigger the callback
    executor_paper_mode._handle_order_status(executor_paper_mode.context['trade'])

@then('the callback is invoked with the trade object')
def verify_callback_called(executor_paper_mode):
    executor_paper_mode.context['callback'].assert_called_once_with(executor_paper_mode.context['trade'])

@then('the trade is removed from active_trades')
def verify_trade_removed(executor_paper_mode):
    assert executor_paper_mode.context['trade_id'] not in executor_paper_mode.active_trades
```

## 5. Pseudocode Outline

```python
# Example usage in app/main.py
from src.ibkr.connector import IBConnector
from src.ibkr.market_data import MarketDataFetcher
from src.orders.option_selector import OptionSelector
from src.orders.executor import OrderExecutor
from src.strategies.engine import StrategyEngine

# Initialize components
ib_connector = IBConnector()
ib = ib_connector.connect(host='localhost', port=7497, client_id=1)

market_data = MarketDataFetcher(ib)
option_selector = OptionSelector(ib, market_data)
strategy_engine = StrategyEngine(market_data, option_selector)
order_executor = OrderExecutor(ib, paper=True)

# Process a symbol and execute if signal found
symbol = 'NFLX'
signal = strategy_engine.evaluate(symbol)

if signal:
    spread = signal['spread']
    print(f"Placing {signal['type']} for {symbol}")
    trade = order_executor.send_vertical_spread(spread)
    
    # Wait for fill
    order_filled = order_executor.wait_for_fill(trade, timeout=30)
    
    if order_filled:
        print(f"Order filled: {trade.orderStatus.status}")
    else:
        print(f"Order not filled, cancelling...")
        order_executor.cancel_order(trade)
else:
    print(f"No trade signal for {symbol}")
```
