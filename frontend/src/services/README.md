# Frontend API Service Layer

This directory contains service abstraction layers that handle communication between the Svelte frontend and the Go backend via Wails bindings.

## Purpose

The service layer provides several benefits:
- **Abstraction**: Components don't need to know the details of how backend calls work
- **Centralized error handling**: Common error patterns can be handled in one place
- **Testability**: Services can be easily mocked for component tests
- **Type safety**: Provides TypeScript interfaces for all API calls

## Usage

Import specific functions from the API service in your components:

```ts
import { fetchSignals, pauseScanner } from '../services/api';

// Then use in your component
const signals = await fetchSignals();
```

## Service Categories

The API service is organized into functional categories:

1. **Signal APIs**
   - `fetchSignals()` - Get current trading signals

2. **Position APIs**
   - `fetchPositions()` - Get current trading positions

3. **Scanner Control APIs**
   - `pauseScanner()` - Pause the scanner service
   - `resumeScanner()` - Resume the scanner service

4. **Configuration APIs**
   - `persistConfig()` - Save configuration to backend
   - `fetchConfigSchema()` - Get configuration schema

5. **Connection APIs**
   - `connectToIBKR()` - Connect to IBKR TWS
   - `disconnectFromIBKR()` - Disconnect from IBKR TWS
   - `checkConnectionStatus()` - Check current connection status

## Error Handling

All API functions include standardized error handling:
- Errors are logged to console
- Most errors are re-thrown to allow components to handle them
- Some non-critical functions (like status checks) return safe defaults on error

## Testing

The services are unit tested in `api.test.ts` with mocked Wails bindings. 