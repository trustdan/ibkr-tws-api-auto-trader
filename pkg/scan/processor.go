package scan

import (
	"context"
	"log"
	"sync"
	"time"

	"github.com/user/trader-scanner/pkg/client"
	"github.com/user/trader-scanner/pkg/config"
)

// Processor handles the scanning logic for stock symbols
type Processor struct {
	Config      *config.Config
	Client      client.MarketDataClient
	MaxWorkers  int
	ScanTimeout time.Duration
}

// NewProcessor creates a new scanner processor with the provided configuration
func NewProcessor(cfg *config.Config, client client.MarketDataClient) *Processor {
	return &Processor{
		Config:      cfg,
		Client:      client,
		MaxWorkers:  10,              // Default concurrency level
		ScanTimeout: 5 * time.Second, // Default timeout per symbol
	}
}

// WithMaxWorkers sets the maximum number of concurrent workers
func (p *Processor) WithMaxWorkers(workers int) *Processor {
	p.MaxWorkers = workers
	return p
}

// WithTimeout sets the timeout for each symbol scan
func (p *Processor) WithTimeout(timeout time.Duration) *Processor {
	p.ScanTimeout = timeout
	return p
}

// ScanAll processes all symbols in the universe concurrently and returns those that match criteria
func (p *Processor) ScanAll(ctx context.Context) ([]Result, error) {
	log.Printf("Scanning %d symbols with SMA50 period: %d, CandleCount: %d",
		len(p.Config.Universe), p.Config.SMA50Period, p.Config.CandleCount)

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Create channels for work distribution and result collection
	symbolChan := make(chan string, len(p.Config.Universe))
	resultChan := make(chan Result, len(p.Config.Universe))

	// Create wait group to track worker completion
	var wg sync.WaitGroup

	// Start workers
	workerCount := min(p.MaxWorkers, len(p.Config.Universe))
	log.Printf("Starting %d workers", workerCount)

	for i := 0; i < workerCount; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for symbol := range symbolChan {
				result := p.scanSymbol(ctx, symbol)
				select {
				case resultChan <- result:
					// Result sent successfully
				case <-ctx.Done():
					// Context cancelled
					return
				}
			}
		}(i)
	}

	// Send symbols to workers
	go func() {
		for _, symbol := range p.Config.Universe {
			select {
			case symbolChan <- symbol:
				// Symbol sent successfully
			case <-ctx.Done():
				// Context cancelled
				break
			}
		}
		close(symbolChan) // Close channel when all symbols are sent
	}()

	// Collect results
	go func() {
		wg.Wait()
		close(resultChan) // Close channel when all workers are done
	}()

	// Gather all results
	results := make([]Result, 0, len(p.Config.Universe))
	for result := range resultChan {
		if result.SignalType != SignalNone {
			results = append(results, result)
		}
	}

	log.Printf("Scan complete. Found %d matches", len(results))
	return results, nil
}

// scanSymbol processes a single symbol and returns a Result
func (p *Processor) scanSymbol(ctx context.Context, symbol string) Result {
	log.Printf("Processing symbol: %s", symbol)

	// Create context with timeout for this symbol
	symCtx, cancel := context.WithTimeout(ctx, p.ScanTimeout)
	defer cancel()

	// Get historical bars
	bars, err := p.Client.GetHistoricalBars(symCtx, symbol, p.Config.SMA50Period+p.Config.CandleCount)
	if err != nil {
		log.Printf("Error fetching bars for %s: %v", symbol, err)
		return Result{Symbol: symbol, SignalType: SignalNone}
	}

	// Get IV percentile
	ivPercentile, err := p.Client.GetIVPercentile(symCtx, symbol)
	if err != nil {
		log.Printf("Error fetching IV for %s: %v", symbol, err)
		return Result{Symbol: symbol, SignalType: SignalNone}
	}

	// Evaluate pattern
	signalType := EvaluatePattern(bars, ivPercentile, p.Config)

	// Return the result
	return Result{Symbol: symbol, SignalType: signalType}
}

// Result represents a single scan result with the symbol and signal type
type Result struct {
	Symbol     string
	SignalType string
}

// min returns the smaller of x or y
func min(x, y int) int {
	if x < y {
		return x
	}
	return y
}
