# 03-helm-charts-optional.md

## 1. Overview

This document introduces an optional Helm chart for templating and deploying our TraderAdmin services (Python Orchestrator, Go Scanner, and Redis).  Using Helm simplifies environment-specific overrides (QA, staging, production) and keeps our manifests DRY.

Key objectives:

* Provide a single chart (`charts/traderadmin`) containing all Kubernetes resources as templates
* Define a `values.yaml` with configurable image tags, resource limits, and config parameters
* Enable easy overrides via `--set` or custom `values-*.yaml` files

## 2. Chart Structure

```
charts/traderadmin/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── configmap.yaml
│   ├── python-orch-deployment.yaml
│   ├── python-orch-service.yaml
│   ├── go-scanner-deployment.yaml
│   ├── go-scanner-service.yaml
│   └── _helpers.tpl
```

### 2.1 Chart.yaml

```yaml
apiVersion: v2
name: traderadmin
description: Helm chart for TraderAdmin services
version: 0.1.0
appVersion: "1.0"
```

### 2.2 values.yaml

```yaml
# Default values
image:
  pythonOrch: your-registry/python-orch:latest
  goScanner: your-registry/go-scanner:latest
resources:
  pythonOrch:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  goScanner:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
config:
  python:
    ibkr:
      host: python-orch
      port: 8000
      client_id: 1
    strategy:
      sma_period: 50
      candle_count: 2
      otm_offset: 1
      iv_threshold: 0.8
      min_reward_risk: 1.0
  scanner:
    sma50_period: 50
    candle_count: 2
    iv_threshold: 0.8
    universe: ["AAPL","MSFT","SPY"]
replicaCount:
  pythonOrch: 1
  goScanner: 1
```

## 3. Template Examples

### templates/configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trader-config
data:
  config.yaml: |
{{ toYaml .Values.config.python | indent 4 }}
  config.json: |
{{ toJson .Values.config.scanner | indent 4 }}
```

### templates/python-orch-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-orch
spec:
  replicas: {{ .Values.replicaCount.pythonOrch }}
  template:
    spec:
      containers:
      - name: python-orch
        image: {{ .Values.image.pythonOrch }}
        resources:
          {{- toYaml .Values.resources.pythonOrch | indent 10 }}
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.yaml
          subPath: config.yaml
      volumes:
      - name: config-volume
        configMap:
          name: trader-config
```

(Additional templates follow the same pattern for services and Go Scanner deployment.)

## 4. Usage

* **Install chart:**

  ```bash
  helm install traderadmin ./charts/traderadmin \
    --namespace trader --create-namespace
  ```
* **Override values:**

  ```bash
  helm upgrade traderadmin ./charts/traderadmin \
    --set image.pythonOrch=registry/python-orch:v2.0 \
    --set replicaCount.goScanner=2
  ```

## 5. Cucumber Scenarios

```gherkin
Feature: Helm Chart Deployment
  Scenario: Install default chart
    Given a Kubernetes cluster
    When I run helm install traderadmin ./charts/traderadmin
    Then deployment/python-orch and go-scanner appear in namespace "trader"

  Scenario: Override image tags
    When I run helm upgrade with --set image.goScanner=custom:1.2
    Then go-scanner pods use image "custom:1.2"
```

## 6. Pseudocode Outline

```text
# Package chart
tar czf traderadmin-0.1.0.tgz charts/traderadmin

# Install
helm install traderadmin traderadmin-0.1.0.tgz

# Upgrade
helm upgrade traderadmin traderadmin-0.1.0.tgz --set replicaCount.goScanner=3
```
