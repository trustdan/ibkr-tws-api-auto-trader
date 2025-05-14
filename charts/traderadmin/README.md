# TraderAdmin Helm Chart

This Helm chart deploys the IBKR TWS API Auto Trader system to a Kubernetes cluster.

## Components

- Python Orchestrator - Manages IBKR connections and order execution
- Go Scanner - Scans for trading opportunities based on technical patterns
- Redis - Shared cache for optimization and rate limiting

## Prerequisites

- Kubernetes 1.16+
- Helm 3+

## Installation

### Quick Start

```bash
# Install the chart with default values
helm install traderadmin ./charts/traderadmin \
  --namespace ibkr-trader --create-namespace
```

### Customizing Values

Create a custom `values.yaml` file and override default values:

```yaml
# custom-values.yaml
replicaCount:
  goScanner: 2  # Run 2 replicas of the Go Scanner

image:
  pythonOrch:
    tag: v1.2.3  # Use a specific version

config:
  python:
    strategy:
      sma_period: 60  # Change SMA period to 60
```

Then install with custom values:

```bash
helm install traderadmin ./charts/traderadmin \
  -f custom-values.yaml \
  --namespace ibkr-trader --create-namespace
```

### Configuration Options

You can override specific values with `--set`:

```bash
helm install traderadmin ./charts/traderadmin \
  --set image.pythonOrch.tag=v1.2.3 \
  --set replicaCount.goScanner=2 \
  --namespace ibkr-trader --create-namespace
```

## Upgrade

```bash
helm upgrade traderadmin ./charts/traderadmin \
  --set image.goScanner.tag=v2.0.0 \
  --namespace ibkr-trader
```

## Uninstall

```bash
helm uninstall traderadmin --namespace ibkr-trader
```

## Configuration Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.pythonOrch.repository` | Python Orchestrator image repository | `localhost:5000/python-orch` |
| `image.pythonOrch.tag` | Python Orchestrator image tag | `latest` |
| `image.goScanner.repository` | Go Scanner image repository | `localhost:5000/go-scanner` |
| `image.goScanner.tag` | Go Scanner image tag | `latest` |
| `replicaCount.pythonOrch` | Number of Python Orchestrator replicas | `1` |
| `replicaCount.goScanner` | Number of Go Scanner replicas | `1` |
| `config.python.strategy.sma_period` | SMA period for strategy | `50` |
| `config.scanner.universe` | List of stock symbols to scan | `["AAPL", "MSFT", "GOOG", ...]` |

## Environment-Specific Deployments

Create environment-specific values files:

### Dev Environment

```bash
helm install traderadmin-dev ./charts/traderadmin \
  -f values-dev.yaml \
  --namespace ibkr-trader-dev --create-namespace
```

### Production Environment

```bash
helm install traderadmin-prod ./charts/traderadmin \
  -f values-prod.yaml \
  --namespace ibkr-trader-prod --create-namespace
```

## Persistence

By default, Redis data is persisted using a PVC. To disable persistence:

```bash
helm install traderadmin ./charts/traderadmin \
  --set persistence.enabled=false \
  --namespace ibkr-trader
```

## Monitoring

The chart includes Prometheus annotations for metrics collection. To disable:

```bash
helm install traderadmin ./charts/traderadmin \
  --set metrics.enabled=false \
  --namespace ibkr-trader
``` 