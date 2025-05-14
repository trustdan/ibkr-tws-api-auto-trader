package config

import (
	"os"
	"testing"
)

func TestLoadConfig(t *testing.T) {
	// Create a temporary config file
	tmpFile, err := os.CreateTemp("", "config-*.json")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())

	// Write test config
	configJSON := `{
		"sma50_period": 60,
		"candle_count": 3,
		"iv_threshold": 0.75,
		"min_reward_risk": 1.5,
		"universe": ["TEST1", "TEST2"]
	}`
	if _, err := tmpFile.Write([]byte(configJSON)); err != nil {
		t.Fatalf("Failed to write to temp file: %v", err)
	}
	if err := tmpFile.Close(); err != nil {
		t.Fatalf("Failed to close temp file: %v", err)
	}

	// Load the config
	cfg, err := Load(tmpFile.Name())
	if err != nil {
		t.Fatalf("Failed to load config: %v", err)
	}

	// Verify values
	if cfg.SMA50Period != 60 {
		t.Errorf("Expected SMA50Period=60, got %d", cfg.SMA50Period)
	}
	if cfg.CandleCount != 3 {
		t.Errorf("Expected CandleCount=3, got %d", cfg.CandleCount)
	}
	if cfg.IVThreshold != 0.75 {
		t.Errorf("Expected IVThreshold=0.75, got %f", cfg.IVThreshold)
	}
	if cfg.MinRewardRisk != 1.5 {
		t.Errorf("Expected MinRewardRisk=1.5, got %f", cfg.MinRewardRisk)
	}
	if len(cfg.Universe) != 2 || cfg.Universe[0] != "TEST1" || cfg.Universe[1] != "TEST2" {
		t.Errorf("Universe mismatch, got %v", cfg.Universe)
	}
}

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.SMA50Period != 50 {
		t.Errorf("Expected default SMA50Period=50, got %d", cfg.SMA50Period)
	}
	if cfg.CandleCount != 2 {
		t.Errorf("Expected default CandleCount=2, got %d", cfg.CandleCount)
	}
}
