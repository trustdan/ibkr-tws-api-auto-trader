# 04-mocking-and-tests.md

## 1. Overview

This document outlines testing strategies for the Go Scanner service. We'll cover:

* **Unit Testing** with mocked `MarketDataClient` to verify signal generation logic independently
* **Table-Driven Tests** for comprehensive coverage of signal patterns (bullish, bearish, high-IV)
* **Concurrency Testing** to ensure parallel scanning works correctly
* **Integration Tests** with in-memory gRPC connections

Through proper test coverage, we'll ensure our scanner accurately identifies trading opportunities based on our defined patterns and handles errors gracefully.

## 2. Unit Testing with Mocks

### Creating a Mock MarketDataClient

Since our scanner depends on the `MarketDataClient` to fetch historical bars and IV data, we need to mock this interface for testing:

```go
package scan

import (
  "context"
  pb "github.com/your-org/trader-scanner/pkg/pb"
)

// MockMarketDataClient implements the MarketDataServiceClient interface
type MockMarketDataClient struct {
  BarsResponse *pb.BarsResponse
  IVResponse   *pb.IVResponse
  BarsError    error
  IVError      error
}

func (m *MockMarketDataClient) GetHistoricalBars(ctx context.Context, in *pb.BarsRequest, opts ...grpc.CallOption) (*pb.BarsResponse, error) {
  return m.BarsResponse, m.BarsError
}

func (m *MockMarketDataClient) GetIVPercentile(ctx context.Context, in *pb.IVRequest, opts ...grpc.CallOption) (*pb.IVResponse, error) {
  return m.IVResponse, m.IVError
}
```

### Unit Testing Core Logic

Test the pattern detection logic in isolation:

```go
package scan

import (
  "context"
  "testing"
  
  pb "github.com/your-org/trader-scanner/pkg/pb"
)

func TestIsBullishPattern(t *testing.T) {
  tests := []struct {
    name     string
    bars     []*pb.Bar
    expected bool
  }{
    {
      name: "Two green bars above rising SMA50",
      bars: createTestBars(50, 2, true, true),  // Helper to create 50+2 bars with last 2 green
      expected: true,
    },
    {
      name: "Two green bars below SMA50",
      bars: createTestBars(50, 2, false, true),  // Last 2 green but below SMA
      expected: false,
    },
    // Add more test cases
  }
  
  for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
      processor := NewProcessor(defaultTestConfig())
      result := processor.isBullishPattern(tt.bars)
      if result != tt.expected {
        t.Errorf("isBullishPattern() = %v, want %v", result, tt.expected)
      }
    })
  }
}

// Similarly, test isBearishPattern and other pattern detection functions
```

## 3. Table-Driven Tests for Signal Generation

Test the complete signal generation pipeline with various input patterns:

```go
func TestScanSymbol(t *testing.T) {
  testCases := []struct {
    name           string
    bars           []*pb.Bar
    ivPercentile   float64
    expectedSignal pb.SignalType
  }{
    {
      name: "Bullish pattern with low IV",
      bars: createBullishBars(),
      ivPercentile: 0.3,
      expectedSignal: pb.SignalType_CALL_DEBIT,
    },
    {
      name: "Bullish pattern with high IV",
      bars: createBullishBars(),
      ivPercentile: 0.9,
      expectedSignal: pb.SignalType_CALL_CREDIT,
    },
    {
      name: "Bearish pattern with low IV",
      bars: createBearishBars(),
      ivPercentile: 0.3,
      expectedSignal: pb.SignalType_PUT_DEBIT,
    },
    {
      name: "Bearish pattern with high IV",
      bars: createBearishBars(),
      ivPercentile: 0.9,
      expectedSignal: pb.SignalType_PUT_CREDIT,
    },
    {
      name: "No pattern",
      bars: createNeutralBars(),
      ivPercentile: 0.5,
      expectedSignal: pb.SignalType_NONE,
    },
  }
  
  for _, tc := range testCases {
    t.Run(tc.name, func(t *testing.T) {
      // Create mock client that returns our test data
      mockClient := &MockMarketDataClient{
        BarsResponse: &pb.BarsResponse{Bars: tc.bars},
        IVResponse: &pb.IVResponse{Percentile: tc.ivPercentile},
      }
      
      processor := NewProcessor(defaultTestConfig(), WithClient(mockClient))
      result, err := processor.ScanSymbol(context.Background(), "TEST")
      
      if err != nil {
        t.Fatalf("Unexpected error: %v", err)
      }
      
      if result.Signal != tc.expectedSignal {
        t.Errorf("Expected signal %v, got %v", tc.expectedSignal, result.Signal)
      }
    })
  }
}
```

