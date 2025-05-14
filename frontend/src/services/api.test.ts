import { vi, describe, it, expect, beforeEach } from 'vitest';
import * as app from '../../wailsjs/go/main/App';
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

// Mock the wails Go bindings
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

describe('API Service', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('fetchSignals', () => {
    it('should call ScanSignals and return results', async () => {
      const mockSignals = [
        { symbol: 'AAPL', signal: 1, timestamp: Date.now() }
      ];
      app.ScanSignals.mockResolvedValue(mockSignals);

      const result = await fetchSignals();
      expect(app.ScanSignals).toHaveBeenCalled();
      expect(result).toEqual(mockSignals);
    });

    it('should propagate errors', async () => {
      const error = new Error('Network error');
      app.ScanSignals.mockRejectedValue(error);

      await expect(fetchSignals()).rejects.toThrow('Network error');
    });
  });

  describe('fetchPositions', () => {
    it('should call GetPositions and return results', async () => {
      const mockPositions = [
        { symbol: 'AAPL', quantity: 100, avgPrice: 180.5, unrealizedPnL: 250.75 }
      ];
      app.GetPositions.mockResolvedValue(mockPositions);

      const result = await fetchPositions();
      expect(app.GetPositions).toHaveBeenCalled();
      expect(result).toEqual(mockPositions);
    });
  });

  describe('pauseScanner', () => {
    it('should call PauseScanning', async () => {
      app.PauseScanning.mockResolvedValue(undefined);

      await pauseScanner();
      expect(app.PauseScanning).toHaveBeenCalled();
    });
  });

  describe('resumeScanner', () => {
    it('should call ResumeScanning', async () => {
      app.ResumeScanning.mockResolvedValue(undefined);

      await resumeScanner();
      expect(app.ResumeScanning).toHaveBeenCalled();
    });
  });

  describe('persistConfig', () => {
    it('should call SaveConfig with JSON string', async () => {
      const config = { host: 'localhost', port: 7497, client_id: 1 };
      app.SaveConfig.mockResolvedValue(undefined);

      await persistConfig(config);
      expect(app.SaveConfig).toHaveBeenCalledWith(JSON.stringify(config));
    });
  });

  describe('connectToIBKR', () => {
    it('should call ConnectIBKR with connection params', async () => {
      app.ConnectIBKR.mockResolvedValue(true);

      const result = await connectToIBKR('localhost', 7497, 1);
      expect(app.ConnectIBKR).toHaveBeenCalledWith('localhost', 7497, 1);
      expect(result).toBe(true);
    });
  });

  describe('disconnectFromIBKR', () => {
    it('should call DisconnectIBKR', async () => {
      app.DisconnectIBKR.mockResolvedValue(true);

      const result = await disconnectFromIBKR();
      expect(app.DisconnectIBKR).toHaveBeenCalled();
      expect(result).toBe(true);
    });
  });

  describe('checkConnectionStatus', () => {
    it('should call IsConnected', async () => {
      app.IsConnected.mockResolvedValue(true);

      const result = await checkConnectionStatus();
      expect(app.IsConnected).toHaveBeenCalled();
      expect(result).toBe(true);
    });

    it('should return false on error', async () => {
      app.IsConnected.mockRejectedValue(new Error('Connection failed'));

      const result = await checkConnectionStatus();
      expect(result).toBe(false);
    });
  });

  describe('fetchConfigSchema', () => {
    it('should call GetConfigSchema and parse JSON', async () => {
      const schemaStr = '{"properties":{"host":{"type":"string"}}}';
      const expectedSchema = { properties: { host: { type: 'string' } } };
      app.GetConfigSchema.mockResolvedValue(schemaStr);

      const result = await fetchConfigSchema();
      expect(app.GetConfigSchema).toHaveBeenCalled();
      expect(result).toEqual(expectedSchema);
    });
  });
}); 