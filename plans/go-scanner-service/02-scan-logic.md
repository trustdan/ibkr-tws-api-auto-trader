# 02-scan-logic.md

## 1. Overview

The Scanner Logic module implements the core pattern-detection engine in Go.  It consumes historical bar data and IV metrics (fetched via Python orchestrator over gRPC or HTTP) and applies your vertical-spread entry rules concurrently across a universe of symbols.  Key responsibilities:

* **Concurrent Scanning:** Use goroutines and a worker pool to scan many symbols in parallel without overwhelming resources
* **Pattern Evaluation:** For each symbol, retrieve N-day bars, compute SMA50, check 2-candle pattern above/below SMA, and fetch IV percentile
* **Signal Aggregation:** Emit a structured list of scan results (e.g., `{Symbol, SignalType}`) for downstream processing
* **Backpressure & Timeouts:** Enforce per-symbol timeouts and limit concurrency to avoid backlogging

## 2. Implementation

Implement in `pkg/scan/processor.go`:

```go
package scan

import (
  "context"
  "sync"
  "time"

  "github.com/your-org/trader-scanner/pkg/config"
  pb "github.com/your-org/trader-proto" // generated gRPC stubs
)

// Processor handles scanning logic
type Processor struct {
  cfg       *config.Config
  client    pb.MarketDataClient // gRPC client to Python orchestrator
  timeout   time.Duration
  maxWorker int
}

// NewProcessor creates a Processor
func NewProcessor(cfg *config.Config, client pb.MarketDataClient) *Processor {
  return &Processor{
    cfg:       cfg,
    client:    client,
    timeout:   5 * time.Second,
    maxWorker: 10,  // configurable
  }
}

// ScanResult holds the outcome for one symbol
type ScanResult struct {
  Symbol     string
  SignalType string // "CALL_DEBIT", "PUT_DEBIT", "CALL_CREDIT", "PUT_CREDIT", or "NONE"
}

// ScanAll performs a full scan of the configured universe
func (p *Processor) ScanAll(ctx context.Context) ([]ScanResult, error) {
  ctx, cancel := context.WithCancel(ctx)
  defer cancel()

  in := make(chan string)
  out := make(chan ScanResult)
  var wg sync.WaitGroup

  // Launch workers
  for i := 0; i < p.maxWorker; i++ {
    wg.Add(1)
    go func() {
      defer wg.Done()
      for sym := range in {
        res := p.scanSymbol(ctx, sym)
        select {
        case out <- res:
        case <-ctx.Done():
          return
        }
      }
    }()
  }

  // Feed symbols
  go func() {
    for _, sym := range p.cfg.Universe {
      in <- sym
    }
    close(in)
  }()

  // Collect results
  go func() {
    wg.Wait()
    close(out)
  }()

  results := make([]ScanResult, 0, len(p.cfg.Universe))
  for r := range out {
    results = append(results, r)
  }

  return results, nil
}

// scanSymbol fetches data and evaluates patterns
func (p *Processor) scanSymbol(ctx context.Context, symbol string) ScanResult {
  cctx, cancel := context.WithTimeout(ctx, p.timeout)
  defer cancel()

  // 1. Historical bars request
  barsReq := &pb.BarsRequest{Symbol: symbol, Days: int32(p.cfg.SMA50Period + p.cfg.CandleCount)}
  barsResp, err := p.client.GetHistoricalBars(cctx, barsReq)
  if err != nil {
    return ScanResult{Symbol: symbol, SignalType: "NONE"}
  }

  // 2. IV percentile request
  ivReq := &pb.IVRequest{Symbol: symbol}
  ivResp, err := p.client.GetIVPercentile(cctx, ivReq)
  if err != nil {
    return ScanResult{Symbol: symbol, SignalType: "NONE"}
  }

  // 3. Pattern evaluation (reuse Python logic via proto, or re-implement in Go)
  signal := evaluatePattern(barsResp.Bars, ivResp.Percentile, p.cfg)
  return ScanResult{Symbol: symbol, SignalType: signal}
}
```

**Key Implementation Notes:**

* **Worker Pool:** `maxWorker` controls concurrency; adjust based on CPU/RAM
* **Context & Timeouts:** Use `context.WithTimeout` to bound each symbol scan
* **gRPC Client:** Communicates with Python orchestrator for data-intensive tasks
* **evaluatePattern:** Can be a Go port of Python’s strategy logic or a direct gRPC call

## 3. Testing & Validation

* **Unit Tests:** Mock `pb.MarketDataClient` with a fake implementation returning synthetic bars and IV; assert `scanSymbol` returns correct `SignalType` for various patterns
* **Integration Tests:** Run against a live Python orchestrator service; measure end-to-end latency and correctness for a small universe
* **Concurrency Tests:** Ensure `ScanAll` handles slow symbol responses without blocking faster ones

## 4. Cucumber Scenarios

```gherkin
Feature: Scanner Pattern Detection
  Background:
    Given a fake gRPC MarketDataClient
    And config.Universe contains ["A","B"]

  Scenario: Detect bullish call debit
    Given GetHistoricalBars returns two green bars above SMA50 for "A"
    And GetIVPercentile returns 0.5
    When ScanAll executes
    Then result for "A" has SignalType == "CALL_DEBIT"

  Scenario: Timeout on slow response
    Given GetHistoricalBars sleeps longer than timeout
    When ScanAll executes
    Then result for that symbol is SignalType == "NONE"
```

## 5. Pseudocode Outline

```text
// main.go or test
client = NewFakeMarketDataClient()
proc = NewProcessor(cfg, client)
results = proc.ScanAll(context.Background())
for r in results {
  print(r.Symbol, r.SignalType)
}
```
