<script lang="ts">
  import { onMount } from 'svelte';
  import { schemaStore, configStore, statusStore } from './stores';
  import ConnectionTab from './tabs/ConnectionTab.svelte';
  import TradingConfigTab from './tabs/TradingConfigTab.svelte';
  import MonitoringTab from './tabs/MonitoringTab.svelte';
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
      loading = false;
    }
  });

  // Tab switching
  function setActiveTab(tab: string) {
    activeTab = tab;
  }
</script>

<main>
  <div class="app">
    <h1>TraderAdmin</h1>
    
    {#if loading}
      <div class="loading">Loading application...</div>
    {:else if error}
      <div class="error">Error: {error}</div>
    {:else}
      <div class="flex">
        <div class="w-48 min-h-screen border-r p-4">
          <nav>
            <ul>
              <li>
                <button 
                  class="w-full text-left p-2 rounded" 
                  class:bg-blue-100={activeTab === 'connection'} 
                  on:click={() => setActiveTab('connection')}>Connection</button>
              </li>
              <li>
                <button 
                  class="w-full text-left p-2 rounded" 
                  class:bg-blue-100={activeTab === 'config'} 
                  on:click={() => setActiveTab('config')}>Strategy Config</button>
              </li>
              <li>
                <button 
                  class="w-full text-left p-2 rounded" 
                  class:bg-blue-100={activeTab === 'monitoring'} 
                  on:click={() => setActiveTab('monitoring')}>Monitoring</button>
              </li>
            </ul>
          </nav>
        </div>
        <div class="flex-1 p-4">
          {#if activeTab === 'connection'}
            <ConnectionTab />
          {:else if activeTab === 'config'}
            <TradingConfigTab />
          {:else if activeTab === 'monitoring'}
            <MonitoringTab />
          {/if}
        </div>
      </div>
    {/if}
  </div>
</main>

<style>
  main {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    padding: 1em;
    max-width: 1200px;
    margin: 0 auto;
    color: #333;
  }
  
  .app {
    text-align: center;
  }
  
  h1 {
    color: #0366d6;
    margin-bottom: 1em;
  }
  
  h2 {
    margin-top: 0;
  }
  
  .loading, .error {
    padding: 1em;
    border-radius: 4px;
    margin: 2em 0;
  }
  
  .loading {
    background-color: #f0f8ff;
    border: 1px solid #b3d9ff;
  }
  
  .error {
    background-color: #fff0f0;
    border: 1px solid #ffb3b3;
    color: #d00;
  }
  
  .tabs {
    display: flex;
    border-bottom: 1px solid #ddd;
    margin-bottom: 2em;
  }
  
  .tab {
    padding: 0.75em 1.5em;
    cursor: pointer;
    border-bottom: 2px solid transparent;
  }
  
  .tab:hover {
    background-color: #f5f5f5;
  }
  
  .tab.active {
    border-bottom: 2px solid #0366d6;
    font-weight: bold;
  }
  
  .connection-panel, .strategy-panel, .monitor-panel {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 1.5em;
    text-align: left;
    max-width: 600px;
    margin: 0 auto;
  }
  
  .status-bar {
    background-color: #ffeeee;
    color: #cc0000;
    padding: 0.75em;
    border-radius: 4px;
    margin-bottom: 1.5em;
    font-weight: bold;
  }
  
  .status-bar.connected {
    background-color: #eeffee;
    color: #007700;
  }
  
  .form-group {
    margin-bottom: 1em;
  }
  
  label {
    display: block;
    margin-bottom: 0.5em;
    font-weight: bold;
  }
  
  input {
    width: 100%;
    padding: 0.5em;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1em;
  }
  
  button {
    background-color: #0366d6;
    color: white;
    border: none;
    padding: 0.75em 1.5em;
    font-size: 1em;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 1em;
  }
  
  button:hover {
    background-color: #0353b4;
  }
</style> 