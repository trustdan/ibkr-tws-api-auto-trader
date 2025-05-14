package scan

import (
	"github.com/user/trader-scanner/pkg/models"
)

// ComputeSMA calculates the Simple Moving Average for the given period
func ComputeSMA(bars []models.Bar, period int) []float64 {
	if len(bars) < period {
		return nil
	}

	sma := make([]float64, len(bars))

	// For each bar, calculate the SMA if we have enough data
	for i := 0; i < len(bars); i++ {
		// Not enough bars yet for SMA
		if i < period-1 {
			sma[i] = 0
			continue
		}

		// Sum the closing prices for the period
		sum := 0.0
		for j := 0; j < period; j++ {
			sum += bars[i-j].Close
		}

		// Calculate the average
		sma[i] = sum / float64(period)
	}

	return sma
}

// IsSMARising checks if the SMA is rising (current value > previous value)
func IsSMARising(sma []float64, index int) bool {
	if index < 1 || index >= len(sma) {
		return false
	}

	return sma[index] > sma[index-1]
}
