# 01-go-scanner-setup.md

## 1. Overview

This document describes how to scaffold and initialize the Go-based Market Scanner service.  The scanner will read a configuration (SMA period, candle-count rules, IV thresholds) and provide a concurrent API for symbol universe scans.  We’ll set up module structure, dependency management, config loading, and a basic main loop stub.

**Key goals:**

* Initialize a Go module (`go.mod`) and directory layout
* Define a `Config` struct to mirror our Python `config.yaml` strategy settings
* Implement JSON- or Viper-based config loading
* Provide a placeholder `Processor` that can later implement the scanning logic in `pkg/scan`

## 2. Project Structure

```plaintext
trader-scanner/           # root of scanner service
├── cmd/                  # CLI entrypoints
│   └── scanner/          # main application
│       └── main.go       # application bootstrap
├── pkg/                  # reusable packages
│   ├── config/           # configuration loading
│   │   └── config.go     # Config struct & loader
│   └── scan/             # core scanning logic
│       └── processor.go  # Processor stub
├── config.json           # sample JSON config file
└── go.mod                # Go module file
```

## 3. Dependencies

Use the standard library plus:

* [spf13/viper](https://github.com/spf13/viper) (optional) for flexible config
* `google.golang.org/grpc` for future gRPC interface

Initialize module:

```bash
cd trader-scanner
go mod init github.com/your-org/trader-scanner
go get github.com/spf13/viper
go get google.golang.org/grpc
```

## 4. Configuration (`config.json`)

Provide a JSON config matching Python values:

```json
{
  "sma50_period": 50,
  "candle_count": 2,
  "iv_threshold": 0.8,
  "min_reward_risk": 1.0,
  "universe": ["AAPL","MSFT","SPY"]
}
```

Implement loader in `pkg/config/config.go`:

```go
package config

import (
  "encoding/json"
  "os"
)

type Config struct {
  SMA50Period     int      `json:"sma50_period"`
  CandleCount     int      `json:"candle_count"`
  IVThreshold     float64  `json:"iv_threshold"`
  MinRewardRisk   float64  `json:"min_reward_risk"`
  Universe        []string `json:"universe"`
}

func Load(path string) (*Config, error) {
  f, err := os.Open(path)
  if err != nil {
    return nil, err
  }
  defer f.Close()
  var cfg Config
  if err := json.NewDecoder(f).Decode(&cfg); err != nil {
    return nil, err
  }
  return &cfg, nil
}
```

## 5. Main Application Stub (`cmd/scanner/main.go`)

```go
package main

import (
  "log"
  "time"

  "github.com/your-org/trader-scanner/pkg/config"
  "github.com/your-org/trader-scanner/pkg/scan"
)

func main() {
  cfg, err := config.Load("config.json")
  if err != nil {
    log.Fatalf("Failed to load config: %v", err)
  }

  // Initialize processor
  proc := scan.NewProcessor(cfg)
  log.Println("Starting scanner service...")

  // Placeholder: run a single scan and exit
  symbols := proc.ScanAll()
  log.Printf("Scan results: %v", symbols)

  // Future: loop with ticker
  time.Sleep(1 * time.Second)
}
```

## 6. Cucumber Scenarios

```gherkin
Feature: Scanner Service Bootstrap
  Scenario: Load configuration
    Given a valid config.json file
    When the scanner service starts
    Then Load("config.json") returns a Config with SMA50Period == 50

  Scenario: Processor stub execution
    Given the scanner service is initialized
    When I call ScanAll()
    Then it returns a slice of strings (possibly empty)
```

## 7. Pseudocode Outline

```text
# main.go
cfg = config.Load("config.json")
proc = NewProcessor(cfg)
symbols = proc.ScanAll()
log.Print(symbols)
```
