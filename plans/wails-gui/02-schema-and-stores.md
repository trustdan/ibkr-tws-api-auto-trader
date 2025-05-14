# 02-schema-and-stores.md

## 1. Overview

This document describes how to expose a dynamic JSON schema from our Go backend to the Svelte frontend and set up Svelte stores (`configStore`, `statusStore`) to hold application state.  The GUI will fetch the schema at startup, use it to build dynamic forms, and subscribe to live status updates from the services.

Key tasks:

* Define Go structs for configuration and serialize them into JSON schema
* Expose a Wails binding (or HTTP/gRPC endpoint) to return the JSON schema
* Create Svelte stores for schema and configuration values
* Implement an initialization flow: fetch schema → populate stores → render forms

## 2. Go Backend: Schema Exposure

In `backend/schema.go`:

```go
package main

import (
  "encoding/json"
  "github.com/alecthomas/jsonschema"
)

type StrategyConfig struct {
  SMAPeriod    int     `json:"sma_period" jsonschema:"minimum=1,description=Period for SMA"`
  CandleCount  int     `json:"candle_count" jsonschema:"minimum=1,description=Number of candles to evaluate"`
  OTMOffset    int     `json:"otm_offset" jsonschema:"minimum=0,description=Strikes out-of-the-money"`
  IVThreshold  float64 `json:"iv_threshold" jsonschema:"minimum=0,maximum=1,description=IV percentile threshold"`
  MinRewardRisk float64 `json:"min_reward_risk" jsonschema:"minimum=0,description=Required reward-to-risk ratio"`
}

func getConfigSchema() (string, error) {
  reflector := &jsonschema.Reflector{RequiredFromJSONSchemaTags: true}
  schema := reflector.Reflect(&StrategyConfig{})
  schemaJSON, err := json.Marshal(schema)
  return string(schemaJSON), err
}
```

In `backend/main.go`, bind:

```go
Bindings: []interface{}{basicEndpoint, getConfigSchema},
```

## 3. Svelte Frontend: Stores and Initialization

### 3.1 Stores

Create `frontend/src/stores.js`:

```js
import { writable } from 'svelte/store';

export const schemaStore = writable(null);
export const configStore = writable({});
export const statusStore = writable({ connected: false });
```

### 3.2 Initialization Flow

In `frontend/src/App.svelte`:

```svelte
<script>
import { onMount } from 'svelte';
import { schemaStore, configStore, statusStore } from './stores';
import { getConfigSchema, connectIbkr } from '../wailsjs/go/main/App';

onMount(async () => {
  const schemaJSON = await getConfigSchema();
  schemaStore.set(JSON.parse(schemaJSON));
  // Initialize default config based on schema
  const defaultConfig = {};
  Object.keys(JSON.parse(schemaJSON).properties).forEach(key => {
    defaultConfig[key] = JSON.parse(schemaJSON).properties[key].default || null;
  });
  configStore.set(defaultConfig);
  // Attempt IBKR connection
  const success = await connectIbkr(defaultConfig.host, defaultConfig.port, defaultConfig.client_id);
  statusStore.set({ connected: success });
});
</script>
```

## 4. Testing & Validation

* **Unit Test**: Mock `getConfigSchema` to return a sample schema; verify `schemaStore` and `configStore` populate correctly.
* **Integration Test**: Run Wails dev server; verify form inputs render based on the schema and initial values appear.

## 5. Cucumber Scenarios

```gherkin
Feature: Dynamic Schema & Store Initialization
  Scenario: Fetch and store schema
    Given Wails backend running
    When frontend onMount calls getConfigSchema()
    Then schemaStore contains parsed JSON schema

  Scenario: Initialize configStore defaults
    Given schemaStore set with properties
    When defaultConfig generated
    Then configStore keys match schema properties with default values

  Scenario: IBKR connection status update
    Given configStore has valid host/port/client_id
    When connectIbkr is called
    Then statusStore.connected == true or false based on response
```

## 6. Pseudocode Outline

```text
// Go backend
getConfigSchema() -> JSON schema string

// Svelte frontend
onMount:
  schema = await getConfigSchema()
  schemaStore.set(schema)
  config = buildDefaults(schema)
  configStore.set(config)
  status = await connectIbkr(config.host, config.port, config.client_id)
  statusStore.set({ connected: status })
```
