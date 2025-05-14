import { writable } from 'svelte/store';

export type NotificationType = 'success' | 'error' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number;
}

function createNotificationStore() {
  const { subscribe, update } = writable<Notification[]>([]);
  
  return {
    subscribe,
    add: (message: string, type: NotificationType = 'info', duration: number = 3000) => {
      const id = Math.random().toString(36).substring(2, 9);
      update((notifications: Notification[]) => [
        ...notifications,
        { id, type, message, duration }
      ]);
      
      if (duration > 0) {
        setTimeout(() => {
          update((notifications: Notification[]) => notifications.filter((n: Notification) => n.id !== id));
        }, duration);
      }
      
      return id;
    },
    remove: (id: string) => {
      update((notifications: Notification[]) => notifications.filter((n: Notification) => n.id !== id));
    },
    clear: () => {
      update(() => []);
    }
  };
}

export const notifications = createNotificationStore(); 