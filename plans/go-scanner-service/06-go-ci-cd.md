# 06-go-ci-cd.md

## 1. Overview

This document outlines the CI/CD pipeline for the Go Scanner service. We will:

* **Code Quality**: run `go fmt`, `go vet`, and unit tests on every PR
* **Docker Build**: produce a multi-stage Docker image (`go-scanner:latest`)
* **Publish**: push the image to a container registry on merges to `main` or version tags
* **Deploy**: update Kubernetes deployments automatically

By automating these steps, we maintain high code quality, ensure repeatable builds, and streamline deployments.

## 2. Dockerfile

Place at `cmd/scanner/Dockerfile`:

```dockerfile
# --- Stage 1: Build and Test ---
FROM golang:1.20-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# Code quality checks
RUN go fmt ./... && go vet ./... && go test ./pkg/... ./cmd/scanner/...
# Build binary
RUN go build -o scanner cmd/scanner/main.go

# --- Stage 2: Runtime ---
FROM alpine:3.16
WORKDIR /app
COPY --from=builder /app/scanner /usr/local/bin/scanner
COPY config.json /app/config.json
EXPOSE 2112 9090
ENTRYPOINT ["scanner", "--config", "/app/config.json"]
```

## 3. GitHub Actions Workflow

Create `.github/workflows/ci-cd-go.yml`:

```yaml
name: Go Scanner CI/CD

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  lint-test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.20'
      - name: Install dependencies
        run: go mod download
      - name: Lint and Vet
        run: |
          go fmt ./... && go vet ./...
      - name: Run tests
        run: go test -v ./pkg/... ./cmd/scanner/...

  build-and-push:
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')
    needs: lint-test-build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          docker build -f cmd/scanner/Dockerfile -t ${{ secrets.REGISTRY }}/go-scanner:${{ github.sha }} .
      - name: Login to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login ${{ secrets.REGISTRY }} -u ${{ secrets.REGISTRY_USER }} --password-stdin
      - name: Push Docker image
        run: |
          docker push ${{ secrets.REGISTRY }}/go-scanner:${{ github.sha }}
      - name: Update K8s Deployment
        uses: appleboy/ssh-action@v0.1.7
        with:
          host: ${{ secrets.K8S_HOST }}
          username: ${{ secrets.K8S_USER }}
          key: ${{ secrets.K8S_SSH_KEY }}
          script: |
            kubectl set image deployment/go-scanner go-scanner=${{ secrets.REGISTRY }}/go-scanner:${{ github.sha }}
```

## 4. Cucumber Scenarios

```gherkin
Feature: Go Scanner CI/CD Pipeline
  Scenario: Lint, vet, and tests on PR
    Given a pull request is opened against main
    When the CI pipeline runs
    Then go fmt, go vet, and go test all pass

  Scenario: Docker build and push on main
    Given a commit is merged into main
    When the CI pipeline completes
    Then a Docker image tagged with the commit SHA is pushed
    And the Kubernetes deployment is updated with the new image
```

## 5. Pseudocode Outline

```text
# On PR builds:
go fmt ./...
go vet ./...
go test ./...

# On main/tag builds:
docker build -f cmd/scanner/Dockerfile -t registry/go-scanner:sha .
docker push registry/go-scanner:sha
ssh deploy-host "kubectl set image ..."
```
