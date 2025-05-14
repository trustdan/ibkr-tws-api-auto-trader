# CI/CD Setup Guide

This guide explains how to set up the CI/CD pipelines for the TraderAdmin application.

## GitHub Actions Workflows

We have implemented four GitHub Actions workflows:

1. **GUI CI/CD** (`.github/workflows/gui-ci-cd.yml`): Builds and packages the Wails desktop application
2. **Python Orchestrator CI/CD** (`.github/workflows/python-ci-cd.yml`): Tests and builds the Python orchestrator Docker image
3. **Go Scanner CI/CD** (`.github/workflows/go-ci-cd.yml`): Tests and builds the Go scanner Docker image
4. **Kubernetes Deployment** (`.github/workflows/k8s-deploy.yml`): Deploys the applications to Kubernetes clusters

## Required Secrets

To make these workflows function properly, you need to set up the following GitHub repository secrets:

### Docker Hub Secrets
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: A Docker Hub access token with push permissions

### Kubernetes Secrets
- `DEV_KUBECONFIG`: The kubeconfig file contents for the development cluster
- `PROD_KUBECONFIG`: The kubeconfig file contents for the production cluster

## Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add each of the secrets mentioned above

## How to Create Docker Hub Token

1. Log in to your Docker Hub account
2. Go to "Account Settings" > "Security"
3. Click "New Access Token"
4. Give it a name (e.g., "TraderAdmin CI/CD")
5. Choose appropriate permissions (Read & Write)
6. Click "Generate" and copy the token

## How to Obtain Kubeconfig

### For Development Environment:
```bash
kubectl config view --minify --flatten --context=your-dev-context > dev-kubeconfig.yaml
```

### For Production Environment:
```bash
kubectl config view --minify --flatten --context=your-prod-context > prod-kubeconfig.yaml
```

Then copy the contents of these files and add them as secrets.

## Testing the Workflows

- **Test GUI Build**: Create a PR to main
- **Test Docker Builds**: Push to main to trigger the Docker image builds
- **Test Deployments**: After Docker images are built, the K8s deployment should happen automatically

## Troubleshooting

Common issues:

1. **Docker Hub Authentication Failures**: Check your DOCKERHUB_USERNAME and DOCKERHUB_TOKEN
2. **Kubernetes Deployment Failures**: Verify the kubeconfig files and make sure they have the right permissions
3. **Missing Directories**: Ensure the python/, go/, and k8s/ directories exist with proper content 