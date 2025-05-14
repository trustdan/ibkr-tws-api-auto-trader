import * as app from '../../wailsjs/go/main/App';
import type { Config, Signal, Position } from '../stores';

/**
 * Signal-related API calls
 */
export async function fetchSignals(): Promise<Signal[]> {
  try {
    return await app.ScanSignals();
  } catch (e) {
    console.error('scanSignals failed', e);
    throw e;
  }
}

/**
 * Position-related API calls
 */
export async function fetchPositions(): Promise<Position[]> {
  try {
    return await app.GetPositions();
  } catch (e) {
    console.error('getPositions failed', e);
    throw e;
  }
}

/**
 * Scanner control API calls
 */
export async function pauseScanner(): Promise<void> {
  try {
    await app.PauseScanning();
  } catch (e) {
    console.error('pauseScanning failed', e);
    throw e;
  }
}

export async function resumeScanner(): Promise<void> {
  try {
    await app.ResumeScanning();
  } catch (e) {
    console.error('resumeScanning failed', e);
    throw e;
  }
}

/**
 * Configuration API calls
 */
export async function persistConfig(cfg: Config): Promise<void> {
  try {
    return await app.SaveConfig(JSON.stringify(cfg));
  } catch (e) {
    console.error('saveConfig failed', e);
    throw e;
  }
}

/**
 * Connection API calls
 */
export async function connectToIBKR(host: string, port: number, clientId: number): Promise<boolean> {
  try {
    return await app.ConnectIBKR(host, port, clientId);
  } catch (e) {
    console.error('connectIBKR failed', e);
    throw e;
  }
}

export async function disconnectFromIBKR(): Promise<boolean> {
  try {
    return await app.DisconnectIBKR();
  } catch (e) {
    console.error('disconnectIBKR failed', e);
    throw e;
  }
}

export async function checkConnectionStatus(): Promise<boolean> {
  try {
    return await app.IsConnected();
  } catch (e) {
    console.error('isConnected failed', e);
    return false;
  }
}

/**
 * Schema API calls
 */
export async function fetchConfigSchema(): Promise<any> {
  try {
    const schemaStr = await app.GetConfigSchema();
    return JSON.parse(schemaStr);
  } catch (e) {
    console.error('getConfigSchema failed', e);
    throw e;
  }
} 