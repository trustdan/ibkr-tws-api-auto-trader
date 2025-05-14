<script lang="ts">
  import { configStore, statusStore, type Config, type ConnectionStatus } from '../stores';
  import { notifications } from '../stores/notification';
  import { connectToIBKR, disconnectFromIBKR } from '../services/api';
  import Spinner from '../components/Spinner.svelte';

  let config: Config;
  let status: ConnectionStatus;
  let connecting = false;
  let disconnecting = false;
  
  configStore.subscribe((value: Config) => (config = value));
  statusStore.subscribe((value: ConnectionStatus) => (status = value));

  async function handleConnect() {
    // Only attempt connection if we have valid values
    if (config.host && config.port > 0 && config.client_id >= 0) {
      connecting = true;
      
      try {
        const success = await connectToIBKR(config.host, config.port, config.client_id);
        statusStore.update((current: ConnectionStatus) => ({ ...current, connected: success }));
        
        if (success) {
          notifications.add(`Connected to IBKR at ${config.host}:${config.port}`, 'success');
        } else {
          notifications.add('Connection failed', 'error');
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        statusStore.update((current: ConnectionStatus) => ({ 
          ...current, 
          connected: false,
          error: errorMsg
        }));
        notifications.add(`Connection error: ${errorMsg}`, 'error');
      } finally {
        connecting = false;
      }
    }
  }

  async function handleDisconnect() {
    disconnecting = true;
    
    try {
      await disconnectFromIBKR();
      statusStore.update((current: ConnectionStatus) => ({ ...current, connected: false }));
      notifications.add('Disconnected from IBKR', 'info');
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      statusStore.update((current: ConnectionStatus) => ({ 
        ...current,
        error: errorMsg
      }));
      notifications.add(`Disconnect error: ${errorMsg}`, 'error');
    } finally {
      disconnecting = false;
    }
  }

  // Computed property to check if form is valid
  $: isFormValid = Boolean(config?.host && config?.port > 0 && config?.client_id >= 0);
</script>

<div>
  <h2 class="text-xl font-bold mb-4">IBKR Connection</h2>
  
  {#if status?.error}
    <div class="mb-4 p-3 bg-red-100 text-red-700 border border-red-200 rounded">
      {status.error}
    </div>
  {/if}
  
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <label class="block font-medium mb-1">Host:</label>
        <input 
          type="text" 
          bind:value={config.host} 
          class="border p-2 w-full rounded shadow-sm" 
          placeholder="localhost"
          disabled={status?.connected}
        />
      </div>
      <div>
        <label class="block font-medium mb-1">Port:</label>
        <input 
          type="number" 
          bind:value={config.port} 
          class="border p-2 w-full rounded shadow-sm" 
          min="1"
          max="65535"
          placeholder="7497"
          disabled={status?.connected}
        />
        {#if config?.port !== undefined && (config.port <= 0 || config.port > 65535)}
          <p class="text-sm text-red-500 mt-1">Port must be between 1-65535</p>
        {/if}
      </div>
      <div>
        <label class="block font-medium mb-1">Client ID:</label>
        <input 
          type="number" 
          bind:value={config.client_id} 
          class="border p-2 w-full rounded shadow-sm" 
          min="0"
          placeholder="1"
          disabled={status?.connected}
        />
      </div>
    </div>
  </div>
  
  <div class="flex items-center">
    <div class="flex items-center mr-4">
      {#if status?.connected}
        <span class="inline-flex items-center">
          <span class="inline-block w-3 h-3 rounded-full bg-green-500 mr-2"></span>
          <span class="text-green-600 font-semibold">Connected</span>
        </span>
      {:else}
        <span class="inline-flex items-center">
          <span class="inline-block w-3 h-3 rounded-full bg-red-500 mr-2"></span>
          <span class="text-red-600 font-semibold">Disconnected</span>
        </span>
      {/if}
    </div>
    
    {#if status?.connected}
      <button 
        on:click={handleDisconnect} 
        disabled={disconnecting}
        class="px-6 py-2 bg-red-500 hover:bg-red-600 text-white rounded shadow-sm transition disabled:bg-gray-400"
      >
        {#if disconnecting}
          <span class="inline-flex items-center">
            <Spinner size="sm" color="#ffffff" />
            <span class="ml-2">Disconnecting...</span>
          </span>
        {:else}
          Disconnect
        {/if}
      </button>
    {:else}
      <button 
        on:click={handleConnect} 
        disabled={!isFormValid || connecting}
        class="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded shadow-sm transition disabled:bg-gray-400"
      >
        {#if connecting}
          <span class="inline-flex items-center">
            <Spinner size="sm" color="#ffffff" />
            <span class="ml-2">Connecting...</span>
          </span>
        {:else}
          Connect
        {/if}
      </button>
    {/if}
  </div>
  
  {#if status?.connected}
    <div class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-blue-800 text-sm">
      Connected to IBKR at {config.host}:{config.port} with client ID {config.client_id}
    </div>
  {/if}
</div> 