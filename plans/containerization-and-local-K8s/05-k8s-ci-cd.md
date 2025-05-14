# 05-k8s-ci-cd.md

## 1. Overview

This document defines the CI/CD pipeline for deploying our trading system to Kubernetes clusters. We'll use GitHub Actions to automatically deploy our Helm charts to development environments on every merge to `main`, and to production upon tag creation with manual approval.

Key features:

* **Helm-based deployments**: Leverage our `charts/traderadmin` Helm chart for consistent deployments
* **Environment-specific configs**: Use value files for different environments (dev, staging, production)
* **Automated validation**: Verify deployments with health checks and rollback on failure
* **Manual approval gate**: Require human review before production deployments
* **Secure credentials**: Store sensitive Kubernetes config via GitHub secrets

## 2. Prerequisites

* GitHub repository with Actions enabled
* Kubernetes clusters for development and production
* Base64-encoded kubeconfig files for each cluster
* Docker images built and pushed by the existing CI pipelines

## 3. Directory Structure

```
.github/
  workflows/
    k8s-deploy.yml
deploy/
  values/
    values-dev.yaml
    values-staging.yaml
    values-prod.yaml
charts/
  traderadmin/
    # Helm chart as previously implemented
```

## 4. Environment Values Files

### 4.1 Development (values-dev.yaml)

```yaml
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
  goScanner:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 300m
      memory: 256Mi

config:
  python:
    ibkr:
      host: "dev-tws-host"
      port: 7497
    strategy:
      sma_period: 50
      candle_count: 2
      otm_offset: 1
      iv_threshold: 0.8
      min_reward_risk: 1.0
  scanner:
    universe: ["AAPL", "MSFT", "SPY", "QQQ", "NVDA"]
```

### 4.2 Production (values-prod.yaml)

```yaml
replicaCount:
  pythonOrch: 2  # Higher availability
  goScanner: 2

resources:
  pythonOrch:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  goScanner:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

config:
  python:
    ibkr:
      host: "prod-tws-host"
      port: 7496  # Production TWS port
    strategy:
      sma_period: 50
      candle_count: 2
      otm_offset: 1
      iv_threshold: 0.8
      min_reward_risk: 1.0
  scanner:
    universe: ["AAPL", "MSFT", "AMZN", "GOOG", "META", "TSLA", "SPY", "QQQ", "DIA", "IWM", "EEM", "GLD", "TLT", "XLF", "XLE"]
```

## 5. GitHub Actions CI/CD Workflow

Create `.github/workflows/k8s-deploy.yml`:

