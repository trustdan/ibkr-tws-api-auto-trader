# 05-metrics-and-logging.md

## 1. Overview

This module adds observability to the Go Scanner service via Prometheus metrics and structured logging.  Proper instrumentation allows us to monitor scan performance, detect anomalies, and troubleshoot issues in production.

Key goals:

* **Prometheus Metrics**: expose `scan_duration_seconds` histogram, `scan_requests_total` counter, and `scan_results_total` counter labeled by `signal_type`.
* **Structured Logging**: use a logging library (e.g., `logrus` or `zap`) to emit JSON logs with context fields (`symbol`, `duration`, `signal_type`, `error`).
* **Metrics Endpoint**: serve `/metrics` HTTP endpoint for Prometheus scraping.

## 2. Implementation

### 2.1. Add Dependencies

In `go.mod`:

```go
go get github.com/prometheus/client_golang/prometheus
go get github.com/prometheus/client_golang/prometheus/promhttp
go get github.com/sirupsen/logrus  # or go.uber.org/zap
```

### 2.2. Define Metrics

Create `pkg/scan/metrics.go`:

```go
package scan

import (
  "github.com/prometheus/client_golang/prometheus"
)

var (
  ScanRequests = prometheus.NewCounter(
    prometheus.CounterOpts{Name: "scan_requests_total", Help: "Total number of scan requests"})
  ScanDuration = prometheus.NewHistogram(
    prometheus.HistogramOpts{Name: "scan_duration_seconds", Help: "Duration of scanSymbol calls"})
  ScanResults = prometheus.NewCounterVec(
    prometheus.CounterOpts{Name: "scan_results_total", Help: "Number of results by signal type"},
    []string{"signal_type"},
  )
)

func init() {
  prometheus.MustRegister(ScanRequests, ScanDuration, ScanResults)
}
```

### 2.3. Instrument Processor

In `processor.go`, wrap `scanSymbol` logic:

```go
func (p *Processor) scanSymbol(ctx context.Context, symbol string) ScanResult {
  start := time.Now()
  ScanRequests.Inc()
  result := ScanResult{Symbol: symbol, SignalType: "NONE"}

  // existing logic...
  result = evaluatePattern(...)

  duration := time.Since(start).Seconds()
  ScanDuration.Observe(duration)
  ScanResults.WithLabelValues(result.SignalType).Inc()

  log.WithFields(log.Fields{
    "symbol":      symbol,
    "signal_type": result.SignalType,
    "duration":    duration,
  }).Info("Completed scanSymbol")

  return result
}
```

### 2.4. Expose HTTP Endpoint

In `cmd/scanner/main.go`, add:

```go
import (
  "net/http"
  "github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
  // existing setup...
  http.Handle("/metrics", promhttp.Handler())
  go http.ListenAndServe(":2112", nil)
  // start scanner loop
}
```

## 3. Testing & Validation

* **Unit Test Metrics Registration**: verify `prometheus.DefaultRegisterer` contains our metrics.
* **Integration Test**: run the scanner service, HTTP GET `http://localhost:2112/metrics`, assert presence of `scan_requests_total` and other metrics.

## 4. Cucumber Scenarios

```gherkin
Feature: Metrics and Logging
  Scenario: Metrics endpoint returns expected metrics
    Given the scanner service is running
    When I GET "/metrics"
    Then the response contains "scan_requests_total"

  Scenario: scanSymbol increments counters and logs fields
    Given a fake symbol scan
    When scanSymbol is called
    Then ScanRequests and ScanDuration metrics increase
    And a log entry with "symbol" and "signal_type" is emitted
```

## 5. Pseudocode Outline

```text
# In Go scanner startup:
http.Handle("/metrics", promhttp.Handler())
start HTTP server on :2112

# In scanSymbol:
ScanRequests.Inc()
startTimer := time.Now()
...logic...
ScanDuration.Observe(time.Since(startTimer).Seconds())
ScanResults.WithLabelValues(signal).Inc()
logrus.WithFields(...).Info("Completed scanSymbol")
```
