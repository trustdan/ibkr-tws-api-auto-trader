import * as app from '../../wailsjs/go/main/App';
import type { Config, Signal, Position } from '../stores';

/**
 * Signal-related API calls
 * These connect to the scanner service via the Go backend
 */

/**
 * Fetches the latest scan signals from the backend
 * The backend calls the gRPC ScannerService.ScanUniverse endpoint
 * @returns Promise<Signal[]> A list of trading signals with symbol, type, and timestamp
 */
export async function fetchSignals(): Promise<Signal[]> {
  try {
    return await app.ScanSignals();
  } catch (e) {
    console.error('ScanSignals failed', e);
    throw e;
  }
}

/**
 * Position-related API calls
 * These connect to the ib_insync account positions service
 */

/**
 * Fetches current positions from the backend
 * The backend calls the Python orchestrator via gRPC to get position data
 * @returns Promise<Position[]> A list of current positions with P/L data
 */
export async function fetchPositions(): Promise<Position[]> {
  try {
    return await app.GetPositions();
  } catch (e) {
    console.error('GetPositions failed', e);
    throw e;
  }
}

/**
 * Scanner control API calls
 * These manage the scanner service state
 */

/**
 * Pauses the scanner service
 * @returns Promise<void>
 */
export async function pauseScanner(): Promise<void> {
  try {
    await app.PauseScanning();
  } catch (e) {
    console.error('PauseScanning failed', e);
    throw e;
  }
}

/**
 * Resumes the scanner service
 * @returns Promise<void>
 */
export async function resumeScanner(): Promise<void> {
  try {
    await app.ResumeScanning();
  } catch (e) {
    console.error('ResumeScanning failed', e);
    throw e;
  }
}

/**
 * Configuration API calls
 * These manage the strategy and execution parameters
 */

/**
 * Persists the configuration to the backend
 * @param cfg The configuration object to save
 * @returns Promise<void>
 */
export async function persistConfig(cfg: Config): Promise<void> {
  try {
    return await app.SaveConfig(JSON.stringify(cfg));
  } catch (e) {
    console.error('SaveConfig failed', e);
    throw e;
  }
}

/**
 * Connection API calls
 * These manage the IBKR TWS connection
 */

/**
 * Connects to IBKR TWS with the specified parameters
 * @param host The TWS host address (usually localhost)
 * @param port The TWS port (typically 7496 for TWS or 7497 for Gateway)
 * @param clientId The client ID to use
 * @returns Promise<boolean> True if connected successfully
 */
export async function connectToIBKR(host: string, port: number, clientId: number): Promise<boolean> {
  try {
    return await app.ConnectIBKR(host, port, clientId);
  } catch (e) {
    console.error('ConnectIBKR failed', e);
    throw e;
  }
}

/**
 * Disconnects from IBKR TWS
 * @returns Promise<boolean> True if disconnected successfully
 */
export async function disconnectFromIBKR(): Promise<boolean> {
  try {
    return await app.DisconnectIBKR();
  } catch (e) {
    console.error('DisconnectIBKR failed', e);
    throw e;
  }
}

/**
 * Checks if we're currently connected to IBKR TWS
 * @returns Promise<boolean> True if currently connected
 */
export async function checkConnectionStatus(): Promise<boolean> {
  try {
    return await app.IsConnected();
  } catch (e) {
    console.error('IsConnected failed', e);
    return false;
  }
}

/**
 * Schema API calls
 * These fetch the configuration schema for dynamic form generation
 */

/**
 * Fetches the configuration schema from the backend
 * @returns Promise<any> The JSON schema for configuration
 */
export async function fetchConfigSchema(): Promise<any> {
  try {
    const schemaStr = await app.GetConfigSchema();
    return JSON.parse(schemaStr);
  } catch (e) {
    console.error('GetConfigSchema failed', e);
    throw e;
  }
} 