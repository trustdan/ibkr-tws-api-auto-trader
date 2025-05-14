package client

import (
	"context"

	"github.com/user/trader-scanner/pkg/models"
)

// MarketDataClient defines the interface for retrieving market data
// This will eventually be implemented with gRPC calls to the Python orchestrator
type MarketDataClient interface {
	// GetHistoricalBars retrieves historical price bars for a symbol
	GetHistoricalBars(ctx context.Context, symbol string, days int) ([]models.Bar, error)

	// GetIVPercentile retrieves the implied volatility percentile for a symbol
	GetIVPercentile(ctx context.Context, symbol string) (float64, error)
}

// MockMarketDataClient provides a testing implementation of MarketDataClient
type MockMarketDataClient struct {
	MockBars        map[string][]models.Bar
	MockIVs         map[string]float64
	ShouldFail      bool
	SimulateTimeout bool
}

// NewMockClient creates a new mock client for testing
func NewMockClient() *MockMarketDataClient {
	return &MockMarketDataClient{
		MockBars: make(map[string][]models.Bar),
		MockIVs:  make(map[string]float64),
	}
}

// GetHistoricalBars implements the MarketDataClient interface for testing
func (m *MockMarketDataClient) GetHistoricalBars(ctx context.Context, symbol string, days int) ([]models.Bar, error) {
	if m.ShouldFail {
		return nil, ErrServiceUnavailable
	}

	if m.SimulateTimeout {
		<-ctx.Done() // Wait for context to expire
		return nil, ctx.Err()
	}

	if bars, ok := m.MockBars[symbol]; ok {
		return bars, nil
	}

	// Return empty bars if not mocked
	return []models.Bar{}, nil
}

// GetIVPercentile implements the MarketDataClient interface for testing
func (m *MockMarketDataClient) GetIVPercentile(ctx context.Context, symbol string) (float64, error) {
	if m.ShouldFail {
		return 0, ErrServiceUnavailable
	}

	if m.SimulateTimeout {
		<-ctx.Done()
		return 0, ctx.Err()
	}

	if iv, ok := m.MockIVs[symbol]; ok {
		return iv, nil
	}

	// Default IV percentile
	return 0.5, nil
}

// Common errors
var (
	ErrServiceUnavailable = NewError("service unavailable", "market data service is unavailable")
)

// Error represents an error with a code and message
type Error struct {
	Code    string
	Message string
}

// NewError creates a new error with code and message
func NewError(code, message string) *Error {
	return &Error{
		Code:    code,
		Message: message,
	}
}

func (e *Error) Error() string {
	return e.Message
}
