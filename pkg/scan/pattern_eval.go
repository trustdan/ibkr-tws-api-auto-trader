package scan

import (
	"github.com/user/trader-scanner/pkg/config"
	"github.com/user/trader-scanner/pkg/models"
)

// EvaluatePattern analyzes bars and IV data to determine a trading signal
func EvaluatePattern(bars []models.Bar, ivPercentile float64, cfg *config.Config) string {
	if len(bars) < cfg.SMA50Period+cfg.CandleCount {
		return SignalNone // Not enough data
	}

	// Calculate SMA50
	sma := ComputeSMA(bars, cfg.SMA50Period)
	if sma == nil {
		return SignalNone
	}

	// Get the last N bars (where N is candle_count) - typically 2
	lastIdx := len(bars) - 1
	startIdx := lastIdx - (cfg.CandleCount - 1)

	// Check if we have enough data for our patterns
	if startIdx < 0 || lastIdx >= len(bars) || lastIdx >= len(sma) {
		return SignalNone
	}

	// Check if last 2 bars are green
	allGreen := true
	for i := startIdx; i <= lastIdx; i++ {
		if !bars[i].IsGreen() {
			allGreen = false
			break
		}
	}

	// Check if last 2 bars are red
	allRed := true
	for i := startIdx; i <= lastIdx; i++ {
		if !bars[i].IsRed() {
			allRed = false
			break
		}
	}

	// Check if SMA is rising
	smaRising := IsSMARising(sma, lastIdx)

	// Check if last bar is above SMA
	aboveSMA := bars[lastIdx].Close > sma[lastIdx]

	// Check if last bar is below SMA
	belowSMA := bars[lastIdx].Close < sma[lastIdx]

	// High IV environment (credit strategies)
	highIV := ivPercentile > cfg.IVThreshold

	// Determine signal type based on pattern rules

	// Bullish: last 2 bars green, closing price above rising SMA50
	if allGreen && aboveSMA && smaRising {
		if highIV {
			return SignalCallCredit // High IV, use credit strategy
		}
		return SignalCallDebit // Normal IV, use debit strategy
	}

	// Bearish: last 2 bars red, closing price below SMA50
	if allRed && belowSMA {
		if highIV {
			return SignalPutCredit // High IV, use credit strategy
		}
		return SignalPutDebit // Normal IV, use debit strategy
	}

	return SignalNone // No pattern detected
}
