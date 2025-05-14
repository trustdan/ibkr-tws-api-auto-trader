#!/usr/bin/env python3
"""
Example Python client for the Go Scanner Service.
This shows how to implement a gRPC client in Python to call the ScanUniverse method.

Note: In a production environment, this would use the generated Python stubs from the proto file.
For this example, we're manually implementing what the generated code would do.
"""

import sys
import time
from enum import IntEnum
from typing import List, Optional

import grpc


# Constants for signal types - must match the values in the proto file
class SignalType(IntEnum):
    NONE = 0
    CALL_DEBIT = 1
    PUT_DEBIT = 2
    CALL_CREDIT = 3
    PUT_CREDIT = 4


class ScannerClient:
    """Client for the Go Scanner Service."""

    def __init__(self, server_address: str):
        """Initialize the client with server address."""
        # In a real implementation, we would use the generated stubs
        # channel = grpc.insecure_channel(server_address)
        # self.stub = scanner_pb2_grpc.ScannerServiceStub(channel)
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)

    def scan_universe(self, symbols: Optional[List[str]] = None) -> dict:
        """
        Call the ScanUniverse method on the Go Scanner Service.

        Args:
            symbols: Optional list of symbols to scan. If not provided, uses the default universe.

        Returns:
            Dictionary mapping symbols to signal types.
        """
        print(f"Connecting to scanner service at {self.server_address}")
        print(f"Requesting scan for symbols: {symbols or 'default universe'}")

        # In a real implementation, we would use the generated stubs like:
        # request = scanner_pb2.ScanRequest(symbols=symbols or [])
        # response = self.stub.ScanUniverse(request)

        # For this example, we'll simulate the response
        # In a real implementation, the following would be returned from the gRPC call
        simulated_response = {
            "AAPL": SignalType.CALL_DEBIT,
            "MSFT": SignalType.CALL_CREDIT,
            "SPY": SignalType.PUT_DEBIT,
            "QQQ": SignalType.PUT_CREDIT,
        }

        # Simulate network delay
        time.sleep(0.5)

        return simulated_response


def main():
    """Example usage of the scanner client."""
    # Default to localhost:50051 if no address provided
    server_address = sys.argv[1] if len(sys.argv) > 1 else "localhost:50051"

    # Create client
    client = ScannerClient(server_address)

    # Example 1: Scan the default universe
    print("Example 1: Scanning default universe")
    results = client.scan_universe()
    print_results(results)

    # Example 2: Scan specific symbols
    print("\nExample 2: Scanning specific symbols")
    custom_symbols = ["AAPL", "GOOG", "MSFT"]
    results = client.scan_universe(custom_symbols)
    print_results(results)


def print_results(results: dict):
    """Print scan results in a formatted way."""
    print("Scan Results:")
    print("=" * 40)
    print(f"{'Symbol':<10} {'Signal Type':<15}")
    print("-" * 40)

    for symbol, signal_type in results.items():
        signal_name = (
            SignalType(signal_type).name
            if isinstance(signal_type, int)
            else signal_type
        )
        print(f"{symbol:<10} {signal_name:<15}")

    print("=" * 40)


if __name__ == "__main__":
    main()
