# 04-dev-cluster-setup.md

## 1. Overview

This document guides setting up a local Kubernetes development cluster using **Kind** or **Minikube**.  A local cluster allows you to validate manifests, test service interactions, and simulate production-like deployments without external infrastructure.

Key tasks:

* Install and configure Kind or Minikube
* Create a cluster named `trader-dev`
* Enable ingress or port-forwarding for service access
* Deploy using `kubectl apply` to test manifests

## 2. Prerequisites

* Docker Engine installed and running
* `kubectl` CLI installed (v1.24+)
* **Kind** (`brew install kind`) or **Minikube** (`brew install minikube`)
* Helm CLI (optional for Helm charts)

## 3. Kind Cluster Setup

### 3.1 Install Kind

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
mv ./kind /usr/local/bin/kind
```

### 3.2 Create Cluster

```bash
kind create cluster --name trader-dev --config <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
      - containerPort: 2112
        hostPort: 2112
EOF
```

* Maps container port 80→host 8080 for ingress; 2112→2112 for metrics.

### 3.3 Verify

```bash
kubectl cluster-info --context kind-trader-dev
kubectl get nodes
```

## 4. Minikube Cluster Setup (Alternative)

```bash
minikube start --profile trader-dev --driver=docker --ports "80:80,2112:2112"
kubectl config use-context trader-dev
```

Enable ingress:

```bash
minikube addons enable ingress
```

## 5. Deploying Services

1. **Apply ConfigMap & Deployments**:

   ```bash
   kubectl apply -f deploy/k8s/configmap.yaml
   kubectl apply -f deploy/k8s/python-orch-deployment.yaml
   kubectl apply -f deploy/k8s/python-orch-service.yaml
   kubectl apply -f deploy/k8s/go-scanner-deployment.yaml
   kubectl apply -f deploy/k8s/go-scanner-service.yaml
   ```
2. **Check Pods & Services**:

   ```bash
   kubectl get pods -n default
   kubectl get svc
   ```

## 6. Accessing Services

* **Python Orchestrator**:

  * Port-forward: `kubectl port-forward svc/python-orch 8000:8000`
  * Visit: `http://localhost:8000/health`

* **Go Scanner Metrics**:

  * Port-forward: `kubectl port-forward svc/go-scanner 2112:2112`
  * Visit: `http://localhost:2112/metrics`

## 7. Cucumber Scenarios

```gherkin
Feature: Local Kubernetes Cluster
  Scenario: Create Kind cluster
    Given Docker is running
    When I run kind create cluster
    Then context "kind-trader-dev" exists

  Scenario: Deploy services
    Given cluster "trader-dev" is up
    When I apply all manifests in deploy/k8s
    Then pods for python-orch and go-scanner are Ready

  Scenario: Access health and metrics
    Given services are deployed
    When I port-forward python-orch to 8000
    Then GET /health returns status ok
    And I port-forward go-scanner to 2112
    Then GET /metrics contains "scan_requests_total"
```

## 8. Pseudocode Outline

```bash
# Kind
kind create cluster --name trader-dev --config kind-config.yaml
kubectl apply -f deploy/k8s/
kubectl port-forward svc/python-orch 8000:8000 &
curl http://localhost:8000/health
kubectl port-forward svc/go-scanner 2112:2112 &
curl http://localhost:2112/metrics
```
