import { render, fireEvent, waitFor } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MonitoringTab from './MonitoringTab.svelte';
import { SignalType } from '../stores';

// Mock the wails Go bindings
vi.mock('../../wailsjs/go/main/App', () => {
  return {
    scanSignals: vi.fn().mockResolvedValue([
      {
        symbol: 'AAPL',
        signal: SignalType.CALL_DEBIT,
        timestamp: Date.now()
      },
      {
        symbol: 'MSFT',
        signal: SignalType.PUT_DEBIT,
        timestamp: Date.now() - 5 * 60 * 1000
      }
    ]),
    getPositions: vi.fn().mockResolvedValue([
      {
        symbol: 'AAPL',
        quantity: 100,
        avgPrice: 180.5,
        unrealizedPnL: 250.75
      },
      {
        symbol: 'MSFT',
        quantity: -50,
        avgPrice: 320.25,
        unrealizedPnL: -125.3
      }
    ]),
    pauseScanning: vi.fn(),
    resumeScanning: vi.fn()
  };
});

describe('MonitoringTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders signal and position data', async () => {
    const { getByText, getAllByRole } = render(MonitoringTab);
    
    // Wait for data to load
    await waitFor(() => {
      // Check for signal data
      expect(getByText('AAPL')).toBeTruthy();
      expect(getByText('MSFT')).toBeTruthy();
      
      // Check for positions
      const rows = getAllByRole('row');
      expect(rows.length).toBeGreaterThan(0);
    });
  });

  it('handles pause and resume scanning', async () => {
    const { getByText } = render(MonitoringTab);
    
    // Click pause button
    const pauseButton = getByText('Pause Scanning');
    await fireEvent.click(pauseButton);
    
    // Verify pause was called
    expect(pauseScanning).toHaveBeenCalled();
    
    // Button should now say "Resume Scanning"
    await waitFor(() => {
      expect(getByText('Resume Scanning')).toBeTruthy();
    });
    
    // Click resume button
    const resumeButton = getByText('Resume Scanning');
    await fireEvent.click(resumeButton);
    
    // Verify resume was called
    expect(resumeScanning).toHaveBeenCalled();
  });

  it('handles errors gracefully', async () => {
    // Override mock to simulate error
    scanSignals.mockRejectedValueOnce(new Error('Network error'));
    
    const { getByText } = render(MonitoringTab);
    
    // Wait for error message
    await waitFor(() => {
      expect(getByText('Network error')).toBeTruthy();
    });
  });
}); 