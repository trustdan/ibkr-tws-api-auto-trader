import { vi, describe, it, expect, beforeEach } from 'vitest';
import { 
  fetchSignals, 
  fetchPositions, 
  pauseScanner,
  resumeScanner,
  persistConfig,
  connectToIBKR,
  disconnectFromIBKR,
  checkConnectionStatus,
  fetchConfigSchema
} from './api';
import type { Config } from '../stores';

// Mock the Wails bindings
vi.mock('../../wailsjs/go/main/App', () => {
  return {
    ScanSignals: vi.fn(),
    GetPositions: vi.fn(),
    PauseScanning: vi.fn(),
    ResumeScanning: vi.fn(),
    SaveConfig: vi.fn(),
    ConnectIBKR: vi.fn(),
    DisconnectIBKR: vi.fn(),
    IsConnected: vi.fn(),
    GetConfigSchema: vi.fn()
  };
});

// Import the mocked module using require to avoid await issues
const app = vi.mocked(require('../../wailsjs/go/main/App'), true);

describe('API Service', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('Signal APIs', () => {
    it('fetchSignals should return signals when successful', async () => {
      const mockSignals = [
        { symbol: 'AAPL', signal: 1, timestamp: Date.now() }
      ];
      
      app.ScanSignals.mockResolvedValue(mockSignals);
      
      const result = await fetchSignals();
      expect(result).toEqual(mockSignals);
      expect(app.ScanSignals).toHaveBeenCalledTimes(1);
    });
    
    it('fetchSignals should throw when backend fails', async () => {
      const mockError = new Error('Backend error');
      app.ScanSignals.mockRejectedValue(mockError);
      
      await expect(fetchSignals()).rejects.toThrow('Backend error');
      expect(app.ScanSignals).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('Position APIs', () => {
    it('fetchPositions should return positions when successful', async () => {
      const mockPositions = [
        { symbol: 'AAPL', quantity: 100, avgPrice: 180.5, unrealizedPnL: 250.75 }
      ];
      
      app.GetPositions.mockResolvedValue(mockPositions);
      
      const result = await fetchPositions();
      expect(result).toEqual(mockPositions);
      expect(app.GetPositions).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('Scanner Control APIs', () => {
    it('pauseScanner should call PauseScanning', async () => {
      await pauseScanner();
      expect(app.PauseScanning).toHaveBeenCalledTimes(1);
    });
    
    it('resumeScanner should call ResumeScanning', async () => {
      await resumeScanner();
      expect(app.ResumeScanning).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('Config APIs', () => {
    it('persistConfig should stringify and send config', async () => {
      const config: Config = { 
        host: 'localhost', 
        port: 7497, 
        client_id: 1,
        sma_period: 50,
        candle_count: 2,
        otm_offset: 1,
        iv_threshold: 0.7,
        min_reward_risk: 1.0,
        max_bid_ask_distance: 5.0,
        order_type: 'Limit',
        price_improvement: 0.5
      };
      
      await persistConfig(config);
      
      expect(app.SaveConfig).toHaveBeenCalledTimes(1);
      expect(app.SaveConfig).toHaveBeenCalledWith(JSON.stringify(config));
    });
  });
  
  describe('Connection APIs', () => {
    it('connectToIBKR should pass connection parameters', async () => {
      app.ConnectIBKR.mockResolvedValue(true);
      
      const result = await connectToIBKR('localhost', 7497, 1);
      
      expect(result).toBe(true);
      expect(app.ConnectIBKR).toHaveBeenCalledTimes(1);
      expect(app.ConnectIBKR).toHaveBeenCalledWith('localhost', 7497, 1);
    });
    
    it('disconnectFromIBKR should call DisconnectIBKR', async () => {
      app.DisconnectIBKR.mockResolvedValue(true);
      
      const result = await disconnectFromIBKR();
      
      expect(result).toBe(true);
      expect(app.DisconnectIBKR).toHaveBeenCalledTimes(1);
    });
    
    it('checkConnectionStatus should handle errors gracefully', async () => {
      app.IsConnected.mockRejectedValue(new Error('Connection error'));
      
      const result = await checkConnectionStatus();
      
      expect(result).toBe(false);
      expect(app.IsConnected).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('Schema APIs', () => {
    it('fetchConfigSchema should parse JSON schema', async () => {
      const mockSchema = { properties: { host: { type: 'string' } } };
      app.GetConfigSchema.mockResolvedValue(JSON.stringify(mockSchema));
      
      const result = await fetchConfigSchema();
      
      expect(result).toEqual(mockSchema);
      expect(app.GetConfigSchema).toHaveBeenCalledTimes(1);
    });
  });
}); 