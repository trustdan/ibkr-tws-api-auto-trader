Below is a high-level **pre-plan** outlining each of the \~24 markdown docs you’ll create, grouped by area and ordered for maximum build flow. Each entry has:

* **2–3 paragraphs** describing scope, key details (with your ATM/OTM vertical-spread rules baked in),
* A **Cucumber/Gherkin** snippet to define acceptance,
* A touch of **pseudocode** to illustrate the core logic.

---

## 🐍 1. Python Orchestrator & ib-insync (6 docs)

#### 01-python-setup.md

First, we’ll scaffold the Python orchestrator repository: virtual environment, dependency management (`poetry` or `pipenv`), and initial project layout (`src/`, `tests/`, `config/`).  Include your **core strategy parameters** in a `config.yaml` (SMA period = 50, candle count = 2, vol thresholds, reward-risk ≥1:1, OTM/ATM deltas).  Document installation of `ib-insync`, `pandas`, `PyYAML`, and testing libs (`pytest`, `pytest-bdd`).

Second, define environment variables for IB host/port/clientID and fallback defaults.  Sketch out the config schema so subsequent docs reference a canonical source of truth.

```gherkin
Feature: Python Project Initialization
  Scenario: Install dependencies
    Given a fresh Python environment
    When I install project dependencies
    Then `ib_insync`, `pandas`, and test frameworks are available
```

```pseudocode
# load configuration
config = load_yaml("config.yaml")
assert config.sma_period == 50
```

---

#### 02-ibkr-connection.md

Outline the `IBConnector` class that wraps `ib_insync.IB()` connect/disconnect logic, with retries and timeout.  Document subscribing to `connectedEvent`, `disconnectedEvent`, and `errorEvent` to maintain a `connected` flag.  Emphasize non-blocking usage (`ib.sleep(0)`) to let the event loop run.

Include instructions for mocking a TWS instance for local dev.  Show how to surface connection status to logs or upstream gRPC calls.

```gherkin
Feature: IBKR Connection Management
  Scenario: Successful connection
    Given TWS is up on localhost:7497
    When the orchestrator calls connect()
    Then is_connected() returns true
```

```pseudocode
if not ib.isConnected():
    ib.connect(host, port, client_id)
```

---

#### 03-market-data-and-chains.md

Detail fetching historical bars for technical analysis (50 days + 2 candles).  Show how to call `reqHistoricalData` for 1d bars, convert to DataFrame, compute SMA50, and pull greeks/implied volatility via `reqSecDefOptParams`.  Describe error handling for symbols with no chain.

Include examples for ATM vs 1-strike OTM resolution.

```gherkin
Feature: Market Data Retrieval
  Scenario: Fetch 1d bars and compute SMA
    Given symbol "AAPL"
    When I request past 52 daily bars
    Then a DataFrame with columns [open, high, low, close, sma50] is returned
```

```pseudocode
bars = ib.reqHistoricalData(stock, duration="52 D", barSize="1 day")
df = to_dataframe(bars)
df["sma50"] = df.close.rolling(50).mean()
```

---

#### 04-strategy-engine.md

Implement your **pattern-detection** rules:

* **Bullish**: last 2 bars green (close>open), close\[−2,−1] both above rising SMA50
* **Bearish**: last 2 bars red, both below SMA50
* **Volatility-trigger**: IV percentile > threshold → switch to credit spreads

Discuss how to encapsulate these in a `StrategyEngine` class, how signals flow downstream, and how to unit-test via Gherkin scenarios.

```gherkin
Feature: Pattern Detection
  Scenario: Bullish call debit signal
    Given AAPL bars with two green closes above rising SMA50
    When strategy.evaluate("AAPL")
    Then signal.type == "CALL_DEBIT"
```

```pseudocode
if last2_green and close[-1] > sma50[-1] and sma50[-1] > sma50[-2]:
    emit_signal("CALL_DEBIT", symbol)
```

---

#### 05-order-execution.md

Guide the construction of vertical spreads via `ib.placeOrder`:

* **Debit**: buy ATM/OTM call or put spread when pattern triggers
* **Credit**: sell vertical when IV high
* Always enforce R\:R ≥ 1:1 by checking `maxProfit/maxLoss`.

Show how to build two `Option` contracts (long/short legs), wrap in `ComboLeg`, place as a single `OrderCombo`.  Include trade-tracking and fill events.

