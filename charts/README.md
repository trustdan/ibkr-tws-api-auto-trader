# Helm Charts for IBKR TWS API Auto Trader

This directory contains Helm charts and helper scripts for deploying the IBKR TWS API Auto Trader system to Kubernetes.

## Directory Structure

- `traderadmin/` - Main Helm chart for deploying the full system
- `helm-deploy.sh` - Bash script for Linux/macOS users
- `helm-deploy.bat` - Batch script for Windows users

## Quick Start

### For Linux/macOS Users

```bash
# Make the script executable
chmod +x helm-deploy.sh

# Install to development environment
./helm-deploy.sh dev install

# Install to production environment
./helm-deploy.sh prod install

# Generate template without installing
./helm-deploy.sh dev template

# Upgrade existing installation
./helm-deploy.sh dev upgrade

# Uninstall
./helm-deploy.sh dev uninstall
```

### For Windows Users

```cmd
# Install to development environment
helm-deploy.bat dev install

# Install to production environment
helm-deploy.bat prod install

# Generate template without installing
helm-deploy.bat dev template

# Upgrade existing installation
helm-deploy.bat dev upgrade

# Uninstall
helm-deploy.bat dev uninstall
```

## Environment-Specific Configuration

The helper scripts automatically create environment-specific values files:

- `values-dev.yaml` - Development environment configuration
- `values-prod.yaml` - Production environment configuration

You can edit these files to customize the deployment for each environment.

## Manual Installation

If you prefer to use Helm directly:

```bash
# Install with custom values
helm install traderadmin ./traderadmin \
  -f custom-values.yaml \
  --namespace ibkr-trader --create-namespace

# Upgrade with new values
helm upgrade traderadmin ./traderadmin \
  -f custom-values.yaml \
  --namespace ibkr-trader
```

## Notes

- The chart uses a dedicated namespace for each environment
- The Redis service uses persistent storage (PVC)
- Both Python Orchestrator and Go Scanner expose metrics for Prometheus 