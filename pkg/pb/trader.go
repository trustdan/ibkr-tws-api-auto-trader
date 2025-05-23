// Package pb contains mock implementations of what would be generated by protoc
// In a production environment, this would be generated from the protobuf definitions
package pb

import (
	"context"
)

// SignalType represents the type of trading signal
type SignalType int32

const (
	// Signal types
	SignalType_NONE        SignalType = 0
	SignalType_CALL_DEBIT  SignalType = 1
	SignalType_PUT_DEBIT   SignalType = 2
	SignalType_CALL_CREDIT SignalType = 3
	SignalType_PUT_CREDIT  SignalType = 4
)

// Bar represents a single price bar/candle
type Bar struct {
	Date   string // YYYY-MM-DD
	Open   float64
	High   float64
	Low    float64
	Close  float64
	Volume float64
}

// BarsRequest is the request for historical bars
type BarsRequest struct {
	Symbol string
	Days   int32
}

// BarsResponse is the response containing historical bars
type BarsResponse struct {
	Bars []*Bar
}

// IVRequest is the request for implied volatility percentile
type IVRequest struct {
	Symbol string
}

// IVResponse is the response containing implied volatility percentile
type IVResponse struct {
	Percentile float64
}

// ScanRequest is the request for scanning symbols
type ScanRequest struct {
	Symbols []string
}

// ScanResponse_Result represents an individual scan result
type ScanResponse_Result struct {
	Symbol string
	Signal SignalType
}

// ScanResponse is the response containing scan results
type ScanResponse struct {
	Results []*ScanResponse_Result
}

// MarketDataServiceClient is the client API for MarketDataService
type MarketDataServiceClient interface {
	GetHistoricalBars(ctx context.Context, in *BarsRequest) (*BarsResponse, error)
	GetIVPercentile(ctx context.Context, in *IVRequest) (*IVResponse, error)
}

// MarketDataServiceServer is the server API for MarketDataService
type MarketDataServiceServer interface {
	GetHistoricalBars(context.Context, *BarsRequest) (*BarsResponse, error)
	GetIVPercentile(context.Context, *IVRequest) (*IVResponse, error)
}

// ScannerServiceClient is the client API for ScannerService
type ScannerServiceClient interface {
	ScanUniverse(ctx context.Context, in *ScanRequest) (*ScanResponse, error)
}

// ScannerServiceServer is the server API for ScannerService
type ScannerServiceServer interface {
	ScanUniverse(context.Context, *ScanRequest) (*ScanResponse, error)
}

// UnimplementedScannerServiceServer provides a base implementation
type UnimplementedScannerServiceServer struct{}

// ScanUniverse implementation
func (UnimplementedScannerServiceServer) ScanUniverse(context.Context, *ScanRequest) (*ScanResponse, error) {
	return nil, nil
}

// RegisterScannerServiceServer registers the server with the gRPC framework
func RegisterScannerServiceServer(s interface{}, srv ScannerServiceServer) {
	// This would normally register with the gRPC server
	// But we're just mocking the interface for now
}
