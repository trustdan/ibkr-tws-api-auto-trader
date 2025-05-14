import { render, fireEvent, waitFor } from '@testing-library/svelte';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MonitoringTab from './MonitoringTab.svelte';
import { SignalType } from '../stores';

// Mock functions
const mockFetchSignals = vi.fn();
const mockFetchPositions = vi.fn();
const mockPauseScanner = vi.fn();
const mockResumeScanner = vi.fn();

// Mock the API services
vi.mock('../services/api', () => {
  return {
    fetchSignals: mockFetchSignals.mockResolvedValue([
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
    fetchPositions: mockFetchPositions.mockResolvedValue([
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
    pauseScanner: mockPauseScanner,
    resumeScanner: mockResumeScanner
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
      expect(getByText('P/L: $250.75')).toBeTruthy();
      expect(getByText('P/L: $-125.30')).toBeTruthy();
    });
  });

  it('displays the P/L chart after loading data', async () => {
    const { getByText, container } = render(MonitoringTab);
    
    // Wait for data to load and chart to render
    await waitFor(() => {
      // First check for the chart heading
      expect(getByText('P/L Over Time')).toBeTruthy();
      
      // Then check if SVG chart is rendered
      const svg = container.querySelector('svg');
      expect(svg).toBeTruthy();
      
      // Check for polyline in the chart
      const polyline = svg?.querySelector('polyline');
      expect(polyline).toBeTruthy();
      
      // Check for current P/L value display
      expect(getByText('Current P/L:')).toBeTruthy();
    });
  });

  it('handles pause and resume scanning', async () => {
    const { getByText } = render(MonitoringTab);
    
    // Click pause button
    const pauseButton = getByText('Pause Scanning');
    await fireEvent.click(pauseButton);
    
    // Verify pause was called
    expect(mockPauseScanner).toHaveBeenCalled();
    
    // Button should now say "Resume Scanning"
    await waitFor(() => {
      expect(getByText('Resume Scanning')).toBeTruthy();
    });
    
    // Click resume button
    const resumeButton = getByText('Resume Scanning');
    await fireEvent.click(resumeButton);
    
    // Verify resume was called
    expect(mockResumeScanner).toHaveBeenCalled();
  });

  it('handles errors gracefully', async () => {
    // Override mock to simulate error
    mockFetchSignals.mockRejectedValueOnce(new Error('Network error'));
    
    const { getByText } = render(MonitoringTab);
    
    // Wait for error message
    await waitFor(() => {
      expect(getByText('Network error')).toBeTruthy();
    });
  });
}); 