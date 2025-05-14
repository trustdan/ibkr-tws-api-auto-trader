<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  
  export let type: 'success' | 'error' | 'info' = 'info';
  export let message: string;
  export let duration = 3000;
  export let showClose = true;
  
  const dispatch = createEventDispatcher();
  let visible = true;
  let timeout: number;
  
  onMount(() => {
    if (duration > 0) {
      timeout = window.setTimeout(() => {
        close();
      }, duration);
    }
    
    return () => {
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  });
  
  function close() {
    visible = false;
    dispatch('close');
  }
  
  let bgColor = '';
  let textColor = '';
  let borderColor = '';
  
  switch (type) {
    case 'success':
      bgColor = 'bg-green-100';
      textColor = 'text-green-700';
      borderColor = 'border-green-200';
      break;
    case 'error':
      bgColor = 'bg-red-100';
      textColor = 'text-red-700';
      borderColor = 'border-red-200';
      break;
    case 'info':
    default:
      bgColor = 'bg-blue-100';
      textColor = 'text-blue-700';
      borderColor = 'border-blue-200';
      break;
  }
</script>

{#if visible}
  <div 
    class={`flex items-center justify-between p-3 mb-4 rounded border ${bgColor} ${textColor} ${borderColor}`}
    role="alert"
  >
    <span>{message}</span>
    {#if showClose}
      <button 
        on:click={close}
        class="ml-4 text-gray-500 hover:text-gray-700"
        aria-label="Close"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          class="h-4 w-4" 
          viewBox="0 0 20 20" 
          fill="currentColor"
        >
          <path 
            fill-rule="evenodd" 
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
            clip-rule="evenodd" 
          />
        </svg>
      </button>
    {/if}
  </div>
{/if} 