import { render, fireEvent, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import ConnectionTab from './ConnectionTab.svelte';
import { configStore, statusStore } from '../stores';

// Mock the Go backend functions
vi.mock('../../wailsjs/go/main/App', () => ({
  ConnectIBKR: vi.fn().mockResolvedValue(true),
  DisconnectIBKR: vi.fn().mockResolvedValue(true)
}));

describe('ConnectionTab', () => {
  beforeEach(() => {
    // Reset stores to default values
    configStore.set({ host: 'localhost', port: 7497, client_id: 1 });
    statusStore.set({ connected: false });
  });

  test('renders connection form with default values', () => {
    render(ConnectionTab);
    
    // Check form elements exist
    expect(screen.getByLabelText(/Host:/i)).toHaveValue('localhost');
    expect(screen.getByLabelText(/Port:/i)).toHaveValue('7497');
    expect(screen.getByLabelText(/Client ID:/i)).toHaveValue('1');
    
    // Check connect button exists and is enabled
    const connectButton = screen.getByRole('button', { name: /Connect/i });
    expect(connectButton).toBeEnabled();
  });

  test('shows disconnected status when not connected', () => {
    render(ConnectionTab);
    expect(screen.getByText(/Disconnected/i)).toBeInTheDocument();
  });

  test('connect button calls ConnectIBKR with form values', async () => {
    const { ConnectIBKR } = await import('../../wailsjs/go/main/App');
    render(ConnectionTab);
    
    // Change form values
    await fireEvent.input(screen.getByLabelText(/Host:/i), {
      target: { value: 'test-host' }
    });
    
    // Click connect button
    await fireEvent.click(screen.getByRole('button', { name: /Connect/i }));
    
    // Check if ConnectIBKR was called with correct params
    expect(ConnectIBKR).toHaveBeenCalledWith('test-host', 7497, 1);
  });

  test('updates status store when connection succeeds', async () => {
    const { ConnectIBKR } = await import('../../wailsjs/go/main/App');
    vi.mocked(ConnectIBKR).mockResolvedValue(true);
    
    render(ConnectionTab);
    await fireEvent.click(screen.getByRole('button', { name: /Connect/i }));
    
    // Check status store was updated
    let currentStatus;
    statusStore.subscribe(value => (currentStatus = value))();
    expect(currentStatus.connected).toBe(true);
  });

  test('shows error when connection fails', async () => {
    const { ConnectIBKR } = await import('../../wailsjs/go/main/App');
    vi.mocked(ConnectIBKR).mockRejectedValue(new Error('Connection error'));
    
    render(ConnectionTab);
    await fireEvent.click(screen.getByRole('button', { name: /Connect/i }));
    
    // Check for error message
    expect(screen.getByText(/Connection error/i)).toBeInTheDocument();
  });
}); 