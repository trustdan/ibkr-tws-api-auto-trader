package main

import (
	"encoding/json"

	"github.com/alecthomas/jsonschema"
)

// IBKRConfig represents connection settings for Interactive Brokers TWS
type IBKRConfig struct {
	Host     string `json:"host" jsonschema:"required,default=localhost,description=TWS hostname or IP address"`
	Port     int    `json:"port" jsonschema:"required,default=7497,minimum=1,maximum=65535,description=TWS port number"`
	ClientID int    `json:"client_id" jsonschema:"required,default=1,minimum=1,description=TWS client ID"`
}

// StrategyConfig represents trading strategy parameters
type StrategyConfig struct {
	SMAPeriod       int     `json:"sma_period" jsonschema:"required,default=50,minimum=5,description=Period for Simple Moving Average calculation"`
	CandleCount     int     `json:"candle_count" jsonschema:"required,default=2,minimum=1,description=Number of candles to evaluate for pattern"`
	OTMOffset       int     `json:"otm_offset" jsonschema:"required,default=1,minimum=0,description=Strikes out-of-the-money for option selection"`
	IVThreshold     float64 `json:"iv_threshold" jsonschema:"required,default=0.6,minimum=0,maximum=1,description=IV percentile threshold for strategy selection"`
	MinRewardRisk   float64 `json:"min_reward_risk" jsonschema:"required,default=1.0,minimum=0.1,description=Required reward-to-risk ratio"`
	EnableAutoTrade bool    `json:"enable_auto_trade" jsonschema:"default=false,description=Enable automatic trade execution"`
}

// RootConfig is the top-level configuration structure
type RootConfig struct {
	IBKR     IBKRConfig     `json:"ibkr" jsonschema:"required"`
	Strategy StrategyConfig `json:"strategy" jsonschema:"required"`
}

// GetIBKRConfigSchema returns the JSON schema for IBKR connection settings
func (a *App) GetIBKRConfigSchema() (string, error) {
	reflector := &jsonschema.Reflector{RequiredFromJSONSchemaTags: true}
	schema := reflector.Reflect(&IBKRConfig{})
	schemaJSON, err := json.MarshalIndent(schema, "", "  ")
	return string(schemaJSON), err
}

// GetStrategyConfigSchema returns the JSON schema for trading strategy parameters
func (a *App) GetStrategyConfigSchema() (string, error) {
	reflector := &jsonschema.Reflector{RequiredFromJSONSchemaTags: true}
	schema := reflector.Reflect(&StrategyConfig{})
	schemaJSON, err := json.MarshalIndent(schema, "", "  ")
	return string(schemaJSON), err
}

// GetConfigSchema returns the complete JSON schema for all configuration
func (a *App) GetConfigSchema() (string, error) {
	reflector := &jsonschema.Reflector{RequiredFromJSONSchemaTags: true}
	schema := reflector.Reflect(&RootConfig{})
	schemaJSON, err := json.MarshalIndent(schema, "", "  ")
	return string(schemaJSON), err
}

// SaveConfig saves the given configuration
func (a *App) SaveConfig(config string) error {
	// TODO: Implement config saving to file
	return nil
}

// LoadConfig loads the configuration
func (a *App) LoadConfig() (string, error) {
	// TODO: Implement config loading from file
	// For now, return default config
	config := RootConfig{
		IBKR: IBKRConfig{
			Host:     "localhost",
			Port:     7497,
			ClientID: 1,
		},
		Strategy: StrategyConfig{
			SMAPeriod:       50,
			CandleCount:     2,
			OTMOffset:       1,
			IVThreshold:     0.6,
			MinRewardRisk:   1.0,
			EnableAutoTrade: false,
		},
	}

	configJSON, err := json.MarshalIndent(config, "", "  ")
	return string(configJSON), err
}
