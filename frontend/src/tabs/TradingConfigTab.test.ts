import { render, fireEvent, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import TradingConfigTab from './TradingConfigTab.svelte';
import { schemaStore, configStore } from '../stores';

// Mock the Go backend functions
vi.mock('../../wailsjs/go/main/App', () => ({
  SaveConfig: vi.fn().mockResolvedValue(true)
}));

describe('TradingConfigTab', () => {
  beforeEach(() => {
    // Set up test schema and configuration
    const testSchema = {
      properties: {
        sma_period: {
          type: 'integer',
          title: 'SMA Period',
          description: 'Period for SMA',
          minimum: 1,
          maximum: 200,
          default: 50
        },
        candle_count: {
          type: 'integer',
          title: 'Candle Count',
          description: 'Number of candles',
          minimum: 1,
          maximum: 10,
          default: 2
        }
      },
      required: ['sma_period', 'candle_count']
    };
    
    const testConfig = {
      host: 'localhost',
      port: 7497,
      client_id: 1,
      sma_period: 50,
      candle_count: 2
    };
    
    schemaStore.set(testSchema);
    configStore.set(testConfig);
  });

  test('renders form based on schema', () => {
    render(TradingConfigTab);
    
    // Check form elements
    expect(screen.getByLabelText(/SMA Period:/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Candle Count:/i)).toBeInTheDocument();
    
    // Check default values
    expect(screen.getByLabelText(/SMA Period:/i)).toHaveValue('50');
    expect(screen.getByLabelText(/Candle Count:/i)).toHaveValue('2');
  });

  test('validates form input', async () => {
    render(TradingConfigTab);
    
    // Set invalid value
    await fireEvent.input(screen.getByLabelText(/SMA Period:/i), {
      target: { value: '0' }
    });
    
    // Should show validation error
    expect(screen.getByText(/Minimum value is 1/i)).toBeInTheDocument();
    
    // Save button should be disabled
    expect(screen.getByRole('button', { name: /Save Configuration/i })).toBeDisabled();
  });

  test('saves configuration', async () => {
    const { SaveConfig } = await import('../../wailsjs/go/main/App');
    render(TradingConfigTab);
    
    // Change SMA period
    await fireEvent.input(screen.getByLabelText(/SMA Period:/i), {
      target: { value: '100' }
    });
    
    // Click save button
    await fireEvent.click(screen.getByRole('button', { name: /Save Configuration/i }));
    
    // Should call SaveConfig with updated config
    expect(SaveConfig).toHaveBeenCalled();
    const savedConfig = JSON.parse(vi.mocked(SaveConfig).mock.calls[0][0]);
    expect(savedConfig.sma_period).toBe(100);
    
    // Success message should be shown
    expect(screen.getByText(/Configuration saved successfully/i)).toBeInTheDocument();
  });
}); 