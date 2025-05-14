import { notifications } from '../stores/notification';

/**
 * Formats an error into a user-friendly message
 * @param error The error to format
 * @returns A formatted error message string
 */
export function formatError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  } else if (typeof error === 'string') {
    return error;
  } else {
    return 'An unknown error occurred';
  }
}

/**
 * Standard error handler for API calls
 * @param error The error to handle
 * @param prefix An optional prefix for the error message
 */
export function handleApiError(error: unknown, prefix: string = 'API Error'): string {
  const errorMessage = formatError(error);
  const fullMessage = `${prefix}: ${errorMessage}`;
  
  // Log to console
  console.error(fullMessage, error);
  
  // Show notification
  notifications.add(fullMessage, 'error');
  
  return fullMessage;
} 