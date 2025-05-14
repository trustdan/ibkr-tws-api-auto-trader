package models

import (
	"time"
)

// Bar represents a single price bar/candle for a financial instrument
type Bar struct {
	Date   time.Time
	Open   float64
	High   float64
	Low    float64
	Close  float64
	Volume float64
}

// IsGreen returns true if the bar closed higher than it opened
func (b *Bar) IsGreen() bool {
	return b.Close > b.Open
}

// IsRed returns true if the bar closed lower than it opened
func (b *Bar) IsRed() bool {
	return b.Close < b.Open
}
