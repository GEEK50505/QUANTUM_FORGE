import { setupWorker } from 'msw';
import { handlers } from './handlers';

// This configures a Service Worker with the given handlers
export const worker = setupWorker(...handlers);

// Start the mock API
export async function startMockApi() {
  // Enable API mocking in development
  if (process.env.NODE_ENV === 'development') {
    await worker.start({
      onUnhandledRequest: 'bypass', // Don't warn about unhandled requests
    });
    console.log('🔶 Mock API Started');
  }
}