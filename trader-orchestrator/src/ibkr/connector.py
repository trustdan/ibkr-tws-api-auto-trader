"""
Connection management for Interactive Brokers TWS/Gateway.
Provides robust connect/disconnect handling and event-driven status updates.
"""
from ib_insync import IB
import time
import logging
from typing import Optional, Callable

# Configure logger
logger = logging.getLogger(__name__)

class IBConnector:
    """
    Handles connection to Interactive Brokers TWS/Gateway.
    
    Features:
    - Connection with retry logic
    - Event-driven connection status
    - Error handling
    - Non-blocking event loop management
    """
    
    def __init__(self, host: str, port: int, client_id: int, timeout: float = 5,
                 readonly: bool = True, max_attempts: int = 3):
        """
        Initialize the connector.
        
        Args:
            host: The hostname or IP address of TWS/Gateway
            port: The port number
            client_id: The client ID to use for the connection
            timeout: Connection timeout in seconds
            readonly: Whether to connect in read-only mode
            max_attempts: Maximum number of connection attempts
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.timeout = timeout
        self.readonly = readonly
        self.max_attempts = max_attempts
        self.connected = False
        self._setup_event_handlers()
        self._status_callbacks = []
        
    def _setup_event_handlers(self):
        """Set up event handlers for IB connection events."""
        self.ib.connectedEvent += self._on_connected
        self.ib.disconnectedEvent += self._on_disconnected
        self.ib.errorEvent += self._on_error
        
    def connect(self) -> bool:
        """
        Attempt to connect to TWS/Gateway with retry logic.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        logger.info(f"Connecting to {self.host}:{self.port} (client ID: {self.client_id})")
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug(f"Connection attempt {attempt}/{self.max_attempts}")
                self.ib.connect(
                    self.host, 
                    self.port, 
                    clientId=self.client_id, 
                    readonly=self.readonly,
                    timeout=self.timeout
                )
                # Let the event loop process the connection event
                self.ib.sleep(0.1)
                break
            except Exception as e:
                logger.warning(f"Connection attempt {attempt} failed: {str(e)}")
                if attempt < self.max_attempts:
                    time.sleep(1)  # Wait before retrying
                else:
                    logger.error(f"Failed to connect after {self.max_attempts} attempts")
                    return False
                    
        return self.connected
        
    def disconnect(self) -> bool:
        """
        Disconnect from TWS/Gateway.
        
        Returns:
            bool: True if disconnection successful (i.e., not connected)
        """
        logger.info("Disconnecting from IBKR")
        if self.ib.isConnected():
            self.ib.disconnect()
            # Let the event loop process the disconnect event
            self.ib.sleep(0.1)
        return not self.connected
        
    def is_connected(self) -> bool:
        """
        Check if currently connected to TWS/Gateway.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
        
    def keep_alive(self):
        """
        Run the event loop once to process pending messages.
        Call this periodically to keep the connection alive.
        """
        if self.connected:
            self.ib.sleep(0)
            
    def add_status_callback(self, callback: Callable[[bool], None]):
        """
        Add a callback to be notified of connection status changes.
        
        Args:
            callback: A function that takes a boolean (connected status)
        """
        self._status_callbacks.append(callback)
        
    def remove_status_callback(self, callback: Callable[[bool], None]):
        """
        Remove a previously added status callback.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
            
    # Event handlers
    def _on_connected(self):
        """Handle connection event."""
        self.connected = True
        logger.info("Connected to IBKR")
        for callback in self._status_callbacks:
            callback(True)
            
    def _on_disconnected(self):
        """Handle disconnection event."""
        self.connected = False
        logger.info("Disconnected from IBKR")
        for callback in self._status_callbacks:
            callback(False)
            
    def _on_error(self, reqId, errorCode, errorString, contract):
        """
        Handle error events from IB.
        
        Args:
            reqId: Request ID that generated the error
            errorCode: Error code from IB
            errorString: Error message
            contract: Contract related to the error (if any)
        """
        logger.error(f"IBKR Error {errorCode}: {errorString}")
        
        # Critical connection errors that should update connection status
        critical_errors = [1100, 1101, 1102, 1300, 2110]
        
        if errorCode in critical_errors:
            logger.warning("Critical connection error detected")
            self.connected = False
            for callback in self._status_callbacks:
                callback(False)
                
    def __del__(self):
        """Ensure we disconnect when the object is garbage collected."""
        if hasattr(self, 'ib') and self.ib.isConnected():
            self.ib.disconnect() 