# 01-wails-scaffold.md

## 1. Overview

This document details how to initialize the Wails-based GUI for TraderAdmin.  We’ll scaffold a new Wails project using Svelte and TypeScript, configure the project structure, and verify the initial “Hello World” build.  This sets up the foundation for integrating our Go backend and Python orchestrator.

Key tasks:

* Install Wails CLI and prerequisites
* Initialize a Wails project named `TraderAdmin`
* Configure Svelte/TypeScript template
* Verify GUI renders and communicates with a dummy Go backend

## 2. Prerequisites

* Node.js (v16+)
* Go (v1.18+)
* Wails CLI (`go install github.com/wailsapp/wails/v2/cmd/wails@latest`)

## 3. Scaffold Project

```bash
# Create a new directory
mkdir trader-admin-gui && cd trader-admin-gui

# Initialize Wails project with Svelte/TS
wails init -n TraderAdmin -t svelte
```

This generates:

```
TraderAdmin/
├── frontend/    # Svelte TypeScript code
│   ├── src/
│   └── app.html
├── backend/     # Go code for Wails
│   └── main.go
├── wails.json   # Wails config
└── go.mod
```

## 4. Verify Build

```bash
# In project root
wails dev
```

* Opens a local server (typically `http://localhost:34115`) with a Svelte welcome page.
* Confirm that changes to `frontend/src/App.svelte` hot-reload in the browser.

## 5. Dummy Go Backend Endpoint

Modify `backend/main.go`:

```go
package main

import (
	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/runtime"
)

func basicEndpoint() string {
	return "Hello from Go backend"
}

func main() {
	app := wails.CreateApp(&wails.AppConfig{
		Width:  800,
		Height: 600,
		Title:  "TraderAdmin",
		JS:     js,
		CSS:    css,
		Colour: "#131313",
		Bindings: []interface{}{basicEndpoint},
	})
	app.Run()
}
```

In `frontend/src/App.svelte`, call:

```js
import { basicEndpoint } from '../../wailsjs/go/main/App';

let msg = '';
onMount(async () => {
  msg = await basicEndpoint();
});
```

Verify the message displays in the GUI.

## 6. Cucumber Scenarios

```gherkin
Feature: Wails GUI Initialization
  Scenario: Scaffold Wails project
    Given Wails CLI installed
    When I run "wails init -n TraderAdmin -t svelte"
    Then a TraderAdmin directory with frontend and backend folders is created

  Scenario: Basic Go-Svelte integration
    Given the Wails dev server is running
    When I modify App.svelte to call basicEndpoint()
    Then the GUI displays "Hello from Go backend"
```

## 7. Pseudocode Outline

```shell
# Install Wails CLI
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Scaffold project
wails init -n TraderAdmin -t svelte

# Run development server
wails dev
```
