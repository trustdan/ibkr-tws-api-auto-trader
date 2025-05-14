<script lang="ts">
  import pkg from '../../package.json';
  
  // You can expose these as props if needed
  export let showLabel = true;
  export let className = "text-xs text-gray-500";
</script>

<div class={className}>
  {#if showLabel}
    <span>Version: </span>
  {/if}
  <span>{pkg.version}</span>
</div> 