# 06-go-ci-cd.md

## 1. Overview

This document outlines the CI/CD pipeline for the Go Scanner service. Our automated pipeline will:

* **Code Quality**: Run `go fmt`, `go vet`, static analysis, and linting on every PR
* **Testing**: Execute unit and integration tests with coverage reporting
* **Security**: Scan dependencies and container images for vulnerabilities
* **Build**: Create optimized, multi-stage Docker images with proper versioning
* **Publish**: Push images to a secure container registry with proper tags
* **Deploy**: Implement progressive delivery to development/staging/production environments

By automating these processes, we ensure consistent code quality, repeatable builds, and reliable deployments while maintaining a clear audit trail of changes.

## 2. Dockerfile with Best Practices

Create a production-ready Dockerfile at `cmd/scanner/Dockerfile`:

```dockerfile
# --- Stage 1: Build and Test ---
FROM golang:1.20-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata && \
    update-ca-certificates

# Create non-root user for running the application
RUN adduser -D -g '' scanner

WORKDIR /build

# Copy and download dependencies first (for better caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Run tests and quality checks
RUN go fmt ./... && \
    go vet ./... && \
    go test -v -cover ./pkg/... ./cmd/scanner/...

# Build binary with security flags
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -X main.version=${VERSION} -X main.buildTime=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    -o scanner cmd/scanner/main.go

# --- Stage 2: Security Scan ---
FROM aquasec/trivy:latest AS security-scan
WORKDIR /scan
COPY --from=builder /build/scanner .
RUN trivy fs --exit-code 1 --severity HIGH,CRITICAL --no-progress /scan

# --- Stage 3: Minimal Runtime ---
FROM alpine:3.16

# Add runtime dependencies and security updates
RUN apk add --no-cache ca-certificates tzdata && \
    update-ca-certificates

# Create configuration directory
WORKDIR /app
COPY config.json /app/config.json

# Copy binary from builder stage
COPY --from=builder /build/scanner /usr/local/bin/scanner
COPY --from=builder /etc/passwd /etc/passwd

# Use non-root user
USER scanner

# Declare volumes for persistent data
VOLUME ["/app/data"]

# Expose Prometheus metrics and gRPC ports
EXPOSE 2112 9090

# Set default command
ENTRYPOINT ["/usr/local/bin/scanner"]
CMD ["--config", "/app/config.json"]

# Add metadata
LABEL org.opencontainers.image.source="https://github.com/your-org/trader-scanner" \
      org.opencontainers.image.description="Go Scanner Service for Trading Signals" \
      org.opencontainers.image.licenses="MIT"
```

## 3. GitHub Actions Workflow

Create a comprehensive workflow at `.github/workflows/go-scanner-pipeline.yml`:

