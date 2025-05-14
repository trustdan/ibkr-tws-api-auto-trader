# 06-frontend-integration.md

## 1. Overview

This document details how the Svelte frontend communicates with our Go backend (via Wails bindings) and Python orchestrator (via gRPC/HTTP through Go).  It covers:

* Invoking backend methods for scanning, trading, and config persistence
* Error propagation from backend to UI
* Managing asynchronous calls and loading states

## 2. Go Backend Bindings

Ensure Wails `Bindings` in `backend/main.go` include:

```go
Bindings: []interface{}{
  basicEndpoint,
  getConfigSchema,
  connectIbkr,
  disconnectIbkr,
  saveConfig,
  scanSignals,
  getPositions,
  pauseScanning,
  resumeScanning,
},
```

Implement `scanSignals` to call the gRPC `ScannerService.ScanUniverse`, and `getPositions` to call `iv_insync` account positions endpoint.

## 3. Svelte Service Layer

Create `frontend/src/services/api.js`:

```js
import * as app from '../wailsjs/go/main/App';

export async function fetchSignals() {
  try {
    return await app.scanSignals();
  } catch (e) {
    console.error('scanSignals failed', e);
    throw e;
  }
}

export async function fetchPositions() {
  try {
    return await app.getPositions();
  } catch (e) {
    console.error('getPositions failed', e);
    throw e;
  }
}

export async function persistConfig(cfg) {
  return app.saveConfig(JSON.stringify(cfg));
}
```

In each Svelte tab use these services instead of direct bindings for cleaner error handling and mocking.

## 4. Error Handling & Loading States

* Wrap calls with `try/catch`; show error toast if an exception occurs.
* Use a `loading` store or local state boolean to disable buttons and display spinners.

Example in `ConnectionTab.svelte`:

```svelte
let loading = false;

async function handleConnect() {
  loading = true;
  try {
    const success = await connectIbkr(...);
    statusStore.set({ connected: success });
  } catch (err) {
    alert('Connection failed: ' + err.message);
  } finally {
    loading = false;
  }
}
```

## 5. Testing & Validation

* **Unit Tests**: stub `api.js` methods to return promises or throw; verify UI reacts correctly.
* **E2E Tests**: use Playwright/Testing Library to simulate full flows.

## 6. Cucumber Scenarios

```gherkin
Feature: Frontend-to-Backend Integration
  Scenario: Scan and display signals
    Given scanSignals returns [{symbol:"AAPL", signal:"CALL_DEBIT"}]
    When the MonitoringTab mounts
    Then fetchSignals is called
    And the table shows the returned signal

  Scenario: Handle scan errors
    Given scanSignals throws an error
    When MonitoringTab mounts
    Then an error message is displayed to the user

  Scenario: Save config through API
    Given valid configStore
    When user clicks Save
    Then persistConfig is called with correct JSON
```

## 7. Pseudocode Outline

```text
// In app startup:
Bindings: [...]  // include all methods

// In Svelte service:
export async function fetchSignals() {
  return app.scanSignals();
}

// In component:
onMount:
  loading = true
  try:
    data = await fetchSignals()
    signalsStore.set(data)
  catch:
    showError()
  finally:
    loading = false
```
