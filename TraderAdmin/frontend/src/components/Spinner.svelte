<script lang="ts">
  export let size = 'md';
  export let color = 'currentColor';
  
  let sizeClass = '';
  
  switch(size) {
    case 'sm':
      sizeClass = 'h-4 w-4';
      break;
    case 'md':
      sizeClass = 'h-6 w-6';
      break;
    case 'lg':
      sizeClass = 'h-8 w-8';
      break;
    default:
      sizeClass = 'h-6 w-6';
  }
</script>

<svg 
  class={`animate-spin ${sizeClass}`} 
  xmlns="http://www.w3.org/2000/svg" 
  fill="none" 
  viewBox="0 0 24 24"
>
  <circle class="opacity-25" cx="12" cy="12" r="10" stroke={color} stroke-width="4"></circle>
  <path class="opacity-75" fill={color} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg> 