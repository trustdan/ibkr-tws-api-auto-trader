# 01-wails-scaffold.md

## 1. Overview

This document details how to initialize the Wails-based GUI for TraderAdmin. We'll scaffold a new Wails project using Svelte and TypeScript, configure the project structure, and verify the initial application build. This GUI will serve as the frontend for our trading system, providing interfaces for:

* Configuring and connecting to IBKR TWS
* Managing trading strategies and parameters
* Monitoring active trades and scan results
* Visualizing performance metrics

## 2. Prerequisites for Windows

### 2.1 Install Go

1. Download Go installer from [golang.org](https://golang.org/dl/)
2. Run the installer and follow the prompts
3. Verify installation:
   ```powershell
   go version
   ```

### 2.2 Install Node.js and npm

1. Download Node.js LTS installer from [nodejs.org](https://nodejs.org/)
2. Run the installer with default options
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

### 2.3 Install WebView2

1. Wails requires Microsoft WebView2:
   ```powershell
   # Using Chocolatey (if installed)
   choco install microsoft-edge-webview2-runtime

   # Or download manually from:
   # https://developer.microsoft.com/en-us/microsoft-edge/webview2/
   ```

### 2.4 Install Wails CLI

```powershell
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

## 3. Project Structure

The Wails project will be organized as follows:

```
TraderAdmin/
├── frontend/          # Svelte TypeScript frontend
│   ├── src/
│   │   ├── App.svelte           # Main application component
│   │   ├── components/          # Reusable UI components
│   │   │   ├── Connection/      # IBKR connection components
│   │   │   ├── Config/          # Strategy configuration components
│   │   │   ├── Monitoring/      # Trade monitoring components
│   │   │   └── common/          # Shared components
│   │   ├── lib/                 # Frontend utilities
│   │   └── stores/              # Svelte stores for state management
│   ├── wailsjs/                 # Auto-generated Go bindings
│   └── index.html               # Main HTML template
├── backend/           # Go backend code
│   ├── main.go                  # Application entry point
│   ├── app.go                   # Main application struct
│   ├── ibkr/                    # IBKR connection handling
│   ├── config/                  # Config management
│   ├── scanner/                 # Scanner client
│   └── orchestrator/            # Orchestrator client
├── build/             # Compiled binaries
├── wails.json         # Wails configuration
└── go.mod             # Go module definition
```

## 4. Scaffolding the Project

### 4.1 Initialize the Project

```powershell
# Create a new directory
mkdir TraderAdmin
cd TraderAdmin

# Initialize Wails project with Svelte/TS template
wails init -n TraderAdmin -t svelte-ts
```

### 4.2 Examine Generated Files

Take a moment to examine the generated files:

* `wails.json`: Contains project configuration
* `frontend/`: Contains the Svelte frontend code
* `backend/`: Contains the Go backend code
* `go.mod`: Go module definition
* `main.go`: Main application entry point

## 5. Customizing the Generated Code

### 5.1 Update App Metadata

Edit `wails.json`:

```json
{
  "name": "TraderAdmin",
  "outputfilename": "TraderAdmin",
  "frontend:install": "npm install",
  "frontend:build": "npm run build",
  "frontend:dev:watcher": "npm run dev",
  "frontend:dev:serverUrl": "auto",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  }
}
```

### 5.2 Update App Structure

Modify `backend/main.go`:

```go
package main

import (
	"embed"
	"log"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	// Create an instance of the app structure
	app := NewApp()

	// Create application with options
	err := wails.Run(&options.App{
		Title:  "TraderAdmin",
		Width:  1024,
		Height: 768,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 27, G: 38, B: 54, A: 1},
		OnStartup:        app.startup,
		Bind: []interface{}{
			app,
		},
	})

	if err != nil {
		log.Fatal("Error starting application:", err)
	}
}
```

### 5.3 Create the App Structure

Create `backend/app.go`:

```go
package main

import (
	"context"
	"fmt"
)

// App struct represents the main application state and methods
type App struct {
	ctx context.Context
}

// NewApp creates a new App instance
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

// Status returns the connection status
func (a *App) Status() string {
	return "TraderAdmin is running"
}

// GetVersion returns the application version
func (a *App) GetVersion() string {
	return "v0.1.0"
}