## 4. Testing Error Handling

Verify that the scanner handles various error conditions correctly:

```go
func TestScanSymbolErrors(t *testing.T) {
  testCases := []struct {
    name      string
    barsError error
    ivError   error
  }{
    {
      name: "Historical bars error",
      barsError: errors.New("failed to fetch bars"),
      ivError: nil,
    },
    {
      name: "IV percentile error",
      barsError: nil,
      ivError: errors.New("failed to fetch IV"),
    },
    {
      name: "Both services error",
      barsError: errors.New("bars error"),
      ivError: errors.New("IV error"),
    },
  }
  
  for _, tc := range testCases {
    t.Run(tc.name, func(t *testing.T) {
      mockClient := &MockMarketDataClient{
        BarsError: tc.barsError,
        IVError: tc.ivError,
      }
      
      processor := NewProcessor(defaultTestConfig(), WithClient(mockClient))
      result, err := processor.ScanSymbol(context.Background(), "TEST")
      
      if err == nil {
        t.Fatal("Expected error but got nil")
      }
      
      // Check that we get NONE signal on error
      if result.Signal != pb.SignalType_NONE {
        t.Errorf("Expected NONE signal on error, got %v", result.Signal)
      }
    })
  }
}
```

## 5. Concurrency & Timeout Tests

Test that the scanner handles multiple symbols concurrently and respects timeouts:

```go
func TestScanAll(t *testing.T) {
  symbols := []string{"AAPL", "MSFT", "GOOG", "AMZN", "META"}
  
  // Mock client that returns different responses based on symbol
  mockClient := &MockMarketDataClient{
    GetHistoricalBarsFn: func(ctx context.Context, req *pb.BarsRequest) (*pb.BarsResponse, error) {
      switch req.Symbol {
      case "AAPL":
        return &pb.BarsResponse{Bars: createBullishBars()}, nil
      case "MSFT":
        return &pb.BarsResponse{Bars: createBearishBars()}, nil
      case "GOOG":
        // Simulate timeout
        time.Sleep(2 * time.Second)
        return nil, context.DeadlineExceeded
      default:
        return &pb.BarsResponse{Bars: createNeutralBars()}, nil
      }
    },
    GetIVPercentileFn: func(ctx context.Context, req *pb.IVRequest) (*pb.IVResponse, error) {
      return &pb.IVResponse{Percentile: 0.4}, nil
    },
  }
  
  config := &Config{
    ScanTimeout: 1 * time.Second,
    WorkerCount: 3,
    Universe: symbols,
  }
  
  processor := NewProcessor(config, WithClient(mockClient))
  
  // Create context with timeout
  ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
  defer cancel()
  
  results, err := processor.ScanAll(ctx)
  if err != nil {
    t.Fatalf("Unexpected error: %v", err)
  }
  
  // Check that we have the right number of results
  if len(results) != len(symbols) {
    t.Errorf("Expected %d results, got %d", len(symbols), len(results))
  }
  
  // Check that GOOG has NONE signal due to timeout
  for _, r := range results {
    if r.Symbol == "GOOG" && r.Signal != pb.SignalType_NONE {
      t.Errorf("Expected NONE signal for GOOG due to timeout, got %v", r.Signal)
    }
  }
}
```

## 6. Integration Testing with In-Memory gRPC

Test the complete gRPC service using an in-memory connection:

