# 02-k8s-manifests.md

## 1. Overview

This document provides Kubernetes manifests to deploy the Python Orchestrator, Go Scanner service, and Redis (optional) in a development or production cluster.  We define:

* **ConfigMap** for centralized configuration
* **Deployments** with resource requests, limits, liveness/readiness probes
* **Services** for internal and external access (ClusterIP, NodePort)

All manifests live in `deploy/k8s/`.

## 2. ConfigMap

`deploy/k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trader-config
data:
  config.yaml: |
    ibkr:
      host: "python-orch"
      port: 8000
      client_id: 1
    strategy:
      sma_period: 50
      candle_count: 2
      otm_offset: 1
      iv_threshold: 0.8
      min_reward_risk: 1.0
  config.json: |
    {
      "sma50_period":50,
      "candle_count":2,
      "iv_threshold":0.8,
      "min_reward_risk":1.0,
      "universe":["AAPL","MSFT","SPY"]
    }
```

## 3. Python Orchestrator Deployment & Service

`deploy/k8s/python-orch-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-orch
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-orch
  template:
    metadata:
      labels:
        app: python-orch
    spec:
      containers:
      - name: python-orch
        image: your-registry/python-orch:latest
        args: ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.yaml
          subPath: config.yaml
      volumes:
      - name: config-volume
        configMap:
          name: trader-config
          items:
          - key: config.yaml
            path: config.yaml
```

`deploy/k8s/python-orch-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: python-orch
spec:
  type: ClusterIP
  selector:
    app: python-orch
  ports:
  - name: http
    port: 8000
    targetPort: 8000
```

## 4. Go Scanner Deployment & Service

`deploy/k8s/go-scanner-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-scanner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: go-scanner
  template:
    metadata:
      labels:
        app: go-scanner
    spec:
      containers:
      - name: go-scanner
        image: your-registry/go-scanner:latest
        args: ["--config", "/app/config.json"]
        ports:
        - containerPort: 2112
        readinessProbe:
          httpGet:
            path: /metrics
            port: 2112
          initialDelaySeconds: 5
          periodSeconds: 15
        livenessProbe:
          httpGet:
            path: /metrics
            port: 2112
          initialDelaySeconds: 20
          periodSeconds: 30
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.json
          subPath: config.json
      volumes:
      - name: config-volume
        configMap:
          name: trader-config
          items:
          - key: config.json
            path: config.json
```

`deploy/k8s/go-scanner-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: go-scanner
spec:
  type: ClusterIP
  selector:
    app: go-scanner
  ports:
  - name: metrics
    port: 2112
    targetPort: 2112
```

## 5. Cucumber Scenarios

```gherkin
Feature: Kubernetes Deployments
  Scenario: Apply all manifests
    Given kubectl context is set
    When I run kubectl apply -f deploy/k8s/
    Then all pods for python-orch, go-scanner, and redis are in Ready state

  Scenario: Services are reachable
    Given deployments are ready
    When I port-forward python-orch to localhost:8000
    Then GET /health returns 200
    And port-forward go-scanner to localhost:2112
    Then GET /metrics contains "scan_requests_total"
```

## 6. Pseudocode Outline

```shell
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/python-orch-deployment.yaml
kubectl apply -f deploy/k8s/python-orch-service.yaml
kubectl apply -f deploy/k8s/go-scanner-deployment.yaml
kubectl apply -f deploy/k8s/go-scanner-service.yaml
```
