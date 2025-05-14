package grpc

import (
	"context"
	"testing"
	"time"

	"github.com/user/trader-scanner/pkg/client"
	"github.com/user/trader-scanner/pkg/config"
	"github.com/user/trader-scanner/pkg/pb"
	"github.com/user/trader-scanner/pkg/scan"
)

func TestScannerServer_ScanUniverse(t *testing.T) {
	// Create a mock client for market data
	mockClient := client.NewMockClient()

	// Create a test configuration
	cfg := &config.Config{
		SMA50Period:   50,
		CandleCount:   2,
		IVThreshold:   0.8,
		MinRewardRisk: 1.0,
		Universe:      []string{"AAPL", "MSFT", "SPY"},
	}

	// Create a processor with the mock client
	processor := scan.NewProcessor(cfg, mockClient)

	// Create a scanner server
	server := NewScannerServer(processor)

	// Test cases
	tests := []struct {
		name    string
		request *pb.ScanRequest
		wantErr bool
	}{
		{
			name: "Default universe",
			request: &pb.ScanRequest{
				Symbols: []string{},
			},
			wantErr: false,
		},
		{
			name: "Custom symbols",
			request: &pb.ScanRequest{
				Symbols: []string{"GOOG", "AMZN"},
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a context with timeout
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()

			// Call the ScanUniverse method
			resp, err := server.ScanUniverse(ctx, tt.request)

			// Check for errors if expected
			if (err != nil) != tt.wantErr {
				t.Errorf("ScanUniverse() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			// Verify response is not nil if no error expected
			if !tt.wantErr && resp == nil {
				t.Error("ScanUniverse() returned nil response but no error")
				return
			}

			// Check the symbols in the response
			if len(tt.request.Symbols) > 0 {
				// If request specified symbols, the universe should have been temporarily overridden
				// Verify that the original universe was restored
				if len(processor.Config.Universe) != len(cfg.Universe) {
					t.Errorf("Universe was not restored, got %v, want %v", processor.Config.Universe, cfg.Universe)
				}
			}
		})
	}
}
