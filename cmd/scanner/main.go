package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/user/trader-scanner/pkg/client"
	"github.com/user/trader-scanner/pkg/config"
	"github.com/user/trader-scanner/pkg/grpc"
	"github.com/user/trader-scanner/pkg/scan"
)

func main() {
	// Define command-line flags
	configPath := flag.String("config", "config.json", "Path to configuration file")
	workers := flag.Int("workers", 10, "Maximum concurrent workers")
	timeout := flag.Duration("timeout", 5*time.Second, "Timeout per symbol")
	scanInterval := flag.Duration("interval", 10*time.Second, "Scan interval")
	grpcAddr := flag.String("grpc", ":50051", "gRPC server address")
	pythonAddr := flag.String("python", "localhost:50052", "Python orchestrator gRPC address")
	flag.Parse()

	// Load configuration
	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Printf("Failed to load config from %s: %v", *configPath, err)
		log.Println("Using default configuration...")
		cfg = config.DefaultConfig()
	}

	// Create context that can be cancelled
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Initialize market data client
	// In production, this would connect to the Python orchestrator
	// For development/testing, we use the mock client
	var mdClient client.MarketDataClient
	useGRPC := false // Set to true to use gRPC client instead of mock

	if useGRPC {
		grpcClient, err := client.NewGRPCClient(*pythonAddr)
		if err != nil {
			log.Fatalf("Failed to connect to Python orchestrator: %v", err)
		}
		defer grpcClient.Close()
		mdClient = grpcClient
		log.Printf("Connected to Python orchestrator at %s", *pythonAddr)
	} else {
		mdClient = createMockClient()
		log.Println("Using mock market data client")
	}

	// Initialize processor
	proc := scan.NewProcessor(cfg, mdClient).
		WithMaxWorkers(*workers).
		WithTimeout(*timeout)

	log.Println("Starting scanner service...")

	// Start gRPC server
	server, err := grpc.StartServer(*grpcAddr, proc)
	if err != nil {
		log.Fatalf("Failed to start gRPC server: %v", err)
	}
	defer server.Stop()

	// Set up a channel to listen for termination signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Run a scan immediately
	log.Println("Running initial scan...")
	results, err := proc.ScanAll(ctx)
	if err != nil {
		log.Fatalf("Initial scan failed: %v", err)
	}

	for _, result := range results {
		log.Printf("Found: %s with signal: %s", result.Symbol, result.SignalType)
	}

	// Set up ticker for periodic scanning
	ticker := time.NewTicker(*scanInterval)
	defer ticker.Stop()

	// Main service loop
	log.Println("Service running, press Ctrl+C to stop")
	running := true
	for running {
		select {
		case <-ticker.C:
			log.Println("Running periodic scan...")
			results, err := proc.ScanAll(ctx)
			if err != nil {
				log.Printf("Scan error: %v", err)
				continue
			}

			if len(results) > 0 {
				log.Printf("Found %d signals:", len(results))
				for _, result := range results {
					log.Printf("  %s: %s", result.Symbol, result.SignalType)
				}
			} else {
				log.Println("No signals found")
			}

		case sig := <-sigChan:
			log.Printf("Received signal: %v", sig)
			running = false
			cancel()
		}
	}

	log.Println("Scanner service shutting down...")
}

// createMockClient creates a mock market data client for testing
func createMockClient() *client.MockMarketDataClient {
	mock := client.NewMockClient()

	// Setup mock data for testing pattern detection
	setupMockData(mock)

	return mock
}
