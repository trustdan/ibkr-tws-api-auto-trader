<script lang="ts">
  import { onMount } from 'svelte';
  import { schemaStore, configStore, statusStore } from './stores';
  import { notifications } from './stores/notification';
  import ConnectionTab from './tabs/ConnectionTab.svelte';
  import TradingConfigTab from './tabs/TradingConfigTab.svelte';
  import MonitoringTab from './tabs/MonitoringTab.svelte';
  import NotificationContainer from './components/NotificationContainer.svelte';
  import VersionDisplay from './components/VersionDisplay.svelte';
  import { fetchConfigSchema, checkConnectionStatus } from './services/api';

  let activeTab = 'connection';
  let loading = true;
  let error: string | null = null;

  // Initialize status and config when app mounts
  onMount(async () => {
    try {
      // Load schema
      const schema = await fetchConfigSchema();
      schemaStore.set(schema);
      
      // Check connection status on startup
      const connected = await checkConnectionStatus();
      statusStore.set({ 
        connected
      });
      
      loading = false;
    } catch (err) {
      console.error("Initialization error:", err);
      statusStore.set({ 
        connected: false, 
        error: err instanceof Error ? err.message : String(err)
      });
      error = err instanceof Error ? err.message : String(err);
      notifications.add(
        err instanceof Error ? err.message : String(err),
        'error'
      );
      loading = false;
    }
  });

  // Tab switching
  function setActiveTab(tab: string) {
    activeTab = tab;
  }
</script>

<main class="bg-gray-100 min-h-screen">
  <NotificationContainer />
  <div class="max-w-6xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-center mb-6">TraderAdmin</h1>
    
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
            <ConnectionTab />
          {:else if activeTab === 'config'}
            <TradingConfigTab />
          {:else if activeTab === 'monitoring'}
            <MonitoringTab />
          {/if}
        </div>
      </div>
      
      <!-- Footer with version -->
      <div class="mt-4 text-right">
        <VersionDisplay />
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