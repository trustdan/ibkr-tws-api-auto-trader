# 04-trading-config-tab.md

## 1. Overview

The Trading Config Tab provides a dynamic form for adjusting strategy parameters in real-time.  Users can fine-tune:

* **SMA Period** (e.g. 50 days)
* **Candle Count** (e.g. 2 candles)
* **OTM Offset** (number of strikes out-of-the-money)
* **IV Threshold** (percentile for switching to credit spreads)
* **Minimum Reward/Risk Ratio**

The form is generated from the JSON schema in `schemaStore`, and updates to `configStore` propagate immediately to the backend when saved.

## 2. Svelte Component Structure

Create `frontend/src/tabs/TradingConfigTab.svelte`:

```svelte
<script>
  import { schemaStore, configStore } from '../stores';
  import { saveConfig } from '../../wailsjs/go/main/App';
  import { get } from 'svelte/store';

  let schema;
  let config;

  schemaStore.subscribe(value => (schema = value));
  configStore.subscribe(value => (config = value));

  async function handleSave() {
    // Persist config via Go backend
    await saveConfig(JSON.stringify(config));
    alert('Configuration saved');
  }
</script>

<template>
  {#if schema}
    <h2 class="text-xl font-bold">Trading Strategy Configuration</h2>
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
          {/if}
          {#if prop.description}
            <p class="text-sm text-gray-600">{prop.description}</p>
          {/if}
        </div>
      {/each}
    </form>
    <button on:click={handleSave} class="mt-6 p-2 bg-blue-600 text-white rounded">Save</button>
  {:else}
    <p>Loading configuration schema...</p>
  {/if}
</template>
```

## 3. Validation & UX

* Ensure numeric fields respect `minimum`/`maximum` from schema
* Disable Save button until all required fields have valid values
* Provide inline error messages for invalid inputs

## 4. Testing & Validation

* **Unit Tests**: Render `TradingConfigTab` with a mock `schemaStore` and `configStore`; simulate user edits and assert `configStore` updates
* **Integration Tests**: Change a value and click Save; verify `saveConfig` Go binding is called with correct JSON

## 5. Cucumber Scenarios

```gherkin
Feature: Trading Configuration Tab
  Scenario: Render dynamic fields
    Given schemaStore has properties [sma_period, candle_count]
    When TradingConfigTab is rendered
    Then input fields for "SMA Period" and "Candle Count" appear

  Scenario: Update configuration store
    Given configStore contains {sma_period:50}
    When user changes sma_period to 60
    Then configStore.sma_period == 60

  Scenario: Save configuration
    Given configStore has valid values
    When user clicks "Save"
    Then saveConfig is invoked with JSON matching configStore
```

## 6. Pseudocode Outline

```text
// On load:
schema = await getConfigSchema()
schemaStore.set(schema)
configStore.set(defaults)

// On input change:
config[key] = newValue
configStore.set(config)

// On Save:
saveConfig(JSON.stringify(config))
alert("Configuration saved")
```
