<script lang="ts">
  import { onMount } from 'svelte';
  import { schemaStore, configStore, statusStore } from './stores';
  import { GetVersion, Status, ConnectIBKR, GetConfigSchema, GetDefaultConfig, GetCurrentConfig, UpdateConfig } from '../wailsjs/go/main/App';

  let activeTab = 'connection';
  let loading = true;
  let error: string | null = null;
  let version = '';

  // Initialize status and config when app mounts
  onMount(async () => {
    try {
      // Load status and version
      const statusText = await Status();
      version = await GetVersion();
      
      // Load schema
      const schemaString = await GetConfigSchema();
      const schema = JSON.parse(schemaString);
      schemaStore.set(schema);
      
      // Load current configuration
      const configString = await GetCurrentConfig();
      const config = JSON.parse(configString);
      configStore.set(config);
      
      // Check connection status
      statusStore.update(current => ({
        ...current,
        connected: false // We don't have IsConnected, so default to false
      }));
      
      loading = false;
    } catch (err) {
      console.error("Initialization error:", err);
      statusStore.update(current => ({ 
        ...current,
        connected: false, 
        error: err instanceof Error ? err.message : String(err)
      }));
      error = err instanceof Error ? err.message : String(err);
      loading = false;
    }
  });

  // Handle connect button click
  async function handleConnect() {
    if ($configStore.host && $configStore.port > 0 && $configStore.client_id >= 0) {
      try {
        const result = await ConnectIBKR($configStore.host, $configStore.port, $configStore.client_id);
        if (result) {
          statusStore.update(current => ({ 
            ...current, 
            connected: true, 
            message: result
          }));
        }
      } catch (error) {
        statusStore.update(current => ({ 
          ...current, 
          connected: false,
          error: error instanceof Error ? error.message : String(error)
        }));
      }
    }
  }

  // Handle disconnect button click
  async function handleDisconnect() {
    // We don't have a DisconnectIBKR method, so just update the status
    statusStore.update(current => ({ 
      ...current, 
      connected: false, 
      message: 'Disconnected from IBKR'
    }));
  }

  // Tab switching
  function setActiveTab(tab: string) {
    activeTab = tab;
  }

  // Handle saving configuration
  async function handleSaveConfig() {
    try {
      const result = await UpdateConfig(JSON.stringify($configStore));
      if (result) {
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error saving config:', error);
      return false;
    }
  }
</script>

<main class="bg-gray-100 min-h-screen">
  <div class="max-w-6xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-center mb-2">TraderAdmin</h1>
    <div class="text-center text-sm text-gray-500 mb-4">Version: {version}</div>
    
    {#if loading}
      <div class="p-6 bg-blue-50 border border-blue-200 rounded text-center">
        <p class="text-lg">Loading application...</p>
      </div>
    {:else if error}
      <div class="p-6 bg-red-50 border border-red-200 rounded text-center text-red-700">
        <p class="text-lg">Error: {error}</p>
      </div>
    {:else}
      <!-- Tab Navigation -->
      <div class="bg-white rounded-t-lg shadow-sm border border-gray-200">
        <div class="flex border-b">
          <button 
            class="py-3 px-6 font-medium focus:outline-none"
            class:text-blue-600={activeTab === 'connection'}
            class:border-b-2={activeTab === 'connection'}
            class:border-blue-600={activeTab === 'connection'}
            on:click={() => setActiveTab('connection')}
          >
            Connection
          </button>
          <button 
            class="py-3 px-6 font-medium focus:outline-none"
            class:text-blue-600={activeTab === 'config'}
            class:border-b-2={activeTab === 'config'}
            class:border-blue-600={activeTab === 'config'}
            on:click={() => setActiveTab('config')}
          >
            Strategy Config
          </button>
          <button 
            class="py-3 px-6 font-medium focus:outline-none"
            class:text-blue-600={activeTab === 'monitoring'}
            class:border-b-2={activeTab === 'monitoring'}
            class:border-blue-600={activeTab === 'monitoring'}
            on:click={() => setActiveTab('monitoring')}
          >
            Monitoring
          </button>
        </div>
      
        <!-- Tab Content -->
        <div class="p-6 bg-white rounded-b-lg">
          {#if activeTab === 'connection'}
            <!-- Connection Tab -->
            <div>
              <h2 class="text-xl font-bold mb-4">IBKR Connection</h2>
              
              {#if $statusStore?.error}
                <div class="mb-4 p-3 bg-red-100 text-red-700 border border-red-200 rounded">
                  {$statusStore.error}
                </div>
              {/if}
              
              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label for="host-input" class="block font-medium mb-1">Host:</label>
                    <input 
                      id="host-input"
                      type="text" 
                      bind:value={$configStore.host} 
                      class="border p-2 w-full rounded shadow-sm" 
                      placeholder="localhost"
                      disabled={$statusStore?.connected}
                    />
                  </div>
                  <div>
                    <label for="port-input" class="block font-medium mb-1">Port:</label>
                    <input 
                      id="port-input"
                      type="number" 
                      bind:value={$configStore.port} 
                      class="border p-2 w-full rounded shadow-sm" 
                      min="1"
                      max="65535"
                      placeholder="7497"
                      disabled={$statusStore?.connected}
                    />
                    {#if $configStore?.port !== undefined && ($configStore.port <= 0 || $configStore.port > 65535)}
                      <p class="text-sm text-red-500 mt-1">Port must be between 1-65535</p>
                    {/if}
                  </div>
                  <div>
                    <label for="client-id-input" class="block font-medium mb-1">Client ID:</label>
                    <input 
                      id="client-id-input"
                      type="number" 
                      bind:value={$configStore.client_id} 
                      class="border p-2 w-full rounded shadow-sm" 
                      min="0"
                      placeholder="1"
                      disabled={$statusStore?.connected}
                    />
                  </div>
                </div>
              </div>
              
              <div class="flex items-center">
                <div class="flex items-center mr-4">
                  {#if $statusStore?.connected}
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
                
                {#if $statusStore?.connected}
                  <button 
                    on:click={handleDisconnect} 
                    class="px-6 py-2 bg-red-500 hover:bg-red-600 text-white rounded shadow-sm transition"
                  >
                    Disconnect
                  </button>
                {:else}
                  <button 
                    on:click={handleConnect} 
                    class="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded shadow-sm transition"
                    disabled={!$configStore?.host || !$configStore?.port || $configStore?.port <= 0 || $configStore?.port > 65535}
                  >
                    Connect
                  </button>
                {/if}
              </div>
              
              {#if $statusStore?.connected && $statusStore?.message}
                <div class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-blue-800 text-sm">
                  {$statusStore.message}
                </div>
              {/if}
            </div>
          {:else if activeTab === 'config'}
            <!-- Trading Config Tab -->
            <div>
              {#if $schemaStore}
                <h2 class="text-xl font-bold mb-4">Trading Strategy Configuration</h2>
                
                <form class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                  {#each Object.entries($schemaStore.properties) as [key, prop]}
                    <!-- Skip connection parameters as they're in the connection tab -->
                    {#if !['host', 'port', 'client_id'].includes(key)}
                      <div class="mb-2">
                        <label for={`input-${key}`} class="block font-medium mb-1">{prop.title || key}</label>
                        
                        {#if prop.type === 'integer' || prop.type === 'number'}
                          <input
                            id={`input-${key}`}
                            type="number"
                            step={prop.type === 'number' ? '0.01' : '1'}
                            bind:value={$configStore[key]}
                            min={prop.minimum}
                            max={prop.maximum}
                            class="border p-2 w-full rounded shadow-sm"
                          />
                        {:else if prop.enum}
                          <select id={`input-${key}`} bind:value={$configStore[key]} class="border p-2 w-full rounded shadow-sm">
                            {#each prop.enum as option}
                              <option value={option}>{option}</option>
                            {/each}
                          </select>
                        {/if}
                        
                        {#if prop.description}
                          <p class="text-sm text-gray-600 mt-1">{prop.description}</p>
                        {/if}
                      </div>
                    {/if}
                  {/each}
                </form>
                
                <button 
                  on:click={handleSaveConfig} 
                  class="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded shadow-sm transition"
                >
                  Save Configuration
                </button>
              {:else}
                <div class="p-4 bg-blue-50 border border-blue-200 rounded">
                  Loading configuration schema...
                </div>
              {/if}
            </div>
          {:else if activeTab === 'monitoring'}
            <!-- Monitoring Tab -->
            <div>
              <h2 class="text-xl font-bold mb-4">Trading Monitor</h2>
              <p class="text-gray-600">Monitoring functionality coming soon...</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen-Sans, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  }
</style>
