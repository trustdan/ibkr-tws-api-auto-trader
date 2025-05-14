package main

import (
	"context"
	"encoding/json"
	"fmt"
)

// App struct represents the main application state and methods
type App struct {
	ctx       context.Context
	config    map[string]interface{}
	connected bool
}

// NewApp creates a new App instance
func NewApp() *App {
	return &App{
		config:    make(map[string]interface{}),
		connected: false,
	}
}

// startup is called when the app starts
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

// Status returns the connection status
func (a *App) Status() string {
	if a.connected {
		return "TraderAdmin is connected to IBKR"
	}
	return "TraderAdmin is running"
}

// GetVersion returns the application version
func (a *App) GetVersion() string {
	return "v0.1.0"
}

// ConnectIBKR simulates connecting to IBKR TWS
func (a *App) ConnectIBKR(host string, port int, clientID int) string {
	connectionString := fmt.Sprintf("Connected to IBKR at %s:%d with client ID %d", host, port, clientID)
	a.connected = true
	return connectionString
}

// UpdateConfig updates the application configuration with JSON input
func (a *App) UpdateConfig(configJSON string) (bool, error) {
	var newConfig map[string]interface{}
	err := json.Unmarshal([]byte(configJSON), &newConfig)
	if err != nil {
		return false, err
	}

	a.config = newConfig
	return true, nil
}

// GetDefaultConfig returns the default configuration
func (a *App) GetDefaultConfig() string {
	defaultConfig := `{
		"host": "localhost",
		"port": 7497,
		"client_id": 1,
		"sma_period": 50,
		"candle_count": 2,
		"otm_offset": 1,
		"iv_threshold": 0.7,
		"min_reward_risk": 1.0,
		"max_bid_ask_distance": 5.0,
		"order_type": "Limit",
		"price_improvement": 0.5
	}`
	return defaultConfig
}

// GetCurrentConfig returns the current configuration (same as default for now)
func (a *App) GetCurrentConfig() string {
	return a.GetDefaultConfig()
}

// SaveConfig saves the configuration (already implemented in app.go)
// IsConnected is already implemented in app.go

// GetConfigSchema returns the JSON schema for configuration
func (a *App) GetConfigSchema() string {
	// This would typically generate a JSON schema from your config structs
	// For now, we'll return a simple schema
	schema := `{
		"$schema": "http://json-schema.org/draft-07/schema#",
		"type": "object",
		"properties": {
			"host": {
				"type": "string",
				"title": "Host",
				"description": "IBKR TWS host address",
				"default": "localhost"
			},
			"port": {
				"type": "integer",
				"title": "Port",
				"description": "IBKR TWS port",
				"default": 7497,
				"minimum": 1,
				"maximum": 65535
			},
			"client_id": {
				"type": "integer",
				"title": "Client ID",
				"description": "IBKR client ID",
				"default": 1,
				"minimum": 0
			},
			"sma_period": {
				"type": "integer",
				"title": "SMA Period",
				"description": "Period for Simple Moving Average calculation (days)",
				"default": 50,
				"minimum": 1,
				"maximum": 200
			},
			"candle_count": {
				"type": "integer",
				"title": "Candle Count",
				"description": "Number of candles to evaluate for pattern",
				"default": 2,
				"minimum": 1,
				"maximum": 10
			},
			"otm_offset": {
				"type": "integer",
				"title": "OTM Offset",
				"description": "Number of strikes out-of-the-money",
				"default": 1,
				"minimum": 0,
				"maximum": 10
			},
			"iv_threshold": {
				"type": "number",
				"title": "IV Threshold",
				"description": "IV percentile threshold (0.0-1.0)",
				"default": 0.7,
				"minimum": 0.0,
				"maximum": 1.0
			},
			"min_reward_risk": {
				"type": "number",
				"title": "Minimum Reward/Risk",
				"description": "Required reward-to-risk ratio",
				"default": 1.0,
				"minimum": 0.1
			},
			"max_bid_ask_distance": {
				"type": "number",
				"title": "Maximum % Distance between Bid and Ask",
				"description": "Maximum acceptable percentage spread between bid and ask prices",
				"default": 5.0,
				"minimum": 0.1,
				"maximum": 20.0
			},
			"order_type": {
				"type": "string",
				"title": "Order Type",
				"description": "Type of order to place when executing trades",
				"default": "Limit",
				"enum": ["Market", "Limit", "MidPrice"]
			},
			"price_improvement": {
				"type": "number",
				"title": "Price Improvement %",
				"description": "Percentage of mid-price improvement for limit orders",
				"default": 0.5,
				"minimum": 0.0,
				"maximum": 5.0
			}
		},
		"required": ["host", "port", "client_id", "sma_period", "candle_count", "otm_offset", "iv_threshold", "min_reward_risk", "max_bid_ask_distance", "order_type"]
	}`

	return schema
}
