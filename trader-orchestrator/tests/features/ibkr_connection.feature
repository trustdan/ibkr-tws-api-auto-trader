Feature: IBKR Connection Handling
  As a trader
  I want to reliably connect to Interactive Brokers TWS/Gateway
  So that I can retrieve market data and execute trades

  Background:
    Given the IBKR configuration is loaded
    And an IBConnector instance is created

  Scenario: Successful connection
    Given TWS/Gateway is running
    When I call connect()
    Then is_connected() should return true

  Scenario: Graceful disconnection
    Given the connector is connected
    When I call disconnect()
    Then is_connected() should return false

  Scenario: Connection failure handling
    Given TWS/Gateway is not running
    When I call connect()
    Then is_connected() should return false
    And an appropriate error message should be logged

  Scenario: Reconnection after disconnect
    Given the connector was previously connected
    And then disconnected
    When I call connect() again
    Then is_connected() should return true

  Scenario: Error events update connection status
    Given the connector is connected
    When a critical error event occurs
    Then is_connected() should return false
    And connection status callbacks should be notified 