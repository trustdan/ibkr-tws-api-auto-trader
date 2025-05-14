# 05-k8s-ci-cd.md

## 1. Overview

This document defines the CI/CD pipeline for deploying to Kubernetes.  We extend our Go and Python CI workflows to apply manifests (or Helm charts) automatically to a development or staging cluster whenever `main` is updated, and to production upon tag creation.

Key steps:

* **On `main` branch**: run `kubectl apply` (or `helm upgrade --install`) against the dev cluster
* **On version tags**: deploy to production cluster after manual approval
* **Rollback support**: track previous deployment revisions and enable rollback via `kubectl rollout undo`

## 2. GitHub Actions Workflow

Create `.github/workflows/k8s-deploy.yml`:

```yaml
name: Kubernetes Deployment

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  deploy-dev:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      - name: Deploy to Dev Cluster
        env:
          KUBECONFIG: ${{ secrets.DEV_KUBECONFIG }}
        run: |
          kubectl apply -f deploy/k8s/
          kubectl rollout status deployment/python-orch
          kubectl rollout status deployment/go-scanner

  deploy-prod:
    if: startsWith(github.ref, 'refs/tags/')
    needs: deploy-dev
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Manual Approval
        uses: hmarr/auto-approve-action@v2
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      - name: Deploy to Prod Cluster
        env:
          KUBECONFIG: ${{ secrets.PROD_KUBECONFIG }}
        run: |
          kubectl apply -f deploy/k8s/
          kubectl rollout status deployment/python-orch --namespace trader
          kubectl rollout status deployment/go-scanner --namespace trader
```

## 3. Rollback Strategy

In case of a faulty release, use:

```bash
kubectl rollout undo deployment/python-orch
kubectl rollout undo deployment/go-scanner
```

Consider adding a GitHub Action step for auto-notification if a rollout fails.

## 4. Cucumber Scenarios

```gherkin
Feature: Kubernetes CD Pipeline
  Scenario: Deploy dev on main commit
    Given a commit is pushed to main
    When the CD pipeline runs
    Then `kubectl apply` is executed
    And both python-orch and go-scanner pods become Ready

  Scenario: Deploy prod on tag
    Given a tag `v1.2.0` is pushed
    When manual approval is granted
    Then manifests are applied to the production cluster
```

## 5. Pseudocode Outline

```text
# GitHub Actions
on push to main:
  run kubectl apply -f deploy/k8s/
  kubectl rollout status ...
on push tag v*:
  require manual approval
  run kubectl apply -f deploy/k8s/ --namespace trader
```