```gherkin
Feature: Vertical Spread Placement
  Scenario: Place a call debit spread
    Given a CALL_DEBIT signal for MSFT
    When order.execute(signal)
    Then two legs (BUY call, SELL call+1) are submitted
```

```pseudocode
long = Option(sym, expiry, atm_strike, "C")
short = Option(sym, expiry, atm_strike+strike_step, "C")
order = ComboOrder("BUY", legs=[long, short])
ib.placeOrder(combo_contract, order)
```

---

#### 06-python-ci-cd.md

Describe your **GitHub Actions** workflow:

* **On push** → lint (`flake8`), format check, unit/BDD tests
* **On tag** → build Docker image (`python:3.10`), push to registry

Include sample `Dockerfile` with multi-stage build, health-check endpoint, and how to expose a `/health` route.

```gherkin
Feature: CI Pipeline
  Scenario: On push to main
    When Actions run
    Then code is linted and tests pass
```

```pseudocode
# .github/workflows/ci.yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest --bdd
  build:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t org/python-orch:latest .
      - run: docker push org/python-orch:latest
```

---

## 🏃 2. Go Scanner Service (6 docs)

#### 01-go-scanner-setup.md

Initialize `go mod`, set up directories (`cmd/scanner`, `pkg/scan`, `pkg/models`).  Document dependencies (e.g. `grpc`, `prometheus/client_golang`).

Outline reading the same config schema (SMA period, candle rules, IV threshold) via JSON or a shared protobuf.

```gherkin
Feature: Go Scanner Setup
  Scenario: Initialize module
    Given an empty directory
    When I run `go mod init scanner`
    Then `go.sum` and `go.mod` exist
```

```pseudocode
type Config struct {
    SMA50Period int
    CandleCount int
    IVThreshold float64
}
```

---

#### 02-scan-logic.md

Detail the core scanning algorithm in Go: fetch bar data (via Python gRPC or direct REST), compute SMA50, count candles, evaluate IV.  Use worker-pool pattern for symbol universe.

```gherkin
Feature: Scanner Logic
  Scenario: Identify bullish symbols
    Given a universe of symbols
    When scanner.scanAll()
    Then symbols matching two green bars above SMA50 are returned
```

```pseudocode
for symbol in symbols {
    go func(sym) {
        bars := fetchBars(sym, 52)
        if last2Green(bars) && smaRising(bars) {
            results <- sym
        }
    }(symbol)
}
```

---

#### 03-grpc-interface.md

Define protobuf messages for `ScanRequest`, `ScanResponse`.  Show service methods:

```protobuf
rpc ScanUniverse(ScanRequest) returns (ScanResponse);
```

Document generating Go stubs, integrating into the scanner and Python orchestrator clients.

```gherkin
Feature: gRPC Scan API
  Scenario: Request a scan
    Given scanner server running
    When client calls ScanUniverse({})
    Then a list of matching symbols is returned
```

```pseudocode
resp, err := client.ScanUniverse(ctx, &pb.ScanRequest{})
symbols := resp.Matches
```

---

#### 04-mocking-and-tests.md

Show unit tests using `testing` and table-driven patterns.  Mock bar data to assert scanning logic.  Include benchmarks for 1k symbols.

```gherkin
Feature: Scanner Unit Tests
  Scenario Outline: Scan pattern
    Given bars: <bars>
    When evaluatePattern(bars)
    Then result == <expected>
    Examples:
      | bars               | expected |
      | [green,green, ...] | true     |
      | [red,red, ...]     | false    |
```

```pseudocode
func TestLast2Green(t *testing.T) { … }
```

---

#### 05-metrics-and-logging.md

Instrument with Prometheus (`Histogram`, `Counter`) for scan durations and match counts.  Configure structured logs (JSON) with zap or logrus.

```gherkin
Feature: Metrics Exposure
  Scenario: Metrics endpoint
    Given scanner running
    When HTTP GET /metrics
    Then Prometheus metrics are returned
```

```pseudocode
scanDuration := metrics.NewHistogram("scan_duration")  
scanDuration.Observe(elapsed)
```

---

#### 06-go-ci-cd.md

Set up GitHub Actions for Go: `go fmt`, `go vet`, `go test`, docker build of `scanner:latest`.  Push to registry on tag.

```gherkin
Feature: Go CI Pipeline
  Scenario: On push
    When Actions run go tests
    Then all tests pass
```

