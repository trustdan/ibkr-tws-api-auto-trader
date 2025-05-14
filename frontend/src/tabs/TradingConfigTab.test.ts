import { vi, describe, it, expect, afterEach, beforeEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import TradingConfigTab from './TradingConfigTab.svelte';
import { schemaStore, configStore } from '../stores';
import type { Schema } from '../stores';

// Mock API service
vi.mock('../services/api', () => ({
  persistConfig: vi.fn().mockResolvedValue(undefined)
}));

describe('TradingConfigTab', () => {
  // Sample schema for testing
  const testSchema: Schema = {
    properties: {
      sma_period: {
        type: 'integer',
        title: 'SMA Period',
        description: 'Period for Simple Moving Average calculation (days)',
        default: 50,
        minimum: 1,
        maximum: 200
      },
      candle_count: {
        type: 'integer',
        title: 'Candle Count',
        description: 'Number of candles to evaluate for pattern',
        default: 2,
        minimum: 1,
        maximum: 10
      },
      iv_threshold: {
        type: 'number',
        title: 'IV Threshold',
        description: 'IV percentile threshold (0.0-1.0)',
        default: 0.7,
        minimum: 0.0,
        maximum: 1.0
      },
      order_type: {
        type: 'string',
        title: 'Order Type',
        description: 'Type of order to place',
        enum: ['Market', 'Limit', 'MidPrice']
      }
    },
    required: ['sma_period', 'candle_count', 'iv_threshold']
  };

  beforeEach(() => {
    // Set up schema and config stores with test data
    schemaStore.set(testSchema);
    configStore.set({
      host: 'localhost',
      port: 7497,
      client_id: 1,
      sma_period: 50,
      candle_count: 2,
      iv_threshold: 0.7,
      order_type: 'Limit'
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('renders form with values from configStore', () => {
    render(TradingConfigTab);
    
    // Check that form fields are rendered with correct values
    expect(screen.getByLabelText(/SMA Period/i)).toHaveValue(50);
    expect(screen.getByLabelText(/Candle Count/i)).toHaveValue(2);
    expect(screen.getByLabelText(/IV Threshold/i)).toHaveValue(0.7);
  });

  it('validates number inputs based on schema constraints', async () => {
    render(TradingConfigTab);
    
    // Update SMA period to invalid value
    const smaInput = screen.getByLabelText(/SMA Period/i);
    await fireEvent.input(smaInput, { target: { value: '0' } });
    
    // Check for validation message
    expect(screen.getByText(/Value must be at least 1/i)).toBeInTheDocument();
    
    // Save button should be disabled
    expect(screen.getByRole('button', { name: /Save Configuration/i })).toBeDisabled();
  });

  it('updates configStore when form values change', async () => {
    render(TradingConfigTab);
    
    // Update SMA period
    const smaInput = screen.getByLabelText(/SMA Period/i);
    await fireEvent.input(smaInput, { target: { value: '100' } });
    
    // Check that store was updated
    let currentConfig;
    const unsubscribe = configStore.subscribe(value => {
      currentConfig = value;
    });
    
    expect(currentConfig.sma_period).toBe(100);
    unsubscribe();
  });

  it('calls persistConfig when save button is clicked', async () => {
    const { persistConfig } = await import('../services/api');
    render(TradingConfigTab);
    
    // Click save button
    const saveButton = screen.getByRole('button', { name: /Save Configuration/i });
    await fireEvent.click(saveButton);
    
    // Check that persistConfig was called with correct data
    expect(persistConfig).toHaveBeenCalledTimes(1);
    expect(persistConfig).toHaveBeenCalledWith(
      expect.objectContaining({
        sma_period: 50,
        candle_count: 2,
        iv_threshold: 0.7
      })
    );
  });

  it('shows success message when save is successful', async () => {
    render(TradingConfigTab);
    
    // Click save button
    const saveButton = screen.getByRole('button', { name: /Save Configuration/i });
    await fireEvent.click(saveButton);
    
    // Check for success message
    expect(screen.getByText(/Configuration saved successfully/i)).toBeInTheDocument();
  });

  it('shows error message when save fails', async () => {
    const { persistConfig } = await import('../services/api');
    vi.mocked(persistConfig).mockRejectedValueOnce(new Error('Failed to save'));
    
    render(TradingConfigTab);
    
    // Click save button
    const saveButton = screen.getByRole('button', { name: /Save Configuration/i });
    await fireEvent.click(saveButton);
    
    // Check for error message
    expect(screen.getByText(/Error saving configuration: Failed to save/i)).toBeInTheDocument();
  });
}); 