// ConnectIBKR simulates connecting to IBKR TWS
func (a *App) ConnectIBKR(host string, port int, clientID int) string {
	connectionString := fmt.Sprintf("Connected to IBKR at %s:%d with client ID %d", host, port, clientID)
	return connectionString
}
```

### 5.4 Update Frontend

Edit `frontend/src/App.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { GetVersion, Status, ConnectIBKR } from '../wailsjs/go/main/App';

  let statusMessage = 'Initializing...';
  let version = '';
  let connectionStatus = '';
  
  // Form inputs
  let host = 'localhost';
  let port = 7497;
  let clientID = 1;

  onMount(async () => {
    try {
      statusMessage = await Status();
      version = await GetVersion();
    } catch (error) {
      console.error(error);
      statusMessage = 'Error initializing application';
    }
  });

  async function handleConnect() {
    try {
      connectionStatus = await ConnectIBKR(host, port, clientID);
    } catch (error) {
      console.error(error);
      connectionStatus = 'Error connecting to IBKR';
    }
  }
</script>

<main>
  <div class="app">
    <h1>TraderAdmin</h1>
    <div class="status">{statusMessage}</div>
    <div class="version">Version: {version}</div>

    <div class="connection-panel">
      <h2>IBKR Connection</h2>
      <div class="form-group">
        <label for="host">Host:</label>
        <input id="host" type="text" bind:value={host} />
      </div>
      <div class="form-group">
        <label for="port">Port:</label>
        <input id="port" type="number" bind:value={port} />
      </div>
      <div class="form-group">
        <label for="clientID">Client ID:</label>
        <input id="clientID" type="number" bind:value={clientID} />
      </div>
      <button on:click={handleConnect}>Connect</button>
      
      {#if connectionStatus}
        <div class="connection-status">{connectionStatus}</div>
      {/if}
    </div>
  </div>
</main>

<style>
  main {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    padding: 1em;
    max-width: 800px;
    margin: 0 auto;
  }
  .app {
    text-align: center;
  }
  h1 {
    color: #0366d6;
  }
  .status, .version {
    margin: 1em 0;
  }
  .connection-panel {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 1.5em;
    margin-top: 2em;
    text-align: left;
  }
  .form-group {
    margin-bottom: 1em;
  }
  label {
    display: block;
    margin-bottom: 0.5em;
    font-weight: bold;
  }
  input {
    width: 100%;
    padding: 0.5em;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  button {
    background-color: #0366d6;
    color: white;
    border: none;
    padding: 0.75em 1.5em;
    font-size: 1em;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 1em;
  }
  button:hover {
    background-color: #0256b9;
  }
  .connection-status {
    margin-top: 1em;
    padding: 0.75em;
    background-color: #e6f7ff;
    border: 1px solid #91d5ff;
    border-radius: 4px;
  }
</style>
```

## 6. Building and Running

### 6.1 Development Mode

```powershell
# In project root
wails dev
```

This will:
- Build the Go code
- Start the frontend dev server
- Open a window with your application
- Enable hot-reloading for frontend changes

### 6.2 Production Build

```powershell
# Build for Windows
wails build

# The binary will be in the build/bin directory
.\build\bin\TraderAdmin.exe
```

## 7. Adding Project Dependencies

### 7.1 Go Dependencies

```powershell
# Add Go dependencies
go get github.com/sirupsen/logrus
go get github.com/spf13/viper
go get google.golang.org/grpc
```

### 7.2 Frontend Dependencies

```powershell
# Navigate to frontend directory
cd frontend

# Add Svelte dependencies
npm install svelte-spa-router
npm install chart.js
npm install svelte-forms-lib
```

## 8. Testing the Application

### 8.1 Verify Go-JavaScript Communication

1. Make sure you can call Go functions from your Svelte code
2. Verify that the UI updates when Go functions return data
3. Test form submission and parameter passing

### 8.2 Basic Functionality Test

1. Run the application
2. Fill in the connection form
3. Click "Connect"
4. Verify the connection message appears

## 9. Cucumber Scenarios

```gherkin
Feature: Wails GUI Initialization
  Scenario: Scaffold Wails project
    Given Wails CLI installed
    When I run "wails init -n TraderAdmin -t svelte-ts"
    Then a TraderAdmin directory with frontend and backend folders is created
    And wails.json contains correct project metadata

  Scenario: Development server
    Given TraderAdmin project is created
    When I run "wails dev" in the project directory
    Then a window opens with the TraderAdmin application
    And the status message shows "TraderAdmin is running"

  Scenario: Basic Go-Svelte communication
    Given the TraderAdmin application is running
    When I enter host="localhost", port=7497, clientID=1
    And I click "Connect"
    Then the connection status shows "Connected to IBKR at localhost:7497 with client ID 1"
```

## 10. Next Steps

After successfully scaffolding the project:

1. Implement the connection tab with real IBKR connectivity
2. Set up the configuration management system
3. Create components for trading strategy configuration
4. Implement monitoring and visualization features

These topics will be covered in subsequent documents in this series.