```yaml
name: Kubernetes Deployment

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod
      version:
        description: 'Version to deploy (default: latest)'
        required: false
        type: string

jobs:
  validate-chart:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Helm
        uses: azure/setup-helm@v3
        with:
          version: 'v3.10.0'
      
      - name: Validate Helm Chart
        run: |
          helm lint charts/traderadmin
          helm template charts/traderadmin
  
  deploy-dev:
    needs: validate-chart
    if: github.ref == 'refs/heads/main' || (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'dev')
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      
      - name: Set up Helm
        uses: azure/setup-helm@v3
        with:
          version: 'v3.10.0'
      
      - name: Configure kubeconfig
        run: |
          echo "${{ secrets.DEV_KUBECONFIG }}" | base64 -d > kubeconfig.yaml
          echo "KUBECONFIG=kubeconfig.yaml" >> $GITHUB_ENV
      
      - name: Set image tags
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" && "${{ github.event.inputs.version }}" != "" ]]; then
            VERSION="${{ github.event.inputs.version }}"
          else
            VERSION="sha-${GITHUB_SHA::8}"
          fi
          echo "Using version: $VERSION"
          echo "VERSION=$VERSION" >> $GITHUB_ENV
      
      - name: Deploy to Dev Cluster
        run: |
          helm upgrade --install traderadmin charts/traderadmin \
            --namespace trader --create-namespace \
            -f deploy/values/values-dev.yaml \
            --set image.pythonOrch=your-registry/python-orch:${VERSION} \
            --set image.goScanner=your-registry/go-scanner:${VERSION}
      
      - name: Verify Deployment
        run: |
          kubectl rollout status deployment/traderadmin-python-orch -n trader --timeout=300s
          kubectl rollout status deployment/traderadmin-go-scanner -n trader --timeout=300s
      
      - name: Health Check
        run: |
          kubectl port-forward svc/traderadmin-python-orch 8000:8000 -n trader &
          PID=$!
          sleep 5
          curl -f http://localhost:8000/health || (kill $PID && exit 1)
          kill $PID
  
  deploy-staging:
    needs: validate-chart
    if: github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'staging'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      # Similar to dev deployment but using staging config and secrets
      - uses: actions/checkout@v3
      
      - name: Set up kubectl and Helm
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      
      - name: Set up Helm
        uses: azure/setup-helm@v3
        with:
          version: 'v3.10.0'
      
      - name: Configure kubeconfig
        run: |
          echo "${{ secrets.STAGING_KUBECONFIG }}" | base64 -d > kubeconfig.yaml
          echo "KUBECONFIG=kubeconfig.yaml" >> $GITHUB_ENV
      
      - name: Deploy to Staging
        run: |
          VERSION="${{ github.event.inputs.version }}"
          if [[ -z "$VERSION" ]]; then
            VERSION="sha-${GITHUB_SHA::8}"
          fi
          helm upgrade --install traderadmin charts/traderadmin \
            --namespace trader --create-namespace \
            -f deploy/values/values-staging.yaml \
            --set image.pythonOrch=your-registry/python-orch:${VERSION} \
            --set image.goScanner=your-registry/go-scanner:${VERSION}
      
      - name: Verify Deployment
        run: |
          kubectl rollout status deployment/traderadmin-python-orch -n trader --timeout=300s
          kubectl rollout status deployment/traderadmin-go-scanner -n trader --timeout=300s
  
  deploy-prod:
    needs: validate-chart
    if: startsWith(github.ref, 'refs/tags/v') || (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'prod')
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://traderadmin-prod.example.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      
      - name: Set up Helm
        uses: azure/setup-helm@v3
        with:
          version: 'v3.10.0'
      
      - name: Configure kubeconfig
        run: |
          echo "${{ secrets.PROD_KUBECONFIG }}" | base64 -d > kubeconfig.yaml
          echo "KUBECONFIG=kubeconfig.yaml" >> $GITHUB_ENV
      
      - name: Extract version
        id: extract_version
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" && "${{ github.event.inputs.version }}" != "" ]]; then
            VERSION="${{ github.event.inputs.version }}"
          elif [[ "${{ github.ref }}" == refs/tags/* ]]; then
            VERSION="${{ github.ref_name }}"
          else
            VERSION="sha-${GITHUB_SHA::8}"
          fi
          echo "Using version: $VERSION"
          echo "VERSION=$VERSION" >> $GITHUB_ENV
      
      - name: Deploy to Production
        run: |
          helm upgrade --install traderadmin charts/traderadmin \
            --namespace trader --create-namespace \
            -f deploy/values/values-prod.yaml \
            --set image.pythonOrch=your-registry/python-orch:${VERSION} \
            --set image.goScanner=your-registry/go-scanner:${VERSION}
      
      - name: Verify Deployment
        run: |
          kubectl rollout status deployment/traderadmin-python-orch -n trader --timeout=300s
          kubectl rollout status deployment/traderadmin-go-scanner -n trader --timeout=300s
      
      - name: Notify Deployment
        if: success()
        run: |
          echo "Production deployment of version ${VERSION} completed successfully"
          # Add notification logic here (Slack, Teams, email)
```

## 6. Local Testing of CI/CD

To test the CI/CD workflow locally before pushing to GitHub:

1. Install `act` to run GitHub Actions locally:
   ```bash
   # On Windows with Chocolatey
   choco install act-cli
   
   # On macOS
   brew install act
   ```

2. Create a `.secrets` file with your kubeconfig:
   ```
   DEV_KUBECONFIG=<base64-encoded-kubeconfig>
   ```

3. Test the workflow:
   ```bash
   act -j deploy-dev --secret-file .secrets
   ```

## 7. Rollback Procedures

