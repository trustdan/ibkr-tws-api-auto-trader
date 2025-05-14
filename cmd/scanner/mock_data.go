package main

import (
	"time"

	"github.com/user/trader-scanner/pkg/client"
	"github.com/user/trader-scanner/pkg/models"
)

// setupMockData sets up mock data for testing pattern detection
func setupMockData(mock *client.MockMarketDataClient) {
	// Today's date
	now := time.Now()

	// Create mock data for AAPL - bullish pattern (2 green candles above rising SMA50)
	applBars := createBullishPattern(now)
	mock.MockBars["AAPL"] = applBars
	mock.MockIVs["AAPL"] = 0.4 // Normal IV

	// Create mock data for MSFT - bullish pattern with high IV (for credit strategy)
	msftBars := createBullishPattern(now)
	mock.MockBars["MSFT"] = msftBars
	mock.MockIVs["MSFT"] = 0.9 // High IV

	// Create mock data for SPY - bearish pattern (2 red candles below SMA50)
	spyBars := createBearishPattern(now)
	mock.MockBars["SPY"] = spyBars
	mock.MockIVs["SPY"] = 0.4 // Normal IV

	// Create mock data for QQQ - bearish pattern with high IV
	qqqBars := createBearishPattern(now)
	mock.MockBars["QQQ"] = qqqBars
	mock.MockIVs["QQQ"] = 0.9 // High IV

	// Create mock data for AMZN - no pattern
	amznBars := createNoPattern(now)
	mock.MockBars["AMZN"] = amznBars
	mock.MockIVs["AMZN"] = 0.5
}

// createBullishPattern creates 60 bars with a bullish pattern (last 2 green above rising SMA50)
func createBullishPattern(now time.Time) []models.Bar {
	// Create 60 bars (enough for SMA50 + 2 candles)
	bars := make([]models.Bar, 60)

	// Initial price and trend
	price := 100.0
	trend := 0.1 // Slight uptrend

	// Generate first 50 bars with a slight uptrend for SMA calculation
	for i := 0; i < 50; i++ {
		date := now.AddDate(0, 0, i-60) // Start 60 days ago

		// Add some randomness to price
		change := trend + (0.5-rand())*2 // Random between -1 and 1

		open := price
		close := price + change
		high := maxFloat(open, close) + 0.5
		low := minFloat(open, close) - 0.5

		bars[i] = models.Bar{
			Date:   date,
			Open:   open,
			High:   high,
			Low:    low,
			Close:  close,
			Volume: 1000000 + rand()*1000000,
		}

		price = close
	}

	// Generate last 2 bars (green, above SMA)
	for i := 50; i < 60; i++ {
		date := now.AddDate(0, 0, i-60)

		// Force a green candle (close > open)
		open := price
		close := price + 1.0 + rand() // Ensure it's green with a minimum 1 point gain
		high := close + 0.5
		low := open - 0.5

		bars[i] = models.Bar{
			Date:   date,
			Open:   open,
			High:   high,
			Low:    low,
			Close:  close,
			Volume: 1500000 + rand()*1000000,
		}

		price = close
	}

	return bars
}

// createBearishPattern creates 60 bars with a bearish pattern (last 2 red below SMA50)
func createBearishPattern(now time.Time) []models.Bar {
	// Create 60 bars (enough for SMA50 + 2 candles)
	bars := make([]models.Bar, 60)

	// Initial price and trend
	price := 100.0
	trend := -0.1 // Slight downtrend

	// Generate first 50 bars with a slight downtrend for SMA calculation
	for i := 0; i < 50; i++ {
		date := now.AddDate(0, 0, i-60) // Start 60 days ago

		// Add some randomness to price
		change := trend + (0.5-rand())*2 // Random between -1 and 1

		open := price
		close := price + change
		high := maxFloat(open, close) + 0.5
		low := minFloat(open, close) - 0.5

		bars[i] = models.Bar{
			Date:   date,
			Open:   open,
			High:   high,
			Low:    low,
			Close:  close,
			Volume: 1000000 + rand()*1000000,
		}

		price = close
	}

	// Generate last 2 bars (red, below SMA)
	for i := 50; i < 60; i++ {
		date := now.AddDate(0, 0, i-60)

		// Force a red candle (close < open)
		open := price
		close := price - (1.0 + rand()) // Ensure it's red with a minimum 1 point drop
		high := open + 0.5
		low := close - 0.5

		bars[i] = models.Bar{
			Date:   date,
			Open:   open,
			High:   high,
			Low:    low,
			Close:  close,
			Volume: 1500000 + rand()*1000000,
		}

		price = close
	}

	return bars
}

// createNoPattern creates 60 bars with no clear pattern
func createNoPattern(now time.Time) []models.Bar {
	// Create 60 bars
	bars := make([]models.Bar, 60)

	// Initial price
	price := 100.0

	// Generate random bars
	for i := 0; i < 60; i++ {
		date := now.AddDate(0, 0, i-60) // Start 60 days ago

		// Random price changes
		change := (0.5 - rand()) * 4 // Random between -2 and 2

		open := price
		close := price + change
		high := maxFloat(open, close) + 0.5 + rand()
		low := minFloat(open, close) - 0.5 - rand()

		bars[i] = models.Bar{
			Date:   date,
			Open:   open,
			High:   high,
			Low:    low,
			Close:  close,
			Volume: 1000000 + rand()*2000000,
		}

		price = close
	}

	return bars
}

// Helper functions for random numbers and min/max
func rand() float64 {
	return float64(time.Now().UnixNano()%1000) / 1000.0
}

func maxFloat(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func minFloat(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
