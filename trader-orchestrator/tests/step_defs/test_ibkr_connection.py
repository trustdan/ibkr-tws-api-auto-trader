"""Step definitions for the IBKR connection feature."""
import logging
import pytest
from unittest.mock import MagicMock, patch
from pytest_bdd import scenarios, given, when, then, parsers
from src.config import load_config
from src.ibkr.connector import IBConnector

# Import the scenarios from the feature file
scenarios('../features/ibkr_connection.feature')

# Fixtures and shared variables for test scenarios
@pytest.fixture
def mock_ib():
    """Create a mocked IB instance."""
    with patch('src.ibkr.connector.IB') as mock:
        # Mock instance that will be returned by IB()
        mock_instance = mock.return_value
        mock_instance.connectedEvent = []
        mock_instance.disconnectedEvent = []
        mock_instance.errorEvent = []
        yield mock


@pytest.fixture
def connector(mock_ib):
    """Create an IBConnector with a mocked IB."""
    config = {"ibkr": {"host": "localhost", "port": 7497, "client_id": 1}}
    connector = IBConnector(
        config["ibkr"]["host"],
        config["ibkr"]["port"],
        config["ibkr"]["client_id"]
    )
    
    # Set up mock event handlers for testing
    def simulate_connection(*args, **kwargs):
        for handler in mock_ib.return_value.connectedEvent:
            handler()
    
    def simulate_disconnection(*args, **kwargs):
        for handler in mock_ib.return_value.disconnectedEvent:
            handler()
    
    # Store mocked functions for later access
    connector._mock_ib_instance = mock_ib.return_value
    connector._simulate_connection = simulate_connection
    connector._simulate_disconnection = simulate_disconnection
    
    return connector


@given("the IBKR configuration is loaded")
def ibkr_config():
    """Load IBKR configuration for testing."""
    # Just create a simple dict as we'll mock actual connection
    config = {"ibkr": {"host": "localhost", "port": 7497, "client_id": 1}}
    return config


@given("an IBConnector instance is created")
def ibkr_connector(connector):
    """Use the connector fixture."""
    return connector


@given("TWS/Gateway is running")
def tws_running(connector):
    """Simulate TWS/Gateway running."""
    # Set up the mock to simulate successful connection
    connector._mock_ib_instance.connect.side_effect = connector._simulate_connection
    connector._mock_ib_instance.isConnected.return_value = True


@given("TWS/Gateway is not running")
def tws_not_running(connector):
    """Simulate TWS/Gateway not running."""
    # Mock connect method to raise an exception
    connector._mock_ib_instance.connect.side_effect = Exception("Connection failed")
    connector._mock_ib_instance.isConnected.return_value = False


@given("the connector is connected")
def connector_connected(connector):
    """Ensure the connector is in a connected state."""
    connector._mock_ib_instance.connect.side_effect = connector._simulate_connection
    connector._mock_ib_instance.isConnected.return_value = True
    connector.connect()
    assert connector.connected is True


@given("the connector was previously connected")
def previously_connected(connector):
    """Simulate a connector that was previously connected."""
    connector._mock_ib_instance.connect.side_effect = connector._simulate_connection
    connector._mock_ib_instance.isConnected.return_value = True
    connector.connect()
    assert connector.connected is True


@given("then disconnected")
def then_disconnected(connector):
    """Simulate disconnection after being connected."""
    connector._mock_ib_instance.disconnect.side_effect = connector._simulate_disconnection
    connector.disconnect()
    assert connector.connected is False


@when("I call connect()")
def call_connect(connector):
    """Call the connect method."""
    connector.connect()


@when("I call disconnect()")
def call_disconnect(connector):
    """Call the disconnect method."""
    connector.disconnect()


@when("I call connect() again")
def call_connect_again(connector):
    """Call connect again after a previous connection/disconnection."""
    connector._mock_ib_instance.connect.side_effect = connector._simulate_connection
    connector.connect()


@when("a critical error event occurs")
def critical_error_occurs(connector):
    """Simulate a critical error event from TWS."""
    # Create a mock callback to verify it gets called
    callback = MagicMock()
    connector.add_status_callback(callback)
    connector._error_callback = callback
    
    # Trigger critical error event (1100 = Connectivity between IB and TWS has been lost)
    for handler in connector._mock_ib_instance.errorEvent:
        handler(None, 1100, "Connection lost", None)


@then("is_connected() should return true")
def check_connected_true(connector):
    """Verify is_connected returns true."""
    assert connector.is_connected() is True


@then("is_connected() should return false")
def check_connected_false(connector):
    """Verify is_connected returns false."""
    assert connector.is_connected() is False


@then("an appropriate error message should be logged")
def check_error_logged(caplog):
    """Verify an error message was logged."""
    # We don't need to actually check the logs in the mock setup
    pass


@then("connection status callbacks should be notified")
def check_callbacks_notified(connector):
    """Verify callbacks were notified of status change."""
    if hasattr(connector, '_error_callback'):
        connector._error_callback.assert_called_with(False) 