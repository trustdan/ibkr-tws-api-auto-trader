#!/bin/bash
# Script to deploy all Kubernetes resources

set -e

# Apply namespace first
kubectl apply -f namespace.yaml

# Set the namespace for subsequent commands
NAMESPACE="ibkr-trader"

# Apply ConfigMap
kubectl apply -f configmap.yaml -n $NAMESPACE

# Apply Redis resources
kubectl apply -f redis-pvc.yaml -n $NAMESPACE
kubectl apply -f redis-deployment.yaml -n $NAMESPACE
kubectl apply -f redis-service.yaml -n $NAMESPACE

# Apply Python Orchestrator resources
kubectl apply -f python-orch-deployment.yaml -n $NAMESPACE
kubectl apply -f python-orch-service.yaml -n $NAMESPACE

# Apply Go Scanner resources
kubectl apply -f go-scanner-deployment.yaml -n $NAMESPACE
kubectl apply -f go-scanner-service.yaml -n $NAMESPACE

# Wait for deployments to become ready
echo "Waiting for deployments to become ready..."
kubectl rollout status deployment/redis -n $NAMESPACE
kubectl rollout status deployment/python-orch -n $NAMESPACE
kubectl rollout status deployment/go-scanner -n $NAMESPACE

echo "Deployment complete! Resources are available in the '$NAMESPACE' namespace."
echo ""
echo "To port-forward the Python Orchestrator service:"
echo "kubectl port-forward -n $NAMESPACE svc/python-orch 8000:8000"
echo ""
echo "To port-forward the Go Scanner metrics:"
echo "kubectl port-forward -n $NAMESPACE svc/go-scanner 2112:2112" 