<script lang="ts">
  import { onMount } from 'svelte';
  import { writable, type Writable } from 'svelte/store';
  import type { Signal, Position } from '../stores';
  import { fetchSignals, fetchPositions, pauseScanner, resumeScanner } from '../services/api';

  const signals: Writable<Signal[]> = writable([]);
  const positions: Writable<Position[]> = writable([]);
  let paused = false;
  let loading = true;
  let error: string | null = null;

  async function fetchData() {
    try {
      loading = true;
      error = null;
      
      const sigs = await fetchSignals();
      signals.set(sigs);
      
      const pos = await fetchPositions();
      positions.set(pos);
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Failed to fetch data';
      console.error('Error fetching monitoring data:', err);
    } finally {
      loading = false;
    }
  }

  function handlePause() {
    try {
      pauseScanner();
      paused = true;
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Failed to pause scanning';
      console.error('Error pausing scan:', err);
    }
  }
  
  function handleResume() {
    try {
      resumeScanner();
      paused = false;
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Failed to resume scanning';
      console.error('Error resuming scan:', err);
    }
  }

  onMount(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  });
</script>

<div class="p-4">
  <h2 class="text-xl font-bold">Monitoring Dashboard</h2>
  
  {#if error}
    <div class="p-3 my-3 bg-red-100 text-red-700 border border-red-200 rounded">
      {error}
    </div>
  {/if}
  
  <div class="mt-4">
    <button 
      on:click={paused ? handleResume : handlePause}
      class="p-2 rounded text-white"
      class:bg-green-500={!paused}
      class:bg-red-500={paused}
      disabled={loading}
    >
      {paused ? 'Resume' : 'Pause'} Scanning
    </button>
  </div>
  
  <div class="mt-6">
    <h3 class="font-semibold">Signals</h3>
    {#if loading && $signals.length === 0}
      <div class="py-4 text-gray-500">Loading signals...</div>
    {:else}
      <table class="w-full mt-2 border-collapse border border-gray-300">
        <thead class="bg-gray-100">
          <tr>
            <th class="border border-gray-300 p-2 text-left">Symbol</th>
            <th class="border border-gray-300 p-2 text-left">Signal</th>
            <th class="border border-gray-300 p-2 text-left">Time</th>
          </tr>
        </thead>
        <tbody>
          {#if $signals.length === 0}
            <tr>
              <td colspan="3" class="border border-gray-300 p-2 text-center">No signals found</td>
            </tr>
          {:else}
            {#each $signals as s}
              <tr class="hover:bg-gray-50">
                <td class="border border-gray-300 p-2">{s.symbol}</td>
                <td class="border border-gray-300 p-2">{s.signal}</td>
                <td class="border border-gray-300 p-2">{new Date(s.timestamp).toLocaleTimeString()}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    {/if}
  </div>
  
  <div class="mt-6">
    <h3 class="font-semibold">Positions & P/L</h3>
    {#if loading && $positions.length === 0}
      <div class="py-4 text-gray-500">Loading positions...</div>
    {:else if $positions.length === 0}
      <div class="py-4 text-gray-500">No active positions</div>
    {:else}
      <div class="mt-2 border rounded border-gray-300">
        {#each $positions as p}
          <div class="p-3 border-b border-gray-300 flex items-center justify-between">
            <div>
              <span class="font-medium">{p.symbol}</span>: {p.quantity} @ {p.avgPrice}
            </div>
            <div class="ml-4" class:text-green-600={p.unrealizedPnL > 0} class:text-red-600={p.unrealizedPnL < 0}>
              P/L: ${p.unrealizedPnL.toFixed(2)}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div> 