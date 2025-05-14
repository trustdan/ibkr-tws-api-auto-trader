package scan

import (
	"testing"
	"time"

	"github.com/user/trader-scanner/pkg/config"
	"github.com/user/trader-scanner/pkg/models"
)

func TestEvaluatePattern(t *testing.T) {
	// Create a test configuration
	cfg := &config.Config{
		SMA50Period: 50,
		CandleCount: 2,
		IVThreshold: 0.8,
	}

	// Test cases
	testCases := []struct {
		name         string
		bars         []models.Bar
		ivPercentile float64
		expected     string
	}{
		{
			name:         "Not enough bars",
			bars:         make([]models.Bar, 10),
			ivPercentile: 0.5,
			expected:     SignalNone,
		},
		{
			name:         "Bullish pattern normal IV",
			bars:         createTestBullishBars(60),
			ivPercentile: 0.5,
			expected:     SignalCallDebit,
		},
		{
			name:         "Bullish pattern high IV",
			bars:         createTestBullishBars(60),
			ivPercentile: 0.9,
			expected:     SignalCallCredit,
		},
		{
			name:         "Bearish pattern normal IV",
			bars:         createTestBearishBars(60),
			ivPercentile: 0.5,
			expected:     SignalPutDebit,
		},
		{
			name:         "Bearish pattern high IV",
			bars:         createTestBearishBars(60),
			ivPercentile: 0.9,
			expected:     SignalPutCredit,
		},
		{
			name:         "No pattern",
			bars:         createTestMixedBars(60),
			ivPercentile: 0.5,
			expected:     SignalNone,
		},
	}

	// Run test cases
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result := EvaluatePattern(tc.bars, tc.ivPercentile, cfg)
			if result != tc.expected {
				t.Errorf("Expected signal %s, got %s", tc.expected, result)
			}
		})
	}
}

// Helper functions to create test data
func createTestBullishBars(count int) []models.Bar {
	bars := make([]models.Bar, count)
	baseTime := time.Now().AddDate(0, 0, -count)

	// Create bars with a general uptrend
	price := 100.0
	for i := 0; i < count-2; i++ {
		// Slightly rising price
		change := 0.1 + float64(i%3)*0.2 // Small upward bias

		open := price
		close := price + change

		// Force some bars to be red to make it realistic
		if i%4 == 0 {
			temp := open
			open = close
			close = temp
		}

		bars[i] = models.Bar{
			Date:   baseTime.AddDate(0, 0, i),
			Open:   open,
			High:   maxFloat(open, close) + 0.5,
			Low:    minFloat(open, close) - 0.5,
			Close:  close,
			Volume: 1000000,
		}

		price = close
	}

	// Last two bars are green and above SMA
	for i := count - 2; i < count; i++ {
		open := price
		close := price + 2.0 // Force green bar

		bars[i] = models.Bar{
			Date:   baseTime.AddDate(0, 0, i),
			Open:   open,
			High:   close + 0.5,
			Low:    open - 0.5,
			Close:  close,
			Volume: 1500000,
		}

		price = close
	}

	return bars
}

func createTestBearishBars(count int) []models.Bar {
	bars := make([]models.Bar, count)
	baseTime := time.Now().AddDate(0, 0, -count)

	// Create bars with a general downtrend
	price := 100.0
	for i := 0; i < count-2; i++ {
		// Slightly falling price
		change := -0.1 - float64(i%3)*0.2 // Small downward bias

		open := price
		close := price + change

		// Force some bars to be green to make it realistic
		if i%4 == 0 {
			temp := open
			open = close
			close = temp
		}

		bars[i] = models.Bar{
			Date:   baseTime.AddDate(0, 0, i),
			Open:   open,
			High:   maxFloat(open, close) + 0.5,
			Low:    minFloat(open, close) - 0.5,
			Close:  close,
			Volume: 1000000,
		}

		price = close
	}

	// Last two bars are red and below SMA
	for i := count - 2; i < count; i++ {
		open := price
		close := price - 2.0 // Force red bar

		bars[i] = models.Bar{
			Date:   baseTime.AddDate(0, 0, i),
			Open:   open,
			High:   open + 0.5,
			Low:    close - 0.5,
			Close:  close,
			Volume: 1500000,
		}

		price = close
	}

	return bars
}

func createTestMixedBars(count int) []models.Bar {
	bars := make([]models.Bar, count)
	baseTime := time.Now().AddDate(0, 0, -count)

	// Create bars with mixed patterns
	price := 100.0
	for i := 0; i < count; i++ {
		// Alternate between up and down
		change := float64(i%2)*2 - 1 // Alternates between 1 and -1

		open := price
		close := price + change

		bars[i] = models.Bar{
			Date:   baseTime.AddDate(0, 0, i),
			Open:   open,
			High:   maxFloat(open, close) + 0.5,
			Low:    minFloat(open, close) - 0.5,
			Close:  close,
			Volume: 1000000,
		}

		price = close
	}

	return bars
}

// Helper functions for the test file
func minFloat(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func maxFloat(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
