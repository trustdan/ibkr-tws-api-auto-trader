# 04-mocking-and-tests.md

## 1. Overview

This module defines testing strategies for the Go Scanner service. We’ll cover:

* **Unit Testing** with mocked `MarketDataClient` to simulate bar and IV responses.
* **Table-Driven Tests** for `scanSymbol` logic: bullish, bearish, high-IV, and timeout scenarios.
* **Concurrency & Integration Tests**: verify `ScanAll` handles multiple symbols, respects timeouts, and aggregates results correctly.

By isolating external dependencies with mocks, we ensure fast, reliable, and deterministic tests.

## 2. Unit Testing with Mocks

### Fake gRPC Client

Implement a fake `pb.MarketDataClient` in `pkg/scan/fake_client.go`:

```go
package scan

import (
  "context"
  pb "github.com/your-org/trader-scanner/pkg/pb"
)

type FakeMarketDataClient struct {
  BarsResp *pb.BarsResponse
  IVResp   *pb.IVResponse
  Err      error
}

func (f *FakeMarketDataClient) GetHistoricalBars(ctx context.Context, req *pb.BarsRequest) (*pb.BarsResponse, error) {
  return f.BarsResp, f.Err
}

func (f *FakeMarketDataClient) GetIVPercentile(ctx context.Context, req *pb.IVRequest) (*pb.IVResponse, error) {
  return f.IVResp, f.Err
}
```

### Table-Driven Tests

Create `pkg/scan/processor_test.go`:

```go
func TestScanSymbolPatterns(t *testing.T) {
  cfg := &config.Config{SMA50Period:50, CandleCount:2, IVThreshold:0.8, Universe:[]string{"X"}}
  bars := &pb.BarsResponse{Bars: []*pb.Bar{
    // Construct 52 bars: first 50 any, then two green above SMA
    // ... fill in simplified test data ...
  }}
  cases := []struct {
    name     string
    ivPct    float64
    expected pb.SignalType
  }{
    {"BullishDebit", 0.5, pb.SignalType_CALL_DEBIT},
    {"BearishDebit", 0.3, pb.SignalType_PUT_DEBIT},
    {"CallCredit",    0.9, pb.SignalType_CALL_CREDIT},
    {"None",          0.2, pb.SignalType_NONE},
  }
  for _, c := range cases {
    t.Run(c.name, func(t *testing.T) {
      fake := &FakeMarketDataClient{BarsResp: bars, IVResp: &pb.IVResponse{Percentile:c.ivPct}}
      proc := NewProcessor(cfg, fake)
      res := proc.scanSymbol(context.Background(), "X")
      if res.SignalType != c.expected.String() {
        t.Errorf("got %v, want %v", res.SignalType, c.expected)
      }
    })
  }
}
```

## 3. Concurrency & Timeout Tests

Verify that slow responses yield `NONE` and do not block others:

```go
func TestScanAllTimeout(t *testing.T) {
  cfg := &config.Config{...Universe:[]string{"A","B"}}
  slowClient := &SlowClient{delay:10*time.Second}
  proc := NewProcessor(cfg, slowClient)
  results, _ := proc.ScanAll(context.Background())
  for _, r := range results {
    if r.SignalType != "NONE" {
      t.Errorf("expected NONE on timeout, got %v", r.SignalType)
    }
  }
}
```

## 4. Integration Tests

* Spin up a local Python orchestrator (in test harness) and Go scanner in-process.
* Use `httptest` or `bufconn` to create an in-memory gRPC server.
* Call `ScanUniverse` RPC and assert non-empty response structure.

## 5. Cucumber Scenarios

```gherkin
Feature: Scanner Unit and Concurrency Tests
  Scenario: Mocked bullish pattern returns CALL_DEBIT
    Given the fake client returns two green bars and iv_percentile=0.5
    When scanSymbol is invoked
    Then SignalType == CALL_DEBIT

  Scenario: Slow client times out
    Given the client delays response > timeout
    When ScanAll executes
    Then result.SignalType == NONE for each symbol
```

## 6. Pseudocode Outline

```text
# In Go test files
fakeClient := &FakeMarketDataClient{...}
proc := NewProcessor(cfg, fakeClient)
res := proc.scanSymbol(ctx, "SYM")
assert res.SignalType == "CALL_DEBIT"
```
