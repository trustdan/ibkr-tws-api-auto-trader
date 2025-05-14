package config

import (
	"encoding/json"
	"os"
)

// Config represents the scanner configuration settings
type Config struct {
	SMA50Period   int      `json:"sma50_period"`
	CandleCount   int      `json:"candle_count"`
	IVThreshold   float64  `json:"iv_threshold"`
	MinRewardRisk float64  `json:"min_reward_risk"`
	Universe      []string `json:"universe"`
}

// Load reads a configuration file from the given path and returns a Config struct
func Load(path string) (*Config, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var cfg Config
	if err := json.NewDecoder(f).Decode(&cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}

// DefaultConfig returns a configuration with sensible defaults
func DefaultConfig() *Config {
	return &Config{
		SMA50Period:   50,
		CandleCount:   2,
		IVThreshold:   0.8,
		MinRewardRisk: 1.0,
		Universe:      []string{"AAPL", "MSFT", "SPY"},
	}
}
