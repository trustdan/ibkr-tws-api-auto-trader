# 02-ibkr-connection.md

## 1. Overview

This document covers establishing and maintaining a robust connection to Interactive Brokers TWS/Gateway using `ib_insync`.  We encapsulate connection logic in an `IBConnector` class, ensuring retries, timeouts, and event-driven state updates.  Correct connection management is critical: without it, market data retrieval and order execution cannot proceed.

Key goals:

* Connect/disconnect cleanly to TWS/Gateway
* Keep the connection non-blocking (allowing the `ib_insync` event loop to run)
* Surface connection status to upstream modules and GUI
* Handle errors and automatic reconnection where appropriate

## 2. IBConnector Class Design

Create `src/ibkr/connector.py`:

```python
from ib_insync import IB
import time

class IBConnector:
    def __init__(self, host: str, port: int, client_id: int, timeout: float = 5):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.timeout = timeout
        self.connected = False
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        self.ib.connectedEvent += self._on_connected
        self.ib.disconnectedEvent += self._on_disconnected
        self.ib.errorEvent += self._on_error

    def connect(self) -> bool:
        """Attempt to connect with retry logic."""
        for attempt in range(1, 4):
            try:
                self.ib.connect(self.host, self.port, self.client_id, timeout=self.timeout)
                break
            except Exception as e:
                if attempt < 3:
                    time.sleep(1)
                else:
                    raise
        return self.connected

    def disconnect(self):
        self.ib.disconnect()
        return not self.connected

    def is_connected(self) -> bool:
        return self.connected

    # Event handlers
    def _on_connected(self):
        self.connected = True
        print("[IBConnector] Connected to IBKR")

    def _on_disconnected(self):
        self.connected = False
        print("[IBConnector] Disconnected from IBKR")

    def _on_error(self, reqId, errorCode, errorString, contract):
        print(f"[IBConnector] Error {errorCode}: {errorString}")
        # Optionally set self.connected = False on critical errors
```

## 3. Testing & Mocking

* Use `pytest` to test `connect()` and `disconnect()` with a **mocked** IB instance (e.g., monkeypatch `IB.connect` to simulate success/failure).
* For integration, run a local TWS paper-trading instance and verify `is_connected()` flips.

## 4. Cucumber Scenarios

```gherkin
Feature: IBKR Connection Handling
  Background:
    Given a running TWS/Gateway on localhost:7497
    And valid credentials (host, port, client_id)

  Scenario: Successful connection
    When I call connector.connect()
    Then connector.is_connected() should be true

  Scenario: Graceful disconnection
    Given connector.is_connected() is true
    When I call connector.disconnect()
    Then connector.is_connected() should be false

  Scenario: Failed connection
    Given TWS/Gateway is not running
    When I call connector.connect()
    Then an exception is raised
```

## 5. Pseudocode Outline

```python
# Load IBKR config
cfg = load_config()
connector = IBConnector(cfg['ibkr']['host'], cfg['ibkr']['port'], cfg['ibkr']['client_id'])

# Attempt connection
if connector.connect():
    print("Connected, proceeding to market data retrieval")
else:
    raise RuntimeError("Unable to connect to IBKR")
```
