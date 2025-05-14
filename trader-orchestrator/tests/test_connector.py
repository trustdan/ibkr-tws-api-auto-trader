"""Unit tests for the IBConnector class."""
import pytest
from unittest.mock import MagicMock, patch
from src.ibkr.connector import IBConnector

class TestIBConnector:
    """Test suite for IBConnector class."""
    
    def test_init(self):
        """Test initializing the connector."""
        connector = IBConnector("localhost", 7497, 1)
        assert connector.host == "localhost"
        assert connector.port == 7497
        assert connector.client_id == 1
        assert connector.connected is False
        
    @patch('src.ibkr.connector.IB')
    def test_successful_connection(self, mock_ib):
        """Test successful connection to IBKR."""
        # Set up the mock
        mock_instance = mock_ib.return_value
        
        # Create connector with mocked IB
        connector = IBConnector("localhost", 7497, 1)
        
        # Set up the connection event handler to mimic connection success
        def trigger_connected(*args, **kwargs):
            # Simulate the connected event being triggered
            for handler in mock_instance.connectedEvent:
                handler()
        
        # Make mock_instance.connect trigger the connected event
        mock_instance.connect.side_effect = trigger_connected
        
        # Call connect
        result = connector.connect()
        
        # Assertions
        assert result is True
        assert connector.connected is True
        mock_instance.connect.assert_called_once_with(
            "localhost", 7497, clientId=1, readonly=True, timeout=5
        )
        
    @patch('src.ibkr.connector.IB')
    def test_connection_failure(self, mock_ib):
        """Test connection failure to IBKR."""
        # Set up the mock
        mock_instance = mock_ib.return_value
        mock_instance.connect.side_effect = Exception("Connection failed")
        
        # Create connector with mocked IB
        connector = IBConnector("localhost", 7497, 1, max_attempts=2)
        
        # Call connect
        result = connector.connect()
        
        # Assertions
        assert result is False
        assert connector.connected is False
        assert mock_instance.connect.call_count == 2  # Two connection attempts
        
    @patch('src.ibkr.connector.IB')
    def test_disconnection(self, mock_ib):
        """Test disconnection from IBKR."""
        # Set up the mock
        mock_instance = mock_ib.return_value
        mock_instance.isConnected.return_value = True
        
        # Create connector with mocked IB
        connector = IBConnector("localhost", 7497, 1)
        
        # Simulate being connected
        connector.connected = True
        
        # Set up the disconnection event handler
        def trigger_disconnected(*args, **kwargs):
            # Simulate the disconnected event being triggered
            for handler in mock_instance.disconnectedEvent:
                handler()
        
        # Make disconnect trigger the disconnected event
        mock_instance.disconnect.side_effect = trigger_disconnected
        
        # Call disconnect
        result = connector.disconnect()
        
        # Assertions
        assert result is True
        assert connector.connected is False
        mock_instance.disconnect.assert_called_once()
        
    @patch('src.ibkr.connector.IB')
    def test_error_handling(self, mock_ib):
        """Test error handling in IBConnector."""
        # Set up the mock
        mock_instance = mock_ib.return_value
        
        # Create connector with mocked IB
        connector = IBConnector("localhost", 7497, 1)
        
        # Simulate being connected
        connector.connected = True
        
        # Create a mock callback
        mock_callback = MagicMock()
        connector.add_status_callback(mock_callback)
        
        # Trigger a critical error (1100 = Connectivity between IB and TWS has been lost)
        for handler in mock_instance.errorEvent:
            handler(None, 1100, "Connection lost", None)
        
        # Assertions
        assert connector.connected is False
        mock_callback.assert_called_once_with(False)
        
    @patch('src.ibkr.connector.IB')
    def test_status_callbacks(self, mock_ib):
        """Test status callback functionality."""
        # Create connector with mocked IB
        connector = IBConnector("localhost", 7497, 1)
        
        # Create mock callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        # Add callbacks
        connector.add_status_callback(callback1)
        connector.add_status_callback(callback2)
        
        # Trigger connected event
        connector._on_connected()
        
        # Check both callbacks were called with True
        callback1.assert_called_once_with(True)
        callback2.assert_called_once_with(True)
        
        # Reset mocks
        callback1.reset_mock()
        callback2.reset_mock()
        
        # Remove one callback
        connector.remove_status_callback(callback1)
        
        # Trigger disconnected event
        connector._on_disconnected()
        
        # Check only callback2 was called
        callback1.assert_not_called()
        callback2.assert_called_once_with(False)
        
    @patch('src.ibkr.connector.IB')
    def test_keep_alive(self, mock_ib):
        """Test keep_alive method."""
        # Set up the mock
        mock_instance = mock_ib.return_value
        
        # Create connector with mocked IB
        connector = IBConnector("localhost", 7497, 1)
        
        # Simulate being connected
        connector.connected = True
        
        # Call keep_alive
        connector.keep_alive()
        
        # Assert ib.sleep was called to run the event loop
        mock_instance.sleep.assert_called_with(0) 