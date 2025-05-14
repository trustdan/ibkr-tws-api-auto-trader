<script lang="ts">
  import { configStore, statusStore, type Config } from '../stores';
  import { connectToIBKR, disconnectFromIBKR, checkConnectionStatus } from '../services/api';
  import { get } from 'svelte/store';

  let config: Config;
  let connectionStatus = get(statusStore);
  let connecting = false;
  let error: string | null = null;

  configStore.subscribe(value => {
    config = { ...value };
  });

  statusStore.subscribe(value => {
    connectionStatus = value;
  });

  async function handleConnect() {
    connecting = true;
    error = null;
    
    try {
      const success = await connectToIBKR(
        config.host,
        config.port,
        config.client_id
      );
      
      statusStore.update(current => ({
        ...current,
        connected: success,
        error: success ? undefined : 'Failed to connect'
      }));
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Connection failed';
      console.error('Connection error:', err);
      
      statusStore.update(current => ({
        ...current,
        connected: false,
        error: err instanceof Error ? err.message : 'Connection failed'
      }));
    } finally {
      connecting = false;
    }
  }

  async function handleDisconnect() {
    connecting = true;
    error = null;
    
    try {
      await disconnectFromIBKR();
      
      statusStore.update(current => ({
        ...current,
        connected: false,
        error: undefined
      }));
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Disconnection failed';
      console.error('Disconnection error:', err);
    } finally {
      connecting = false;
    }
  }

  async function refreshStatus() {
    try {
      const isConnected = await checkConnectionStatus();
      
      statusStore.update(current => ({
        ...current,
        connected: isConnected,
        error: undefined
      }));
    } catch (err: unknown) {
      console.error('Status check error:', err);
      
      statusStore.update(current => ({
        ...current,
        connected: false,
        error: err instanceof Error ? err.message : 'Failed to check connection status'
      }));
    }
  }
</script>

<div class="p-4">
  <h2 class="text-xl font-bold">IBKR Connection</h2>
  
  <div class="mt-4">
    <div class="flex items-center">
      <div class="mr-2 h-4 w-4 rounded-full" class:bg-green-500={connectionStatus.connected} class:bg-red-500={!connectionStatus.connected}></div>
      <span class="font-medium">Status: {connectionStatus.connected ? 'Connected' : 'Disconnected'}</span>
    </div>
    
    {#if connectionStatus.error}
      <div class="mt-2 p-3 bg-red-100 text-red-700 border border-red-200 rounded">
        Error: {connectionStatus.error}
      </div>
    {/if}
    
    {#if error}
      <div class="mt-2 p-3 bg-red-100 text-red-700 border border-red-200 rounded">
        Error: {error}
      </div>
    {/if}
  </div>
  
  <div class="mt-6 grid grid-cols-1 gap-4 max-w-md">
    <div>
      <label class="block font-medium">Host</label>
      <input
        type="text"
        bind:value={config.host}
        disabled={connectionStatus.connected || connecting}
        class="border p-2 w-full rounded"
      />
    </div>
    
    <div>
      <label class="block font-medium">Port</label>
      <input
        type="number"
        bind:value={config.port}
        min="1"
        max="65535"
        disabled={connectionStatus.connected || connecting}
        class="border p-2 w-full rounded"
      />
    </div>
    
    <div>
      <label class="block font-medium">Client ID</label>
      <input
        type="number"
        bind:value={config.client_id}
        min="1"
        disabled={connectionStatus.connected || connecting}
        class="border p-2 w-full rounded"
      />
    </div>
  </div>
  
  <div class="mt-6">
    {#if connectionStatus.connected}
      <button
        on:click={handleDisconnect}
        disabled={connecting}
        class="bg-red-600 text-white py-2 px-4 rounded"
      >
        {connecting ? 'Disconnecting...' : 'Disconnect'}
      </button>
    {:else}
      <button
        on:click={handleConnect}
        disabled={connecting}
        class="bg-green-600 text-white py-2 px-4 rounded"
      >
        {connecting ? 'Connecting...' : 'Connect'}
      </button>
    {/if}
    
    <button
      on:click={refreshStatus}
      class="ml-2 bg-gray-200 py-2 px-4 rounded"
    >
      Refresh Status
    </button>
  </div>
</div> 