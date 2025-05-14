<script lang="ts">
  import { schemaStore, configStore } from '../stores';
  import { notifications } from '../stores/notification';
  import { persistConfig } from '../services/api';
  import Spinner from '../components/Spinner.svelte';
  import type { Config, Schema } from '../stores';

  let schema: Schema | null;
  let config: Config;
  let saving = false;

  // Subscribe to stores
  schemaStore.subscribe((value: Schema | null) => {
    schema = value;
  });
  
  configStore.subscribe((value: Config) => {
    config = value;
  });

  // Handle save button click
  async function handleSave() {
    if (!config) return;
    
    saving = true;
    
    try {
      await persistConfig(config);
      notifications.add('Configuration saved successfully', 'success');
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      notifications.add(`Error saving configuration: ${errorMsg}`, 'error');
    } finally {
      saving = false;
    }
  }

  // Validate numerical input based on schema constraints
  function isValidInput(key: string, value: number): boolean {
    if (!schema?.properties[key]) return true;
    
    const prop = schema.properties[key];
    
    if (prop.type === 'number' || prop.type === 'integer') {
      if (prop.minimum !== undefined && value < prop.minimum) return false;
      if (prop.maximum !== undefined && value > prop.maximum) return false;
    }
    
    return true;
  }

  // Compute form validity
  $: isFormValid = Object.entries(schema?.properties || {}).every(([key, prop]) => {
    if (prop.type === 'number' || prop.type === 'integer') {
      return isValidInput(key, config[key]);
    }
    return true;
  });
</script>

<div>
  {#if schema}
    <h2 class="text-xl font-bold mb-4">Trading Strategy Configuration</h2>

    <form class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
      {#each Object.entries(schema.properties) as [key, prop]}
        <!-- Skip connection parameters as they're in the connection tab -->
        {#if !['host', 'port', 'client_id'].includes(key)}
          <div class="mb-2">
            <label class="block font-medium mb-1">{prop.title || key}</label>
            
            {#if prop.type === 'integer' || prop.type === 'number'}
              <input
                type="number"
                step={prop.type === 'number' ? '0.01' : '1'}
                bind:value={config[key]}
                min={prop.minimum}
                max={prop.maximum}
                class="border p-2 w-full rounded shadow-sm"
                class:border-red-500={!isValidInput(key, config[key])}
              />
              {#if !isValidInput(key, config[key])}
                <p class="text-sm text-red-500 mt-1">
                  {#if prop.minimum !== undefined && prop.maximum !== undefined}
                    Value must be between {prop.minimum} and {prop.maximum}
                  {:else if prop.minimum !== undefined}
                    Value must be at least {prop.minimum}
                  {:else if prop.maximum !== undefined}
                    Value must be at most {prop.maximum}
                  {/if}
                </p>
              {/if}
            {:else if prop.enum}
              <select bind:value={config[key]} class="border p-2 w-full rounded shadow-sm">
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
      on:click={handleSave} 
      disabled={!isFormValid || saving}
      class="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded shadow-sm disabled:bg-gray-400 transition"
    >
      {#if saving}
        <span class="inline-flex items-center">
          <Spinner size="sm" color="#ffffff" />
          <span class="ml-2">Saving...</span>
        </span>
      {:else}
        Save Configuration
      {/if}
    </button>
  {:else}
    <div class="p-4 bg-blue-50 border border-blue-200 rounded">
      Loading configuration schema...
    </div>
  {/if}
</div> 