```go
func TestScannerServiceIntegration(t *testing.T) {
  // Create a buffer for in-memory gRPC
  buffer := bufconn.Listen(1024 * 1024)
  
  // Create and start server
  server := grpc.NewServer()
  mockMarketDataClient := createMockMarketDataClient()
  processor := NewProcessor(defaultTestConfig(), WithClient(mockMarketDataClient))
  pb.RegisterScannerServiceServer(server, NewScannerServer(processor))
  
  go func() {
    if err := server.Serve(buffer); err != nil {
      t.Errorf("Failed to serve: %v", err)
    }
  }()
  
  // Create client connection
  conn, err := grpc.DialContext(
    context.Background(),
    "bufnet",
    grpc.WithContextDialer(func(ctx context.Context, s string) (net.Conn, error) {
      return buffer.Dial()
    }),
    grpc.WithInsecure(),
  )
  if err != nil {
    t.Fatalf("Failed to dial bufnet: %v", err)
  }
  defer conn.Close()
  
  // Create client
  client := pb.NewScannerServiceClient(conn)
  
  // Test ScanUniverse RPC
  resp, err := client.ScanUniverse(context.Background(), &pb.ScanRequest{
    Symbols: []string{"AAPL", "MSFT"},
  })
  
  if err != nil {
    t.Fatalf("ScanUniverse failed: %v", err)
  }
  
  if len(resp.Results) != 2 {
    t.Errorf("Expected 2 results, got %d", len(resp.Results))
  }
  
  // Verify results
  for _, result := range resp.Results {
    if result.Symbol != "AAPL" && result.Symbol != "MSFT" {
      t.Errorf("Unexpected symbol in results: %s", result.Symbol)
    }
  }
}
```

## 7. Benchmark Tests

Add benchmarks to measure scanner performance with different universe sizes:

```go
func BenchmarkScanAll(b *testing.B) {
  // Create test data
  mockClient := createBenchmarkMockClient()
  
  // Test different universe sizes
  universes := []struct{
    name string
    size int
  }{
    {"Small", 10},
    {"Medium", 100},
    {"Large", 1000},
  }
  
  for _, u := range universes {
    b.Run(u.name, func(b *testing.B) {
      symbols := make([]string, u.size)
      for i := 0; i < u.size; i++ {
        symbols[i] = fmt.Sprintf("SYM%d", i)
      }
      
      config := defaultTestConfig()
      config.Universe = symbols
      config.WorkerCount = 10
      
      processor := NewProcessor(config, WithClient(mockClient))
      
      // Reset timer before the loop
      b.ResetTimer()
      
      for i := 0; i < b.N; i++ {
        ctx := context.Background()
        _, err := processor.ScanAll(ctx)
        if err != nil {
          b.Fatalf("Error in ScanAll: %v", err)
        }
      }
    })
  }
}
```

## 8. Cucumber Scenarios

```gherkin
Feature: Go Scanner Signal Generation
  Scenario: Bullish Pattern Detection
    Given historical bars with two green candles above rising SMA50
    And IV percentile is 0.3 (below threshold)
    When scanner processes the symbol
    Then a CALL_DEBIT signal is generated

  Scenario: Bearish Pattern with High IV
    Given historical bars with two red candles below falling SMA50
    And IV percentile is 0.9 (above threshold)
    When scanner processes the symbol
    Then a PUT_CREDIT signal is generated

  Scenario: Concurrent Scanning
    Given a universe of 100 symbols
    When ScanAll is called with a 5-second timeout
    Then all symbols are processed within the timeout
    And signals are generated for matching patterns only

  Scenario: Error Handling
    Given the market data service returns errors
    When scanner processes a symbol
    Then a NONE signal is returned
    And the error is logged
```

## 9. Implementation Strategy

1. **Start with unit tests** for pattern detection functions
2. **Implement mock client** for MarketDataService
3. **Write table-driven tests** for different signal scenarios
4. **Add concurrency tests** with worker pool pattern
5. **Create integration tests** with in-memory gRPC
6. **Add benchmarks** to measure performance with different universe sizes

## 10. Testing Tools

- **testing package**: Standard Go testing framework
- **testify/assert**: For cleaner assertions (optional)
- **bufconn**: For in-memory gRPC testing
- **go-cmp**: For deep equality comparison

## 11. Test Command Examples

```bash
# Run all tests
go test ./pkg/scan/... -v

# Run specific test
go test ./pkg/scan -run TestScanSymbol

# Run benchmarks
go test -bench=BenchmarkScanAll -benchmem ./pkg/scan/...

# Generate coverage report
go test -coverprofile=coverage.out ./pkg/scan/...
go tool cover -html=coverage.out
```
