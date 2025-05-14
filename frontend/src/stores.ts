import { writable } from 'svelte/store';

export interface Config {
  // Connection parameters
  host: string;
  port: number;
  client_id: number;
  
  // Strategy parameters
  sma_period?: number;
  candle_count?: number;
  otm_offset?: number;
  iv_threshold?: number;
  min_reward_risk?: number;
  
  [key: string]: any; // Allow other properties
}

export interface ConnectionStatus {
  connected: boolean;
  error?: string;
}

// Default initial values
const defaultConfig: Config = {
  // Connection defaults
  host: 'localhost',
  port: 7497,
  client_id: 1,
  
  // Strategy defaults
  sma_period: 50,
  candle_count: 2,
  otm_offset: 1,
  iv_threshold: 0.7,
  min_reward_risk: 1.0
};

export interface Schema {
  properties: Record<string, {
    type: string;
    title?: string;
    description?: string;
    minimum?: number;
    maximum?: number;
    default?: any;
  }>;
  required?: string[];
}

export const schemaStore = writable<Schema | null>(null);
export const configStore = writable<Config>(defaultConfig);
export const statusStore = writable<ConnectionStatus>({ connected: false });

// Signal types matching our proto definitions
export enum SignalType {
  NONE = 0,
  CALL_DEBIT = 1,
  PUT_DEBIT = 2,
  CALL_CREDIT = 3,
  PUT_CREDIT = 4
}

export interface Signal {
  symbol: string;
  signal: SignalType;
  timestamp: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  unrealizedPnL: number;
} 