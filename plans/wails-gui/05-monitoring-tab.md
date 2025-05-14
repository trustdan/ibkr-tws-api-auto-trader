# 05-monitoring-tab.md

## 1. Overview

The Monitoring Tab provides real-time visualization of trading activity, scanner signals, and account positions.  It integrates:

* **Signal Table**: list of current scan results (`SignalType`, `Symbol`, `Timestamp`) retrieved via Go scanner gRPC or HTTP
* **Positions & P/L**: current open positions and profit/loss from Python orchestrator
* **Pause/Edit/Unpause Controls**: buttons to pause scanning, adjust parameters, and resume
* **Charts**: simple line or bar charts for P/L over time (using a charting library)

This tab subscribes to live updates via WebSockets or polling and renders data reactively in Svelte.

## 2. Svelte Component Structure

Create `frontend/src/tabs/MonitoringTab.svelte`:

```svelte
<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import { scanSignals, getPositions, pauseScanning, resumeScanning } from '../../wailsjs/go/main/App';

  const signals = writable([]);
  const positions = writable([]);
  let paused = false;

  async function fetchData() {
    const sigs = await scanSignals();
    signals.set(sigs);
    const pos = await getPositions();
    positions.set(pos);
  }

  function handlePause() {
    pauseScanning();
    paused = true;
  }
  function handleResume() {
    resumeScanning();
    paused = false;
  }

  onMount(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  });
</script>

<div class="p-4">
  <h2 class="text-xl font-bold">Monitoring Dashboard</h2>
  <div class="mt-4">
    <button on:click={paused ? handleResume : handlePause}
      class="p-2 rounded text-white"
      class:bg-green-500={!paused}
      class:bg-red-500={paused}>
      {paused ? 'Resume' : 'Pause'} Scanning
    </button>
  </div>
  <div class="mt-6">
    <h3 class="font-semibold">Signals</h3>
    <table class="w-full mt-2 border-collapse">
      <thead>
        <tr><th>Symbol</th><th>Signal</th><th>Time</th></tr>
      </thead>
      <tbody>
        {#each $signals as s}
          <tr><td>{s.symbol}</td><td>{s.signal}</td><td>{new Date(s.timestamp).toLocaleTimeString()}</td></tr>
        {/each}
      </tbody>
    </table>
  </div>
  <div class="mt-6">
    <h3 class="font-semibold">Positions & P/L</h3>
    <ul class="list-disc pl-5">
      {#each $positions as p}
        <li>{p.symbol}: {p.quantity} @ {p.avgPrice} — P/L: {p.unrealizedPnL}</li>
      {/each}
    </ul>
  </div>
</div>
```

## 3. UX Considerations

* **Auto-Refresh**: poll every 5 seconds; consider WebSocket for push updates
* **Loading States**: show spinner while data is fetching
* **Error Handling**: display errors if RPC calls fail
* **Chart Integration**: extend with simple line chart of P/L history using a Svelte chart library

## 4. Testing & Validation

* **Unit Tests**: mock `scanSignals`, `getPositions` bindings to return sample data; render component and assert table rows
* **End-to-End**: run full stack locally; verify signals appear and positions update as simulated trades execute

## 5. Cucumber Scenarios

```gherkin
Feature: Monitoring Tab
  Scenario: Display scan signals
    Given scanSignals returns [{symbol:"AAPL", signal:"CALL_DEBIT", timestamp: now}]
    When MonitoringTab mounts
    Then the Signals table shows a row with AAPL and CALL_DEBIT

  Scenario: Pause and resume scanning
    Given scanning is active
    When I click "Pause Scanning"
    Then pauseScanning is invoked
    And button label changes to "Resume Scanning"

  Scenario: Display positions
    Given getPositions returns [{symbol:"MSFT", quantity:2, avgPrice:300, unrealizedPnL:50}]
    When MonitoringTab mounts
    Then the Positions list contains "MSFT: 2 @ 300 — P/L: 50"
```

## 6. Pseudocode Outline

```text
onMount:
  fetchData();
  setInterval(fetchData, 5000);

fetchData:
  signals = await scanSignals();
  signalsStore.set(signals);
  positions = await getPositions();
  positionsStore.set(positions);

handlePause:
  pauseScanning(); paused=true;
handleResume:
  resumeScanning(); paused=false;
```
