import { vi } from 'vitest';

// This file is run before any test
// You can add any global setup code here

// Mock the wailsjs runtime
globalThis.runtime = {
  WindowSetTitle: vi.fn(),
  EventsOn: vi.fn(),
  EventsOff: vi.fn(),
  EventsOnce: vi.fn(),
  EventsEmit: vi.fn(),
  LogPrint: vi.fn(),
  LogDebug: vi.fn(),
  LogInfo: vi.fn(),
  LogWarning: vi.fn(),
  LogError: vi.fn()
} 