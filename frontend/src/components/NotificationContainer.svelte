<script lang="ts">
  import { notifications } from '../stores/notification';
  import type { Notification } from '../stores/notification';
  import Toast from './Toast.svelte';
</script>

<div class="fixed top-4 right-4 z-50 w-80">
  {#each $notifications as notification (notification.id)}
    <Toast 
      type={notification.type} 
      message={notification.message}
      duration={notification.duration || 3000}
      on:close={() => notifications.remove(notification.id)}
    />
  {/each}
</div> 