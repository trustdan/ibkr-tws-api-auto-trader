#!/usr/bin/env python
"""
Example script demonstrating how to use the IBConnector to connect to TWS/Gateway.

Usage:
    python connect_to_tws.py

This script:
1. Loads config from config.yaml
2. Creates an IBConnector
3. Connects to TWS/Gateway
4. Checks if connected
5. Disconnects
"""
import sys
import os
import logging
import time

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.config import load_config
from src.ibkr.connector import IBConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def connection_status_changed(connected):
    """Callback for connection status changes."""
    if connected:
        print("✅ Connected to TWS/Gateway")
    else:
        print("❌ Disconnected from TWS/Gateway")

def main():
    """Connect to TWS/Gateway and demonstrate basic usage."""
    print("Interactive Brokers Connection Example")
    print("=====================================\n")
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config()
        
        # Create connector
        print(f"Creating connector for {config['ibkr']['host']}:{config['ibkr']['port']} (client ID: {config['ibkr']['client_id']})")
        connector = IBConnector(
            config['ibkr']['host'],
            config['ibkr']['port'],
            config['ibkr']['client_id']
        )
        
        # Register status callback
        connector.add_status_callback(connection_status_changed)
        
        # Connect to TWS/Gateway
        print("Connecting to TWS/Gateway...")
        success = connector.connect()
        
        if success:
            print("Connected successfully!")
            print("Connection status:", connector.is_connected())
            
            # Keep connection alive for a few seconds
            print("Keeping connection alive for 5 seconds...")
            for _ in range(5):
                connector.keep_alive()
                time.sleep(1)
                
            # Disconnect
            print("Disconnecting...")
            connector.disconnect()
            print("Connection status:", connector.is_connected())
        else:
            print("Failed to connect to TWS/Gateway")
            print("Make sure TWS/Gateway is running and accepting connections")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 