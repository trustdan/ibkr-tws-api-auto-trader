import { writable } from 'svelte/store';

// Store for the JSON schema
export const schemaStore = writable(null);

// Store for the current configuration
export const configStore = writable({
  // Connection parameters
  host: "localhost",
  port: 7497,
  client_id: 1,
  
  // Strategy parameters
  sma_period: 50,
  candle_count: 2,
  otm_offset: 1,
  iv_threshold: 0.7,
  min_reward_risk: 1.0,
  
  // Execution parameters
  max_bid_ask_distance: 5.0,
  order_type: 'Limit',
  price_improvement: 0.5
});

// Store for the connection status
export const statusStore = writable({ 
  connected: false,
  message: 'Not connected to IBKR',
  error: null
});

// Store for trading data
export const tradingStore = writable({
  signals: [],
  positions: []
}); 