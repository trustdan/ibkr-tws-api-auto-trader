import { vi, describe, it, expect, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import ConnectionTab from './ConnectionTab.svelte';
import { configStore, statusStore } from '../stores';

// Mock API service
vi.mock('../services/api', () => ({
  connectToIBKR: vi.fn().mockResolvedValue(true),
  disconnectFromIBKR: vi.fn().mockResolvedValue(true)
}));

describe('ConnectionTab', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    
    // Reset stores
    configStore.set({
      host: 'localhost',
      port: 7497,
      client_id: 1
    });
    statusStore.set({ connected: false });
  });

  it('renders connection form', () => {
    render(ConnectionTab);
    
    expect(screen.getByLabelText(/Host:/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Port:/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Client ID:/i)).toBeInTheDocument();
    expect(screen.getByText(/Disconnected/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Connect/i })).toBeInTheDocument();
  });

  it('enables connect button when form is valid', async () => {
    render(ConnectionTab);
    
    const connectButton = screen.getByRole('button', { name: /Connect/i });
    expect(connectButton).not.toBeDisabled();
  });

  it('disables connect button when form is invalid', async () => {
    configStore.set({
      host: '',
      port: 0,
      client_id: -1
    });
    
    render(ConnectionTab);
    
    const connectButton = screen.getByRole('button', { name: /Connect/i });
    expect(connectButton).toBeDisabled();
  });

  it('calls connectToIBKR when connect button is clicked', async () => {
    const { connectToIBKR } = await import('../services/api');
    render(ConnectionTab);
    
    const connectButton = screen.getByRole('button', { name: /Connect/i });
    await fireEvent.click(connectButton);
    
    expect(connectToIBKR).toHaveBeenCalledWith('localhost', 7497, 1);
    expect(screen.getByText(/Connected/i)).toBeInTheDocument();
  });

  it('calls disconnectFromIBKR when disconnect button is clicked', async () => {
    const { disconnectFromIBKR } = await import('../services/api');
    
    // Set connected status
    statusStore.set({ connected: true });
    
    render(ConnectionTab);
    
    // Should show disconnect button
    const disconnectButton = screen.getByRole('button', { name: /Disconnect/i });
    await fireEvent.click(disconnectButton);
    
    expect(disconnectFromIBKR).toHaveBeenCalled();
    expect(screen.getByText(/Disconnected/i)).toBeInTheDocument();
  });

  it('disables form inputs when connected', () => {
    statusStore.set({ connected: true });
    render(ConnectionTab);
    
    expect(screen.getByLabelText(/Host:/i)).toBeDisabled();
    expect(screen.getByLabelText(/Port:/i)).toBeDisabled();
    expect(screen.getByLabelText(/Client ID:/i)).toBeDisabled();
  });

  it('displays error message when connection fails', async () => {
    const { connectToIBKR } = await import('../services/api');
    vi.mocked(connectToIBKR).mockRejectedValueOnce(new Error('Connection failed'));
    
    render(ConnectionTab);
    
    const connectButton = screen.getByRole('button', { name: /Connect/i });
    await fireEvent.click(connectButton);
    
    expect(screen.getByText(/Connection failed/i)).toBeInTheDocument();
    expect(screen.getByText(/Disconnected/i)).toBeInTheDocument();
  });
}); 