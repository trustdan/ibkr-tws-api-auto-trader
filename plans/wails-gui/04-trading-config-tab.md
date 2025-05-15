# 04-trading-config-tab.md

## 1. Overview

The Trading Config Tab provides a dynamic form for adjusting strategy parameters in real-time. Users can fine-tune not only core strategy parameters but also crucial price execution settings to ensure optimal trade execution:

- **SMA Period** (e.g., 50 days)
- **Candle Count** (e.g., 2 candles)
- **OTM Offset** (number of strikes out-of-the-money)
- **IV Threshold** (percentile for switching to credit spreads)
- **Minimum Reward/Risk Ratio**
- **Maximum % Distance between Bid and Ask** (ensures favorable pricing)
- **Order Type** (Market, Limit, or Mid-price Limit orders)
- **Price Improvement Percentage** (minimum improvement on mid-price for limit orders)

The form is generated dynamically from the JSON schema in `schemaStore`, and changes made via the UI update `configStore`, immediately propagating to the backend when saved.

## 2. Svelte Component Structure

Create `frontend/src/tabs/TradingConfigTab.svelte`:

```svelte
<script>
  import { schemaStore, configStore } from '../stores';
  import { saveConfig } from '../../wailsjs/go/main/App';

  let schema;
  let config;

  schemaStore.subscribe(value => (schema = value));
  configStore.subscribe(value => (config = value));

  async function handleSave() {
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
          {#if prop.type === 'integer' || prop.type === 'number'}
            <input
              type="number"
              step={prop.type === 'number' ? '0.01' : '1'}
              bind:value={config[key]}
              min={prop.minimum}
              max={prop.maximum}
              class="border p-1 w-full"
            />
          {:else if prop.enum}
            <select bind:value={config[key]} class="border p-1 w-full">
              {#each prop.enum as option}
                <option value={option}>{option}</option>
              {/each}
            </select>
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

- Numeric fields enforce `minimum`/`maximum` from schema.
- Save button is disabled if required fields have invalid values.
- Provide inline error messages for invalid inputs, especially for bid-ask spreads and price improvement values.

## 4. Testing & Validation

- **Unit Tests**: Verify dynamic rendering, input handling, and state updates.
- **Integration Tests**: Simulate saving configurations and validate the JSON sent to the backend.

## 5. Cucumber Scenarios

```gherkin
Feature: Trading Configuration Tab
  Scenario: Render dynamic fields including execution parameters
    Given schemaStore has execution properties [max_bid_ask_distance, order_type]
    When TradingConfigTab is rendered
    Then input fields for "Maximum % Distance between Bid and Ask" and a dropdown for "Order Type" appear

  Scenario: Validate bid-ask distance
    Given user inputs a max_bid_ask_distance of -1
    Then an inline validation error is displayed

  Scenario: Save execution parameters
    Given valid execution parameters in configStore
    When user clicks "Save"
    Then saveConfig receives correct JSON including max_bid_ask_distance and order_type
```

## 6. Pseudocode Outline

```text
// On initialization
schema = await getConfigSchema();
schemaStore.set(schema);
configStore.set(initialDefaults);

// Handle form input
update configStore with new values;

// Validate input
show inline errors if inputs are invalid;

// Save configuration
onSave():
  saveConfig(JSON.stringify(configStore));
  notifyUser("Configuration saved");
```
