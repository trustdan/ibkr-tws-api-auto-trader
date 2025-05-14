# 03-grpc-interface.md

## 1. Overview

This document defines the gRPC contract between the Go Scanner service and the Python Orchestrator (Market Data provider).  We establish Protobuf messages and service methods for:

* **GetHistoricalBars**: request N-day daily bars for a symbol
* **GetIVPercentile**: request IV percentile for a symbol
* **ScanResult**: return symbol + signal type

A well-defined interface decouples data retrieval (Python) from scanning logic (Go) and enables language-agnostic microservices.

## 2. Protobuf Definitions

Create `proto/trader.proto`:

```protobuf
syntax = "proto3";
package trader;

enum SignalType {
  NONE = 0;
  CALL_DEBIT = 1;
  PUT_DEBIT = 2;
  CALL_CREDIT = 3;
  PUT_CREDIT = 4;
}

message BarsRequest {
  string symbol = 1;
  int32 days = 2;
}

message Bar {
  string date = 1;      // YYYY-MM-DD
  double open = 2;
  double high = 3;
  double low = 4;
  double close = 5;
  double volume = 6;
}

message BarsResponse {
  repeated Bar bars = 1;
}

message IVRequest {
  string symbol = 1;
}

message IVResponse {
  double percentile = 1;  // 0.0–1.0
}

message ScanRequest {
  repeated string symbols = 1;
}

message ScanResponse {
  message Result { string symbol = 1; SignalType signal = 2; }
  repeated Result results = 1;
}

service MarketDataService {
  rpc GetHistoricalBars(BarsRequest) returns (BarsResponse);
  rpc GetIVPercentile(IVRequest) returns (IVResponse);
}

service ScannerService {
  rpc ScanUniverse(ScanRequest) returns (ScanResponse);
}
```

## 3. Code Generation

### Generate stubs

```bash
protoc --go_out=./pkg/pb --go-grpc_out=./pkg/pb proto/trader.proto
```

* `pkg/pb/trader.pb.go` and `trader_grpc.pb.go` will be created for Go
* Python orchestrator uses `grpc_tools.protoc` to generate Python stubs in `src/brokers/pb`

## 4. Go Server Implementation

Implement ScannerService in `cmd/scanner/server.go`:

```go
// after imports...

type scannerServer struct {
  pb.UnimplementedScannerServiceServer
  processor *scan.Processor
}

func (s *scannerServer) ScanUniverse(ctx context.Context, req *pb.ScanRequest) (*pb.ScanResponse, error) {
  // override universe if req symbols provided
  symbols := req.Symbols
  if len(symbols) == 0 {
    symbols = s.processor.Config.Universe
  }
  // reuse ScanAll logic by temporarily setting universe
  s.processor.Config.Universe = symbols
  results, _ := s.processor.ScanAll(ctx)

  resp := &pb.ScanResponse{}
  for _, r := range results {
    resp.Results = append(resp.Results, &pb.ScanResponse_Result{
      Symbol: r.Symbol,
      Signal: pb.SignalType(pb.SignalType_value[r.SignalType]),
    })
  }
  return resp, nil
}
```

## 5. Python Client Implementation

Generate Python stubs and implement MarketDataService server in `src/brokers/grpc_server.py`, e.g.:

```python
class MarketDataServiceServicer(pb2_grpc.MarketDataServiceServicer):
    def GetHistoricalBars(self, request, context):
        df = fetcher.get_historical_bars(request.symbol, days=request.days)
        bars = [pb2.Bar(date=row.date, open=row.open, high=row.high,
                        low=row.low, close=row.close, volume=row.volume)
                for row in df.itertuples()]
        return pb2.BarsResponse(bars=bars)

    def GetIVPercentile(self, request, context):
        pct = fetcher.get_iv_percentile(request.symbol)
        return pb2.IVResponse(percentile=pct)
```

## 6. Testing & Validation

* **Schema validation**: Ensure proto compiles without errors
* **Unit Tests**: Mock gRPC client/server to verify correct marshaling of Bars and IV messages
* **Integration Test**: Start both Go and Python servers locally; call `ScanUniverse` via a gRPC client and verify shape of `ScanResponse`

## 7. Cucumber Scenarios

```gherkin
Feature: gRPC Interface Contract
  Scenario: Historical Bars RPC
    Given MarketDataService is running
    When client calls GetHistoricalBars(symbol="AAPL", days=5)
    Then a BarsResponse with 5 Bar entries is returned

  Scenario: IV Percentile RPC
    Given MarketDataService is running
    When client calls GetIVPercentile(symbol="SPY")
    Then IVResponse.percentile is between 0.0 and 1.0

  Scenario: ScannerService RPC
    Given ScannerService is running
    When client calls ScanUniverse(symbols=["AAPL","MSFT"])
    Then ScanResponse contains two results with valid SignalType
```

## 8. Pseudocode Outline

```text
# Go client example
conn = grpc.Dial(url)
client := pb.NewMarketDataServiceClient(conn)
barsResp, _ := client.GetHistoricalBars(ctx, &pb.BarsRequest{"AAPL", 10})
# Python server example
server = grpc.server(futures.ThreadPoolExecutor())
pb2_grpc.add_MarketDataServiceServicer_to_server(servicer, server)
server.add_insecure_port('[::]:50051')
server.start()
```