```yaml
name: Go Scanner CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'pkg/**'
      - 'cmd/scanner/**'
      - 'go.mod'
      - 'go.sum'
      - '.github/workflows/go-scanner-pipeline.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'pkg/**'
      - 'cmd/scanner/**'
      - 'go.mod'
      - 'go.sum'
  release:
    types: [created]

env:
  GO_VERSION: '1.20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/go-scanner

jobs:
  lint-and-test:
    name: Lint and Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true
          
      - name: Install dependencies
        run: go mod download
        
      - name: Run go fmt
        run: |
          go fmt ./...
          if [ -n "$(git status --porcelain)" ]; then
            echo "Code is not formatted with go fmt"
            exit 1
          fi
          
      - name: Run go vet
        run: go vet ./...
        
      - name: Run staticcheck
        uses: dominikh/staticcheck-action@v1.3.0
        with:
          version: latest
          install-go: false
          
      - name: Run tests with coverage
        run: |
          go test -race -coverprofile=coverage.txt -covermode=atomic ./pkg/... ./cmd/scanner/...
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.txt
          flags: unittests
          
  dependency-scan:
    name: Scan Dependencies
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
          
      - name: Run Nancy (Vulnerability Scanner)
        uses: sonatype-nexus-community/nancy-github-action@main
        
  build-and-push:
    name: Build and Push Docker Image
    needs: [lint-and-test, dependency-scan]
    if: ${{ github.event_name != 'pull_request' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,format=long
            type=ref,event=branch
            type=semver,pattern={{version}},event=release
            
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: cmd/scanner/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            VERSION=${{ github.ref_name }}
            
      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
          
  deploy-to-dev:
    name: Deploy to Development
    needs: build-and-push
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: development
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Set up Kubernetes tools
        uses: azure/setup-kubectl@v3
        
      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBECONFIG_DEV }}
          
      - name: Deploy to development
        run: |
          sed -i "s|image: .*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}|g" k8s/dev/go-scanner-deployment.yaml
          kubectl apply -f k8s/dev/go-scanner-deployment.yaml
          kubectl rollout status deployment/go-scanner -n trading-dev
          
  deploy-to-prod:
    name: Deploy to Production
    needs: build-and-push
    if: github.event_name == 'release' && startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.trading.example.com/scanner
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Set up Kubernetes tools
        uses: azure/setup-kubectl@v3
        
      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBECONFIG_PROD }}
          
      - name: Deploy to production
        run: |
          VERSION=$(echo "${{ github.ref }}" | sed -e 's,.*/\(.*\),\1,')
          sed -i "s|image: .*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:$VERSION|g" k8s/prod/go-scanner-deployment.yaml
          kubectl apply -f k8s/prod/go-scanner-deployment.yaml
          kubectl rollout status deployment/go-scanner -n trading-prod
          
      - name: Verify deployment
        run: |
          kubectl run curl --image=curlimages/curl -n trading-prod --restart=Never --rm --wait -i -- \
          curl -s http://go-scanner-service:2112/health
          
      - name: Create deployment record
        uses: chrnorm/deployment-action@v2
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          environment: production
          description: "Deployed version ${{ github.ref_name }} to production"
```

## 4. Versioning Strategy

Implement semantic versioning for the Go Scanner service:

```go
// In cmd/scanner/main.go

var (
    // Set by build process
    version   = "dev"
    buildTime = "unknown"
)

func main() {
    // Log version info on startup
    log.Printf("Starting Go Scanner version %s (built at %s)", version, buildTime)
    
    // Add version endpoint
    http.HandleFunc("/version", func(w http.ResponseWriter, r *http.Request) {
        info := map[string]string{
            "version":    version,
            "build_time": buildTime,
        }
        json.NewEncoder(w).Encode(info)
    })
    
    // ... rest of main function
}
```

## 5. Kubernetes Deployment Templates

Create environment-specific deployment manifests:

### Development Environment (`k8s/dev/go-scanner-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-scanner
  namespace: trading-dev
  labels:
    app: go-scanner
    environment: development
spec:
  replicas: 1
  selector:
    matchLabels:
      app: go-scanner
  template:
    metadata:
      labels:
        app: go-scanner
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "2112"
    spec:
      containers:
      - name: go-scanner
        image: ghcr.io/your-org/trader-scanner/go-scanner:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 9090
          name: grpc
        - containerPort: 2112
          name: metrics
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 2112
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 2112
          initialDelaySeconds: 3
          periodSeconds: 5
        env:
        - name: LOG_LEVEL
          value: "debug"
        - name: PYTHON_ORCHESTRATOR_HOST
          value: "python-orch-service"
        - name: PYTHON_ORCHESTRATOR_PORT
          value: "50051"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.json
          subPath: config.json
      volumes:
      - name: config-volume
        configMap:
          name: go-scanner-config
---
apiVersion: v1
kind: Service
metadata:
  name: go-scanner-service
  namespace: trading-dev
spec:
  selector:
    app: go-scanner
  ports:
  - name: grpc
    port: 9090
    targetPort: 9090
  - name: metrics
    port: 2112
    targetPort: 2112
