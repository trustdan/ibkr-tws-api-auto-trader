import { writable, get } from 'svelte/store';

// Define types for our stores
export interface IBKRConfig {
  host: string;
  port: number;
  client_id: number;
}

export interface StrategyConfig {
  sma_period: number;
  candle_count: number;
  otm_offset: number;
  iv_threshold: number;
  min_reward_risk: number;
  enable_auto_trade: boolean;
}

export interface RootConfig {
  ibkr: IBKRConfig;
  strategy: StrategyConfig;
}

export interface ConnectionStatus {
  connected: boolean;
  message: string;
  lastConnectAttempt?: Date;
}

// Create stores
export const schemaStore = writable<any>(null);
export const configStore = writable<RootConfig>({
  ibkr: {
    host: 'localhost',
    port: 7497,
    client_id: 1
  },
  strategy: {
    sma_period: 50,
    candle_count: 2,
    otm_offset: 1,
    iv_threshold: 0.6,
    min_reward_risk: 1.0,
    enable_auto_trade: false
  }
});
export const statusStore = writable<ConnectionStatus>({
  connected: false,
  message: 'Not connected to IBKR'
});

// Helper functions
export const updateConfig = (path: string, value: any) => {
  // Update nested properties using path notation (e.g., "ibkr.host")
  configStore.update(config => {
    const pathParts = path.split('.');
    let current: any = config;
    
    // Navigate to the correct nested object
    for (let i = 0; i < pathParts.length - 1; i++) {
      current = current[pathParts[i]];
    }
    
    // Update the value
    current[pathParts[pathParts.length - 1]] = value;
    return config;
  });
};

export const getDefaultFromSchema = (schema: any): any => {
  if (!schema) return null;
  
  // If this is a schema with properties, process each property
  if (schema.properties) {
    const result: any = {};
    for (const [key, prop] of Object.entries<any>(schema.properties)) {
      if (prop.default !== undefined) {
        result[key] = prop.default;
      } else if (prop.type === 'object' && prop.properties) {
        result[key] = getDefaultFromSchema(prop);
      } else if (prop.type === 'array') {
        result[key] = [];
      } else if (prop.type === 'string') {
        result[key] = '';
      } else if (prop.type === 'number' || prop.type === 'integer') {
        result[key] = 0;
      } else if (prop.type === 'boolean') {
        result[key] = false;
      } else {
        result[key] = null;
      }
    }
    return result;
  }
  
  // If this is a single property, return its default or an appropriate default value
  if (schema.default !== undefined) {
    return schema.default;
  }
  
  // Fallback defaults based on type
  if (schema.type === 'string') return '';
  if (schema.type === 'number' || schema.type === 'integer') return 0;
  if (schema.type === 'boolean') return false;
  if (schema.type === 'array') return [];
  if (schema.type === 'object') return {};
  
  return null;
}; 