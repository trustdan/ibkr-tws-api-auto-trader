<script lang="ts">
  import { onMount } from 'svelte';
  import { writable, type Writable } from 'svelte/store';
  import { GetPositions, ScanSignals, PauseScanning, ResumeScanning } from '../../wailsjs/go/main/App';
  import Spinner from '../components/Spinner.svelte';

  interface Signal {
    symbol: string;
    signal: number;
    timestamp: number;
  }

  interface Position {
    symbol: string;
    quantity: number;
    avgPrice: number;
    unrealizedPnL: number;
  }

  interface PLDataPoint {
    timestamp: number;
    value: number;
  }

  const signals: Writable<Signal[]> = writable([]);
  const positions: Writable<Position[]> = writable([]);
  const plHistory: Writable<PLDataPoint[]> = writable([]);
  let paused = false;
  let loading = true;
  let error: string | null = null;

  // Function to fetch data from backend
  async function fetchData() {
    try {
      loading = true;
      error = null;
      
      // Fetch signals
      const sigs = await ScanSignals();
      signals.set(sigs);
      
      // Fetch positions
      const pos = await GetPositions();
      positions.set(pos);
      
      // Update P/L history with new data point
      const totalPL = pos.reduce((sum: number, p: Position) => sum + p.unrealizedPnL, 0);
      plHistory.update((history: PLDataPoint[]) => {
        // Keep only last 20 data points for the chart
        const newHistory = [...history, {timestamp: Date.now(), value: totalPL}];
        return newHistory.slice(-20);
      });
      
      // Update chart display
      updateChartPoints();
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Failed to fetch data';
      console.error('Error fetching monitoring data:', err);
    } finally {
      loading = false;
    }
  }

  // Handle pausing scanner
  function handlePause() {
    try {
      PauseScanning();
      paused = true;
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Failed to pause scanning';
      console.error('Error pausing scan:', err);
    }
  }
  
  // Handle resuming scanner
  function handleResume() {
    try {
      ResumeScanning();
      paused = false;
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Failed to resume scanning';
      console.error('Error resuming scan:', err);
    }
  }

  // SVG chart helpers
  let chartPoints = '';
  let chartColor = '#4ade80';
  
  function updateChartPoints() {
    if ($plHistory.length < 2) return;
    
    const maxValue = Math.max(Math.abs(Math.max(...$plHistory.map((p: PLDataPoint) => p.value))), 
                           Math.abs(Math.min(...$plHistory.map((p: PLDataPoint) => p.value))), 10);
    
    chartPoints = $plHistory.map((p: PLDataPoint, i: number) => 
      `${(i / ($plHistory.length - 1)) * 1000},${50 - (p.value / maxValue * 45)}`
    ).join(' ');
    
    chartColor = $plHistory[$plHistory.length - 1].value >= 0 ? "#4ade80" : "#ef4444";
  }

  // Helper function to convert signal numbers to readable names
  function getSignalName(signalType: number): string {
    const signalTypes: Record<number, string> = {
      0: 'NONE',
      1: 'CALL_DEBIT',
      2: 'PUT_DEBIT',
      3: 'CALL_CREDIT',
      4: 'PUT_CREDIT'
    };
    return signalTypes[signalType] || `UNKNOWN (${signalType})`;
  }

  // Set up polling on component mount
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
  
  <!-- P/L Chart -->
  <div class="mt-6">
    <h3 class="font-semibold">P/L Over Time</h3>
    {#if loading && $plHistory.length === 0}
      <div class="py-8 text-center text-gray-500">
        <Spinner size="md" color="#8c8c8c" />
        <p class="mt-2">Loading chart data...</p>
      </div>
    {:else if $plHistory.length === 0}
      <div class="py-4 text-gray-500">No P/L data available yet</div>
    {:else}
      <div class="h-40 mt-2 border border-gray-300 p-2 bg-white relative">
        <!-- Simple SVG-based chart -->
        <svg width="100%" height="100%" viewBox="0 0 1000 100" preserveAspectRatio="none">
          <!-- Zero line -->
          <line x1="0" y1="50" x2="1000" y2="50" stroke="#888" stroke-width="1" />
          
          <!-- P/L line -->
          {#if chartPoints}
            <polyline 
              points={chartPoints} 
              fill="none" 
              stroke={chartColor} 
              stroke-width="2" 
            />
          {/if}
        </svg>
        
        <!-- Current P/L value -->
        {#if $plHistory.length > 0}
          <div class="absolute right-2 top-2 bg-gray-100 p-1 rounded text-sm">
            Current P/L: <span class={$plHistory[$plHistory.length - 1].value >= 0 ? "text-green-600" : "text-red-600"}>
              ${$plHistory[$plHistory.length - 1].value.toFixed(2)}
            </span>
          </div>
        {/if}
      </div>
    {/if}
  </div>
  
  <!-- Signals Table -->
  <div class="mt-6">
    <h3 class="font-semibold">Signals</h3>
    {#if loading && $signals.length === 0}
      <div class="py-8 text-center text-gray-500">
        <Spinner size="md" color="#8c8c8c" />
        <p class="mt-2">Loading signals...</p>
      </div>
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
                <td class="border border-gray-300 p-2">{getSignalName(s.signal)}</td>
                <td class="border border-gray-300 p-2">{new Date(s.timestamp).toLocaleTimeString()}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    {/if}
  </div>
  
  <!-- Positions & P/L -->
  <div class="mt-6">
    <h3 class="font-semibold">Positions & P/L</h3>
    {#if loading && $positions.length === 0}
      <div class="py-8 text-center text-gray-500">
        <Spinner size="md" color="#8c8c8c" />
        <p class="mt-2">Loading positions...</p>
      </div>
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