### 7.1 Using Helm Rollback

Helm maintains a history of releases, making rollbacks straightforward:

```bash
# List release history
helm history traderadmin -n trader

# Rollback to previous release
helm rollback traderadmin 1 -n trader

# Rollback to specific revision
helm rollback traderadmin <revision_number> -n trader
```

### 7.2 Emergency Rollback in GitHub Actions

Add this job to your workflow file for manual emergency rollbacks:

```yaml
emergency-rollback:
  if: github.event_name == 'workflow_dispatch' && github.event.inputs.rollback == 'true'
  runs-on: ubuntu-latest
  environment: 
    name: ${{ github.event.inputs.environment }}
  steps:
    - name: Configure kubeconfig
      run: |
        if [[ "${{ github.event.inputs.environment }}" == "prod" ]]; then
          echo "${{ secrets.PROD_KUBECONFIG }}" | base64 -d > kubeconfig.yaml
        elif [[ "${{ github.event.inputs.environment }}" == "staging" ]]; then
          echo "${{ secrets.STAGING_KUBECONFIG }}" | base64 -d > kubeconfig.yaml
        else
          echo "${{ secrets.DEV_KUBECONFIG }}" | base64 -d > kubeconfig.yaml
        fi
        echo "KUBECONFIG=kubeconfig.yaml" >> $GITHUB_ENV
    
    - name: Rollback to previous release
      run: |
        helm rollback traderadmin 0 -n trader
        kubectl rollout status deployment/traderadmin-python-orch -n trader
        kubectl rollout status deployment/traderadmin-go-scanner -n trader
```

## 8. Security Considerations

1. **Secrets management**: Store kubeconfig and credentials as encrypted GitHub secrets
2. **RBAC**: Use service accounts with limited permissions for CI/CD
3. **Container scanning**: Add Trivy or Anchore scanning before deployment
4. **Manual approval**: Keep the manual approval gate for production deployments

## 9. Cucumber Scenarios

```gherkin
Feature: Kubernetes CI/CD Pipeline
  Scenario: Automatic deployment to dev
    Given a commit is pushed to main branch
    When the CI/CD pipeline runs
    Then the Helm chart is validated
    And the chart is deployed to the development cluster
    And deployment status is verified with health checks

  Scenario: Versioned deployment to production
    Given a new tag "v1.2.0" is pushed
    When CI/CD pipeline runs with manual approval
    Then the production environment receives version "v1.2.0"
    And all services are healthy after deployment

  Scenario: Rollback on failure
    Given a deployment in progress
    When health checks fail
    Then automatic rollback is triggered
    And notification is sent to the team
```

## 10. Troubleshooting

### 10.1 Common Issues

1. **Failed deployment**: Check pod logs and events
   ```bash
   kubectl logs -n trader deploy/traderadmin-python-orch
   kubectl describe pod -n trader -l app=traderadmin-python-orch
   ```

2. **Stuck rollout**: Force rollback and check logs
   ```bash
   helm rollback traderadmin 0 -n trader
   kubectl get events -n trader --sort-by='.lastTimestamp'
   ```

3. **Invalid Helm chart**: Run helm lint and template locally
   ```bash
   helm lint charts/traderadmin
   helm template charts/traderadmin -f deploy/values/values-dev.yaml
   ```

### 10.2 Debugging CI/CD Workflow

1. View GitHub Actions logs in the repository's Actions tab
2. Compare failed deployment parameters with successful ones
3. Manually apply the Helm chart with `--debug` for verbose output

## 11. Windows Compatibility

For Windows users working with the CI/CD pipeline:

1. **Setting up kubeconfig**:
   ```powershell
   # Convert kubeconfig to base64
   [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Raw kubeconfig.yaml)))
   ```

2. **Local Helm testing**:
   ```powershell
   helm upgrade --install --dry-run traderadmin .\charts\traderadmin -f .\deploy\values\values-dev.yaml
   ```

3. **Deployment verification**:
   ```powershell
   kubectl port-forward -n trader svc/traderadmin-python-orch 8000:8000
   Invoke-RestMethod -Uri http://localhost:8000/health
   ```
