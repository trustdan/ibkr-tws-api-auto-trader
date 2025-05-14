<script lang="ts">
  import { schemaStore, configStore } from '../stores';
  import { persistConfig } from '../services/api';
  import { get } from 'svelte/store';

  let schema: any;
  let config: any;
  let saving = false;
  let saveSuccess = false;
  let saveError: string | null = null;

  schemaStore.subscribe(value => (schema = value));
  configStore.subscribe(value => (config = value));

  async function handleSave() {
    try {
      saving = true;
      saveSuccess = false;
      saveError = null;
      
      // Persist config via API
      await persistConfig(config);
      
      saveSuccess = true;
      setTimeout(() => {
        saveSuccess = false;
      }, 3000); // Hide success message after 3 seconds
    } catch (err: unknown) {
      saveError = err instanceof Error ? err.message : 'Failed to save configuration';
      console.error('Error saving config:', err);
    } finally {
      saving = false;
    }
  }

  function isValid(key: string, value: any): boolean {
    if (!schema || !schema.properties[key]) return true;
    
    const prop = schema.properties[key];
    
    if (prop.type === 'number' || prop.type === 'integer') {
      if (value === null || value === undefined || value === '') return false;
      if (typeof prop.minimum === 'number' && value < prop.minimum) return false;
      if (typeof prop.maximum === 'number' && value > prop.maximum) return false;
    }
    
    return true;
  }

  $: formValid = schema && Object.keys(schema.properties).every(key => 
    !schema?.required?.includes(key) || isValid(key, config?.[key]));
</script>

<div class="p-4">
  {#if schema}
    <h2 class="text-xl font-bold">Trading Strategy Configuration</h2>
    
    {#if saveSuccess}
      <div class="mt-4 p-3 bg-green-100 text-green-700 border border-green-200 rounded">
        Configuration saved successfully!
      </div>
    {/if}
    
    {#if saveError}
      <div class="mt-4 p-3 bg-red-100 text-red-700 border border-red-200 rounded">
        Error: {saveError}
      </div>
    {/if}
    
    <form class="grid grid-cols-2 gap-4 mt-4">
      {#each Object.entries(schema.properties) as [key, prop]}
        <div>
          <label class="block font-medium">{prop.title || key}</label>
          {#if prop.type === 'integer'}
            <input
              type="number"
              bind:value={config[key]}
              min={prop.minimum}
              max={prop.maximum}
              class="border p-1 w-full"
            />
          {:else if prop.type === 'number'}
            <input
              type="number"
              step="0.01"
              bind:value={config[key]}
              min={prop.minimum}
              max={prop.maximum}
              class="border p-1 w-full"
            />
          {:else if prop.type === 'string'}
            <input
              type="text"
              bind:value={config[key]}
              class="border p-1 w-full"
            />
          {/if}
          {#if prop.description}
            <p class="text-sm text-gray-600">{prop.description}</p>
          {/if}
        </div>
      {/each}
    </form>
    
    <button 
      on:click={handleSave} 
      class="mt-6 p-2 bg-blue-600 text-white rounded"
      disabled={saving}
    >
      {saving ? 'Saving...' : 'Save'}
    </button>
  {:else}
    <p>Loading configuration schema...</p>
  {/if}
</div> 