```

### Production Environment (`k8s/prod/go-scanner-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-scanner
  namespace: trading-prod
  labels:
    app: go-scanner
    environment: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: go-scanner
  template:
    metadata:
      labels:
        app: go-scanner
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "2112"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - go-scanner
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: go-scanner
        image: ghcr.io/your-org/trader-scanner/go-scanner:latest  # Will be replaced in CI
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 9090
          name: grpc
        - containerPort: 2112
          name: metrics
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 2112
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /health
            port: 2112
          initialDelaySeconds: 5
          periodSeconds: 10
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: PYTHON_ORCHESTRATOR_HOST
          value: "python-orch-service"
        - name: PYTHON_ORCHESTRATOR_PORT
          value: "50051"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config.json
          subPath: config.json
        - name: scanner-data
          mountPath: /app/data
      volumes:
      - name: config-volume
        configMap:
          name: go-scanner-config
      - name: scanner-data
        persistentVolumeClaim:
          claimName: go-scanner-data
---
apiVersion: v1
kind: Service
metadata:
  name: go-scanner-service
  namespace: trading-prod
spec:
  selector:
    app: go-scanner
  ports:
  - name: grpc
    port: 9090
    targetPort: 9090
  - name: metrics
    port: 2112
    targetPort: 2112
```

## 6. Release Process

Document the release process for new versions:

1. Create and merge feature branches into `develop`
2. Test thoroughly in the development environment
3. When ready for release:
   ```bash
   git checkout main
   git merge develop
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin main --tags
   ```
4. The GitHub Actions workflow will:
   - Build and tag the Docker image with the version
   - Push to container registry
   - Deploy to production with manual approval

## 7. Cucumber Scenarios

```gherkin
Feature: Go Scanner CI/CD Pipeline
  Scenario: Pull Request Quality Checks
    Given a developer opens a pull request against develop
    When the CI pipeline runs
    Then code formatting is checked
    And static analysis is performed
    And all tests pass with coverage report
    And dependencies are scanned for vulnerabilities

  Scenario: Automatic Development Deployment
    Given a pull request is merged to develop
    When the CI/CD pipeline completes
    Then a Docker image is built and tagged with the commit SHA
    And the image is pushed to the container registry
    And the development environment is updated with the new image
    And health checks confirm the service is running

  Scenario: Production Release
    Given a release tag v1.2.3 is created
    When the CI/CD pipeline runs
    Then a Docker image is tagged with v1.2.3
    And the production deployment requires manual approval
    And after approval, the production environment is updated
    And verification tests confirm the deployment success
    And a deployment record is created
```

## 8. Monitoring and Rollback

### Post-Deployment Monitoring

After each deployment, automatically monitor for failures:

```yaml
# In GitHub Actions workflow
- name: Monitor deployment health
  run: |
    # Check that pods are running
    HEALTHY=0
    for i in {1..12}; do
      if kubectl get pods -n trading-prod -l app=go-scanner | grep -q "Running"; then
        HEALTHY=1
        break
      fi
      echo "Waiting for pods to be ready... ($i/12)"
      sleep 10
    done
    
    if [ $HEALTHY -eq 0 ]; then
      echo "Deployment failed health check. Initiating rollback."
      kubectl rollout undo deployment/go-scanner -n trading-prod
      exit 1
    fi
    
    # Check application metrics
    ERRORS=$(curl -s http://go-scanner-service:2112/metrics | grep scanner_data_fetch_errors_total | wc -l)
    if [ $ERRORS -gt 0 ]; then
      echo "Detected errors in metrics. Initiating rollback."
      kubectl rollout undo deployment/go-scanner -n trading-prod
      exit 1
    fi
```

## 9. Security Best Practices

1. **Scan images** with Trivy before deployment
2. **Use non-root user** in container
3. **Limit container capabilities** in Kubernetes
4. **Store secrets** in Kubernetes secrets or external vault
5. **Regularly update** base images and dependencies

## 10. Implementation Checklist

- [ ] Create Dockerfile with multi-stage build
- [ ] Configure GitHub Actions workflow
- [ ] Add version information to application
- [ ] Create Kubernetes deployment manifests
- [ ] Set up secret management
- [ ] Configure deployment environments
- [ ] Create monitoring and rollback procedures
- [ ] Document release process for team members