```pseudocode
jobs:
  build:
    steps:
      - run: go fmt ./...
      - run: go test ./...
      - run: docker build -t org/go-scanner:latest .
```

---

## 📦 3. Containerization & Local K8s (5 docs)

#### 01-docker-compose.md

Compose the `python-orch`, `go-scanner`, and a local Redis (for caching) services.  Define shared network, volumes, environment files, and health checks.

```gherkin
Feature: Docker Compose Setup
  Scenario: Bring up services
    When I run `docker-compose up -d`
    Then python-orch and go-scanner are healthy
```

```pseudocode
services:
  python-orch:
    image: org/python-orch:latest
    ...
  go-scanner:
    image: org/go-scanner:latest
```

---

#### 02-k8s-manifests.md

Write Kubernetes `Deployment`, `Service`, and `ConfigMap` YAML for each component.  Include readiness/liveness probes and resource requests/limits.

```gherkin
Feature: K8s Deployment
  Scenario: Deploy orchestrator
    Given KUBECONFIG set
    When `kubectl apply -f orchestrator-deployment.yaml`
    Then pods become Ready
```

```pseudocode
apiVersion: apps/v1
kind: Deployment
...
```

---

#### 03-helm-charts-optional.md

(Optional) Show how to templatize deployments with Helm: `values.yaml` for images and config overrides.  Chart structure under `charts/traderadmin`.

```gherkin
Feature: Helm Chart
  Scenario: Install chart
    Given a valid values.yaml
    When `helm install traderadmin ./charts/traderadmin`
    Then all pods start with correct images
```

```pseudocode
{{ .Values.python.image }}
```

---

#### 04-dev-cluster-setup.md

Guide on using Kind or Minikube: installing, creating a cluster, enabling ingress, port-forwarding to services.

```gherkin
Feature: Local K8s Cluster
  Scenario: Create Kind cluster
    When `kind create cluster --name traderdev`
    Then a Kubernetes cluster named traderdev exists
```

```pseudocode
kind create cluster --config kind-config.yaml
kubectl apply -f ingress.yaml
```

---

#### 05-k8s-ci-cd.md

Define GitHub Actions to deploy to your dev cluster on `main` (via `kubectl apply` or Helm), and to production via a manual approval step.

```gherkin
Feature: K8s CD Pipeline
  Scenario: On merge to main
    When Actions run
    Then manifests are applied to dev cluster
```

```pseudocode
- run: kubectl apply -f k8s/
  env:
    KUBECONFIG: ${{ secrets.DEV_KUBECONFIG }}
```

---

## 💻 4. Wails GUI (7 docs)

#### 01-wails-scaffold.md

Initialize a Wails project (`wails init`), choose Svelte/TS, and wire up a basic App shell.  Document folder structure (`frontend/`, `backend/`).

```gherkin
Feature: Wails Project Init
  Scenario: Scaffold GUI
    When I run `wails init -n TraderAdmin`
    Then frontend and backend dirs exist
```

```pseudocode
wails init -n TraderAdmin -t svelte
```

---

#### 02-schema-and-stores.md

Show how the Go backend exposes a JSON schema of your Python config (via gRPC or REST), and how Svelte stores (`configStore`, `statusStore`) ingest it.

```gherkin
Feature: Config Schema Loading
  Scenario: Fetch schema
    Given backend running
    When frontend calls getSchema()
    Then configStore.schema is populated
```

```pseudocode
let schema = await backend.getSchema()
configStore.setSchema(schema)
```

---

#### 03-connection-tab.md

Design the Connection tab: form inputs for host/port/clientID, a “Connect” button, and a live status indicator (green/red).  Show how Wails calls Go backend which proxies to Python orchestrator.

```gherkin
Feature: Connection Tab
  Scenario: Connect button
    Given host=localhost, port=7497
    When I click Connect
    Then status turns green
```

```pseudocode
onConnect() {
  backend.connectIbkr(host, port, clientId)
}
```

---

#### 04-trading-config-tab.md

Render dynamic forms for your strategy parameters: SMA period, candle count, IV threshold, reward-risk ratio, strike offset (ATM vs OTM).  Validate inputs client-side.

```gherkin
Feature: Trading Config
  Scenario: Update SMA period
    Given current sma=50
    When user sets sma=60
    Then configStore.update("smaPeriod", 60)
```

