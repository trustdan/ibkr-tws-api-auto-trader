<script lang="ts">
  import { schemaStore, configStore, updateConfig } from '../stores/index';
  
  export let section: 'ibkr' | 'strategy' = 'strategy';
  
  // Get a human-readable label from a camelCase or snake_case field name
  function formatLabel(key: string): string {
    // Convert snake_case or camelCase to Title Case with spaces
    return key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
  }
  
  // Handle input changes
  function handleChange(path: string, event: Event, type: string) {
    const target = event.target as HTMLInputElement;
    let value: any;
    
    if (type === 'boolean') {
      value = target.checked;
    } else if (type === 'number' || type === 'integer') {
      value = target.value === '' ? null : Number(target.value);
    } else {
      value = target.value;
    }
    
    updateConfig(path, value);
  }
</script>

{#if $schemaStore && $schemaStore.properties && $schemaStore.properties[section]}
  <div class="config-form">
    <h3>{formatLabel(section)} Configuration</h3>
    
    {#each Object.entries($schemaStore.properties[section].properties || {}) as [key, field]}
      {@const path = `${section}.${key}`}
      {@const value = $configStore[section][key]}
      {@const type = field.type}
      
      <div class="form-group">
        <label for={path}>{formatLabel(key)}:</label>
        
        {#if field.description}
          <div class="description">{field.description}</div>
        {/if}
        
        {#if type === 'boolean'}
          <div class="switch-container">
            <label class="switch">
              <input 
                type="checkbox" 
                id={path} 
                checked={value} 
                on:change={e => handleChange(path, e, type)}
              />
              <span class="slider"></span>
            </label>
            <span class="toggle-label">{value ? 'Enabled' : 'Disabled'}</span>
          </div>
        {:else if type === 'string'}
          <input 
            type="text" 
            id={path} 
            value={value} 
            on:input={e => handleChange(path, e, type)}
            placeholder={field.default !== undefined ? `Default: ${field.default}` : ''}
          />
        {:else if type === 'number' || type === 'integer'}
          <input 
            type="number" 
            id={path} 
            value={value} 
            min={field.minimum} 
            max={field.maximum}
            step={type === 'integer' ? 1 : 0.1}
            on:input={e => handleChange(path, e, type)}
            placeholder={field.default !== undefined ? `Default: ${field.default}` : ''}
          />
        {:else if type === 'array'}
          <div class="not-implemented">Array editing not implemented yet</div>
        {:else if type === 'object'}
          <div class="not-implemented">Object editing not implemented yet</div>
        {:else}
          <div class="not-implemented">Unknown type: {type}</div>
        {/if}
      </div>
    {/each}
  </div>
{:else}
  <div class="loading">Loading schema...</div>
{/if}

<style>
  .config-form {
    background-color: #f9f9f9;
    padding: 1.5em;
    border-radius: 8px;
    max-width: 600px;
    margin: 0 auto;
  }
  
  h3 {
    margin-top: 0;
    color: #333;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.5em;
    margin-bottom: 1em;
  }
  
  .form-group {
    margin-bottom: 1.5em;
  }
  
  label {
    display: block;
    font-weight: bold;
    margin-bottom: 0.3em;
  }
  
  .description {
    font-size: 0.85em;
    color: #666;
    margin-bottom: 0.5em;
  }
  
  input[type="text"],
  input[type="number"] {
    width: 100%;
    padding: 0.5em;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1em;
  }
  
  input:focus {
    border-color: #0366d6;
    outline: none;
    box-shadow: 0 0 0 2px rgba(3, 102, 214, 0.2);
  }
  
  .not-implemented {
    padding: 0.5em;
    background-color: #ffeebb;
    border-radius: 4px;
    font-style: italic;
    color: #775500;
  }
  
  .loading {
    padding: 1em;
    text-align: center;
    color: #666;
  }
  
  /* Switch/toggle styling */
  .switch-container {
    display: flex;
    align-items: center;
  }
  
  .switch {
    position: relative;
    display: inline-block;
    width: 48px;
    height: 24px;
  }
  
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .3s;
    border-radius: 24px;
  }
  
  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .3s;
    border-radius: 50%;
  }
  
  input:checked + .slider {
    background-color: #0366d6;
  }
  
  input:focus + .slider {
    box-shadow: 0 0 1px #0366d6;
  }
  
  input:checked + .slider:before {
    transform: translateX(24px);
  }
  
  .toggle-label {
    margin-left: 0.75em;
  }
</style> 