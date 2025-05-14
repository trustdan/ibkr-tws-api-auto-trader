# 04-dev-cluster-setup.md

## 1. Overview

This document guides setting up a local Kubernetes development cluster using **Kind** or **Minikube**. A local cluster allows you to validate manifests, test service interactions, and simulate production-like deployments without external infrastructure.

Key tasks:

* Install and configure Kind or Minikube
* Create a cluster named `trader-dev`
* Enable ingress or port-forwarding for service access
* Deploy our Helm charts for testing
* Set up local development workflows

## 2. Prerequisites

* Docker Desktop installed and running
* `kubectl` CLI installed (v1.24+)
* **Kind** or **Minikube** 
* Helm CLI (v3.8+)

## 3. Installation Instructions (Windows)

### 3.1 Install Chocolatey (if not already installed)

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### 3.2 Install kubectl

```powershell
choco install kubernetes-cli
```

### 3.3 Install Kind

```powershell
choco install kind
```

Or Minikube (alternative):

```powershell
choco install minikube
```

### 3.4 Install Helm

```powershell
choco install kubernetes-helm
```

## 4. Kind Cluster Setup

### 4.1 Create Kind Configuration

Create a file named `kind-config.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
        protocol: TCP
      - containerPort: 443
        hostPort: 8443
        protocol: TCP
      - containerPort: 8000
        hostPort: 8000
        protocol: TCP
      - containerPort: 2112
        hostPort: 2112
        protocol: TCP
```

### 4.2 Create Cluster

```powershell
kind create cluster --name trader-dev --config kind-config.yaml
```

### 4.3 Verify

```powershell
kubectl cluster-info --context kind-trader-dev
kubectl get nodes
```

### 4.4 Install NGINX Ingress Controller

```powershell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s
```

## 5. Minikube Cluster Setup (Alternative)

### 5.1 Start Minikube

```powershell
minikube start --profile trader-dev --driver=docker --ports=8000:8000,2112:2112,8080:80
```

### 5.2 Enable Ingress

```powershell
minikube addons enable ingress --profile trader-dev
```

### 5.3 Set Context

```powershell
kubectl config use-context trader-dev
```

## 6. Deploying Services with Helm

### 6.1 Deploy using Helm

```powershell
# Deploy to development environment
helm install traderadmin ./charts/traderadmin --namespace trader --create-namespace
```

### 6.2 Custom Values for Development

Create a file named `dev-values.yaml`:

```yaml
# Dev-specific overrides
replicaCount:
  pythonOrch: 1
  goScanner: 1

resources:
  pythonOrch:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 300m
      memory: 256Mi

config:
  python:
    ibkr:
      host: "host.docker.internal"  # For connecting to TWS running on host machine
      port: 7497
  scanner:
    universe: ["AAPL", "MSFT", "AMZN", "GOOG", "SPY"]  # Limited universe for development
```

Deploy with development values:

```powershell
helm install traderadmin ./charts/traderadmin -f dev-values.yaml --namespace trader --create-namespace
```

### 6.3 Verify Deployment

```powershell
kubectl get pods -n trader
kubectl get svc -n trader
```

## 7. Accessing Services

### 7.1 Port-Forwarding Method

For Python Orchestrator:

```powershell
kubectl port-forward -n trader svc/traderadmin-python-orch 8000:8000
```

For Go Scanner Metrics:

```powershell
kubectl port-forward -n trader svc/traderadmin-go-scanner 2112:2112
```

### 7.2 Ingress Method

If your Helm chart defines an Ingress resource, you can access services via:

* Python Orchestrator: http://localhost:8080/api/orch
* Go Scanner: http://localhost:8080/api/scanner

### 7.3 Dashboard Script

Create `dashboard.ps1` for easy access to all services:

```powershell
# dashboard.ps1
Write-Host "Starting port-forwarding for all services..."
Start-Process powershell -ArgumentList "kubectl port-forward -n trader svc/traderadmin-python-orch 8000:8000; Read-Host"
Start-Process powershell -ArgumentList "kubectl port-forward -n trader svc/traderadmin-go-scanner 2112:2112; Read-Host"
Write-Host "Services available at:"
Write-Host "- Python Orchestrator: http://localhost:8000"
Write-Host "- Go Scanner Metrics: http://localhost:2112/metrics"
```

## 8. Local Development Workflow

### 8.1 Direct Apply vs Helm

During active development, you can either:

1. Use `kubectl apply` for quick manifest updates:
   ```powershell
   kubectl apply -f k8s/python-orch-deployment.yaml -n trader
   ```

2. Use Helm upgrade with values for consistent deployments:
   ```powershell
   helm upgrade traderadmin ./charts/traderadmin -f dev-values.yaml --namespace trader
   ```

### 8.2 Connecting to Host Services

When running TWS on your local machine, configure your services to use `host.docker.internal` instead of `localhost`:

```yaml
config:
  python:
    ibkr:
      host: "host.docker.internal"
```

## 9. Troubleshooting

### 9.1 Common Issues

1. **Images not pulling**: Ensure images exist locally for Kind or are accessible via registry
   ```powershell
   kind load docker-image your-registry/python-orch:latest --name trader-dev
   ```

2. **Connection refused**: Check if ports are properly mapped and services are running
   ```powershell
   kubectl get endpoints -n trader
   ```

3. **Ingress not working**: Verify ingress controller is running
   ```powershell
   kubectl get pods -n ingress-nginx
   ```

### 9.2 Logs

```powershell
kubectl logs -n trader deploy/traderadmin-python-orch
kubectl logs -n trader deploy/traderadmin-go-scanner
```

### 9.3 Resource Management

```powershell
# Delete resources if needed
helm uninstall traderadmin -n trader

# Delete cluster
kind delete cluster --name trader-dev
```

## 10. Cucumber Scenarios

```gherkin
Feature: Local Kubernetes Cluster
  Scenario: Create Kind cluster
    Given Docker Desktop is running
    When I run "kind create cluster --name trader-dev --config kind-config.yaml"
    Then context "kind-trader-dev" exists in kubectl config
    And the cluster has 1 node

  Scenario: Deploy with Helm
    Given trader-dev cluster is running
    When I run "helm install traderadmin ./charts/traderadmin -f dev-values.yaml --namespace trader --create-namespace"
    Then namespace "trader" contains pods for python-orch and go-scanner
    And all pods reach Ready state within 2 minutes

  Scenario: Access services
    Given traderadmin chart is deployed
    When I port-forward the python-orch service to port 8000
    Then GET http://localhost:8000/health returns status 200
    And when I port-forward the go-scanner service to port 2112
    Then GET http://localhost:2112/metrics contains prometheus metrics
```

## 11. Next Steps

1. Experiment with scaling: `kubectl scale -n trader deployment/traderadmin-python-orch --replicas=2`
2. Set up continuous deployment to your local cluster (see 05-k8s-ci-cd.md)
3. Configure your Wails GUI to connect to local K8s services