```pseudocode
<input bind:value={config.smaPeriod}/>
```

---

#### 05-monitoring-tab.md

Display real-time scan results, active positions, and P/L charts.  Include Pause/Edit/Unpause controls that call Go backend which orchestrates Python to stop/reload strategies.

```gherkin
Feature: Monitoring Dashboard
  Scenario: Show new signals
    Given scanner running
    When a bullish signal arrives
    Then symbol appears in table
```

```pseudocode
signals.subscribe(list => updateTable(list))
```

---

#### 06-frontend-integration.md

Detail how the Svelte frontend calls Go backend methods (via Wails) which then invoke Python orchestrator gRPC endpoints.  Show error-handling flow to surface issues in the GUI.

```gherkin
Feature: End-to-End Call
  Scenario: Trigger scan from GUI
    When I click "Run Scan"
    Then goScanner.ScanUniverse is called
    And pythonOrch.executeStrategies is invoked
```

```pseudocode
async function runFullScan() {
  const symbols = await go.scanUniverse()
  await python.runStrategies(symbols)
}
```

---

#### 07-gui-ci-cd.md

Set up GitHub Actions to build Wails binaries for Windows, macOS, and Linux on each tag, and upload artifacts.  Include a step to validate that the frontend bundles without errors.

```gherkin
Feature: GUI Build Pipeline
  Scenario: On release tag
    When Actions run
    Then App.dmg, .exe, and Linux binaries are published
```

```pseudocode
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: wails build
      - uses: actions/upload-artifact@v3
        with: {path: build/}
```

---

> **Next steps:**
>
> 1. Duplicate each skeleton doc into your `docs/` folder (e.g. `docs/01-python-setup.md`).
> 2. Flesh out sections with code, diagrams, and test cases.
> 3. Iterate as you implement each component—your cucumber specs will drive development.

Add these two as “bookshelf” entries **after** the GUI section (so they become docs 08 and 09 under Wails GUI), or if you prefer lumping them into a new “Packaging & Docs” section after GUI:

---

### 08-gui-nsis-installer.md

**Where:** Immediately after **07-gui-ci-cd.md**
**Scope:**

* Write an NSIS script (`.nsi`) that packages your Wails-built binaries into a single Windows installer (.exe).
* Include custom install paths, Start-menu shortcuts, environment‐variable setting if needed, and an uninstaller section.
* Hook it into your GUI CI workflow so that on a release tag you not only build the `.exe`/`.dmg`/Linux bins but also run `makensis installer.nsi` and upload the resulting `TraderAdmin-Setup.exe`.

**Cucumber Snippet:**

```gherkin
Feature: Windows Installer Packaging
  Scenario: Build Windows installer
    Given Wails GUI artifacts exist
    When CI runs NSIS build script
    Then TraderAdmin-Setup.exe is generated with Start-menu entry
```

**Pseudocode Outline:**

```text
# In .github/workflows/gui-build.yaml
- name: Build NSIS installer
  run: makensis -V2 installer.nsi
- name: Upload installer
  uses: actions/upload-artifact@v3
  with:
    name: TraderAdmin-Setup.exe
    path: build/TraderAdmin-Setup.exe
```

---

### 09-documentation-guidelines.md

**Where:** Right after the NSIS module (or as its own top-level doc)
**Scope:**

* Establish docs conventions: Use Markdown in `/docs`, update READMEs in each service’s root.
* Define a template for each new `.md` plan file (overview, Gherkin, pseudocode, code snippets).
* Set up a Sphinx or MkDocs site (optional) to generate navigable HTML for your architecture.
* Include CI job to lint markdown (`markdownlint`) and to build the docs site.

**Cucumber Snippet:**

```gherkin
Feature: Project Documentation
  Scenario: Validate docs on pull request
    Given new .md files added
    When CI runs markdownlint
    Then no lint errors are reported
```

**Pseudocode Outline:**

```text
# .github/workflows/docs.yml
- run: markdownlint "docs/**/*.md"
- run: mkdocs build --strict
- run: actions/upload-artifact@v3 path=site/
```

---

Embed those two into your `docs/` index, and you’ll have both a polished Windows installer and a living, validated documentation site.


With this **24-leg outline**, you’ve got a clear roadmap to build, test, containerize, and deliver a full-stack, ib-insync-powered vertical-spread trading dashboard. 🚀
