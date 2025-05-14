# 03-connection-tab.md

## 1. Overview

The Connection Tab in the Wails GUI allows users to configure and manage the IBKR TWS connection.  It provides:

* **Form Inputs**: Host, Port, Client ID fields bound to `configStore`
* **Connect/Disconnect Button**: triggers `connectIbkr` and `disconnectIbkr` Go backend bindings
* **Status Indicator**: shows live connection status via `statusStore`
* **Validation**: ensures host/port inputs are non-empty and port is a valid number

This module wires the frontend UI to the Go backend’s IBKR connector and surfaces real-time status.

## 2. Svelte Component Structure

Create `frontend/src/tabs/ConnectionTab.svelte`:

```svelte
<script>
  import { configStore, statusStore } from '../stores';
  import { connectIbkr, disconnectIbkr } from '../../wailsjs/go/main/App';
  import { get } from 'svelte/store';

  let config;
  let status;
  configStore.subscribe(value => (config = value));
  statusStore.subscribe(value => (status = value));

  async function handleConnect() {
    const success = await connectIbkr(config.host, config.port, config.client_id);
    statusStore.set({ connected: success });
  }

  async function handleDisconnect() {
    await disconnectIbkr();
    statusStore.set({ connected: false });
  }
</script>

<div class="p-4">
  <h2 class="text-xl font-bold">IBKR Connection</h2>
  <div class="grid grid-cols-2 gap-4 mt-2">
    <div>
      <label>Host:</label>
      <input type="text" bind:value={config.host} class="border p-1 w-full" />
    </div>
    <div>
      <label>Port:</label>
      <input type="number" bind:value={config.port} class="border p-1 w-full" />
    </div>
    <div>
      <label>Client ID:</label>
      <input type="number" bind:value={config.client_id} class="border p-1 w-full" />
    </div>
  </div>
  <div class="mt-4">
    {#if status.connected}
      <span class="text-green-600 font-semibold">Connected</span>
      <button on:click={handleDisconnect} class="ml-4 p-2 bg-red-500 text-white rounded">Disconnect</button>
    {:else}
      <span class="text-red-600 font-semibold">Disconnected</span>
      <button on:click={handleConnect} class="ml-4 p-2 bg-green-500 text-white rounded">Connect</button>
    {/if}
  </div>
</div>
```

## 3. Validation & UX

* **Port Validation**: Svelte automatically enforces numeric input; consider showing an error message if port ≤ 0 or > 65535.
* **Disabled States**: disable Connect button if missing config fields; show spinner during connect/disconnect operations.

## 4. Testing & Validation

* **Unit Test**: use `@testing-library/svelte` to render `ConnectionTab`, simulate user input, and mock `connectIbkr` binding to assert `statusStore` updates.
* **Integration**: run Wails desktop build, enter real TWS credentials, verify connection toggles status indicator.

## 5. Cucumber Scenarios

```gherkin
Feature: Connection Tab Functionality
  Scenario: Successful connection flow
    Given the GUI is open
    And configStore.host=localhost, port=7497, client_id=1
    When I click "Connect"
    And the backend returns success
    Then statusStore.connected == true
    And the UI shows "Connected"

  Scenario: Disconnect flow
    Given statusStore.connected == true
    When I click "Disconnect"
    Then statusStore.connected == false
    And the UI shows "Disconnected"

  Scenario: Validation prevents connect
    Given configStore.port is empty
    When I view the Connect button
    Then the Connect button is disabled
```

## 6. Pseudocode Outline

```text
// On user click Connect
def handleConnect():
  if config.host && config.port > 0:
    success = connectIbkr(config.host, config.port, config.client_id)
    statusStore.set({connected:success})

// Reactively update UI based on statusStore.connected
```
