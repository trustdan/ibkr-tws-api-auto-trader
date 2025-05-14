# 06-python-ci-cd.md

## 1. Overview

This document defines the continuous integration and delivery (CI/CD) pipeline for the Python orchestrator. We'll:

* **Lint & Format**: Enforce code style via `flake8` and `black` on every PR.
* **Unit & BDD Tests**: Run `pytest` and `pytest-bdd` scenarios to validate functionality.
* **Build & Publish**: On merges to `main` (and on tags), build a Docker image (`python-orch:latest`), push to a container registry, and update the development Kubernetes cluster.

This ensures our orchestrator remains reliable, test-covered, and deployable with minimal manual intervention.

## 2. Project Setup

First, ensure your project has proper dependency management using Poetry. Create or update `pyproject.toml`:

```toml
[tool.poetry]
name = "ibkr-trader-orchestrator"
version = "0.1.0"
description = "Python-based orchestrator for IBKR TWS trading strategies"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
ib-insync = "^0.9.85"
fastapi = "^0.100.0"
uvicorn = "^0.22.0"
pydantic = "^2.0.3"
pyyaml = "^6.0"
pandas = "^2.0.3"
numpy = "^1.25.1"
loguru = "^0.7.0"
grpcio = "^1.56.0"
grpcio-tools = "^1.56.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.1"
pytest-bdd = "^6.1.1"
black = "^23.7.0"
flake8 = "^6.0.0"
mypy = "^1.4.1"
isort = "^5.12.0"

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.isort]
profile = "black"
line_length = 88

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

## 3. Dockerfile

Create a multi-stage Dockerfile at the root of your project:

```dockerfile
# --- Stage 1: Build and Test ---
FROM python:3.10-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install poetry==1.5.1 && \
    poetry config virtualenvs.create false

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# --- Stage 2: Runtime ---
FROM python:3.10-slim

WORKDIR /app

# Install required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY src /app/src
COPY config.yaml /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 4. Health Check Endpoint

Add a health check endpoint to your FastAPI application in `src/app/main.py`:

```python
import logging
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ib_insync import IB

from src.config.loader import load_config
from src.ibkr.connector import IBConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IBKR TWS Orchestrator",
    description="Python orchestrator for IBKR TWS trading strategies",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config = load_config("config.yaml")

# Create IB connector (but don't connect yet)
ib_connector = IBConnector()
ib: IB = None

@app.on_event("startup")
async def startup_event():
    """Connect to IB TWS on startup if auto_connect is enabled"""
    global ib
    if config.get("ibkr", {}).get("auto_connect", False):
        try:
            ib = ib_connector.connect(
                host=config["ibkr"]["host"],
                port=config["ibkr"]["port"],
                client_id=config["ibkr"]["client_id"],
            )
            logger.info("Connected to IB TWS on startup")
        except Exception as e:
            logger.error(f"Failed to connect to IB TWS on startup: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from IB TWS on shutdown"""
    global ib
    if ib and ib.isConnected():
        ib_connector.disconnect()
        logger.info("Disconnected from IB TWS on shutdown")


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/status", tags=["Health"])
async def status() -> Dict[str, bool]:
    """Get connection status"""
    global ib
    is_connected = False
    if ib:
        is_connected = ib.isConnected()
    return {"connected": is_connected}


@app.post("/connect", tags=["IB"])
async def connect() -> Dict[str, bool]:
    """Connect to IB TWS"""
    global ib
    try:
        ib = ib_connector.connect(
            host=config["ibkr"]["host"],
            port=config["ibkr"]["port"],
            client_id=config["ibkr"]["client_id"],
        )
        return {"connected": ib.isConnected()}
    except Exception as e:
        logger.error(f"Failed to connect to IB TWS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disconnect", tags=["IB"])
async def disconnect() -> Dict[str, bool]:
    """Disconnect from IB TWS"""
    global ib
    if ib and ib.isConnected():
        ib_connector.disconnect()
    return {"connected": False}
```

## 5. GitHub Actions Workflow

Create `.github/workflows/ci-cd-python.yml`:

```yaml
name: Python Orchestrator CI/CD

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          poetry install
      
      - name: Lint with flake8
        run: |
          poetry run flake8 src tests
      
      - name: Format check with black
        run: |
          poetry run black --check src tests
      
      - name: Type check with mypy
        run: |
          poetry run mypy src
      
      - name: Run tests
        run: |
          poetry run pytest --maxfail=1 --disable-warnings -v

  build-and-push:
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')
    needs: lint-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          registry: ${{ secrets.REGISTRY }}
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ secrets.REGISTRY }}/python-orch
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,format=long
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ secrets.REGISTRY }}/python-orch:cache
          cache-to: type=registry,ref=${{ secrets.REGISTRY }}/python-orch:cache,mode=max

  deploy-to-dev:
    if: github.ref == 'refs/heads/main'
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v3
      
      - name: Update K8s Deployment
        uses: appleboy/ssh-action@v0.1.7
        with:
          host: ${{ secrets.K8S_HOST }}
          username: ${{ secrets.K8S_USER }}
          key: ${{ secrets.K8S_SSH_KEY }}
          script: |
            cd ~/kubernetes/manifests
            kubectl set image deployment/python-orch python-orch=${{ secrets.REGISTRY }}/python-orch:sha-${{ github.sha }} --record

  deploy-to-production:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      - name: Extract tag name
        id: tag
        run: echo "TAG=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
      
      - name: Update K8s Deployment
        uses: appleboy/ssh-action@v0.1.7
        with:
          host: ${{ secrets.PROD_K8S_HOST }}
          username: ${{ secrets.PROD_K8S_USER }}
          key: ${{ secrets.PROD_K8S_SSH_KEY }}
          script: |
            cd ~/kubernetes/manifests
            kubectl set image deployment/python-orch python-orch=${{ secrets.REGISTRY }}/python-orch:${{ steps.tag.outputs.TAG }} --record
```

## 6. Local Development Setup

Add a `docker-compose.yml` file to simplify local development:

```yaml
version: '3.8'

services:
  python-orch:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml
    environment:
      - IBKR_HOST=${IBKR_HOST:-localhost}
      - IBKR_PORT=${IBKR_PORT:-7497}
      - IBKR_CLIENT_ID=${IBKR_CLIENT_ID:-1}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s
```

### Pre-commit Hooks

To ensure code quality during local development, set up pre-commit hooks with a phased adoption approach:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        args: [--line-length=88]
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  # Flake8 is commented out initially to allow gradual adoption
  # Uncomment when ready to enforce stricter linting
  # - repo: https://github.com/pycqa/flake8
  #   rev: 6.0.0
  #   hooks:
  #     - id: flake8
  #       args: [--max-line-length=88, --extend-ignore=E203]
  #       exclude: examples/
  #       additional_dependencies:
  #         - flake8-bugbear
```

Also create a `setup.cfg` file to configure flake8 behavior for when you're ready to enforce it:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, E501
per-file-ignores =
    # Allow unused imports in __init__.py files
    */__init__.py:F401
    # Allow imports not at top in example files and unused imports
    */examples/*.py:E402,F401,E231,E501
    # Allow unused imports and long lines in tests
    */tests/*.py:F401,E501
    # Allow unused imports in module files 
    */src/*/*.py:F401,E231
    # Ignore specific loop variable issue in market data test
    */tests/step_defs/test_market_data.py:B007
```

#### Phased Adoption Approach

1. **Phase 1**: Start with Black and isort only
   - This automatically formats code while being minimally disruptive
   - Run: `poetry run pre-commit run --all-files` to apply formatting

2. **Phase 2**: Introduce flake8 with broad exceptions
   - Uncomment the flake8 section in `.pre-commit-config.yaml`
   - Fix errors gradually in logical chunks

3. **Phase 3**: Tighten flake8 rules
   - Update `setup.cfg` to gradually remove exceptions
   - Focus on one type of issue at a time

Install and run the hooks with:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 7. Kubernetes Manifests

Create a basic Kubernetes deployment in `k8s/python-orch-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-orch
  labels:
    app: python-orch
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
        image: ${REGISTRY}/python-orch:latest
        ports:
        - containerPort: 8000
        env:
        - name: IBKR_HOST
          valueFrom:
            configMapKeyRef:
              name: ibkr-config
              key: host
        - name: IBKR_PORT
          valueFrom:
            configMapKeyRef:
              name: ibkr-config
              key: port
        - name: IBKR_CLIENT_ID
          valueFrom:
            configMapKeyRef:
              name: ibkr-config
              key: client_id
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: python-orch
spec:
  selector:
    app: python-orch
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ibkr-config
data:
  host: "192.168.1.100"  # Replace with your TWS host
  port: "7497"
  client_id: "1"
```

## 8. CI/CD Secrets

Configure the following GitHub secrets for your repository:

- `REGISTRY`: Your container registry URL (e.g., `docker.io/yourname`)
- `REGISTRY_USER`: Username for your container registry
- `REGISTRY_PASSWORD`: Password for your container registry
- `K8S_HOST`: Development Kubernetes cluster SSH hostname
- `K8S_USER`: Development Kubernetes cluster SSH username
- `K8S_SSH_KEY`: Development Kubernetes cluster SSH private key
- `PROD_K8S_HOST`: Production Kubernetes cluster SSH hostname
- `PROD_K8S_USER`: Production Kubernetes cluster SSH username
- `PROD_K8S_SSH_KEY`: Production Kubernetes cluster SSH private key

## 9. Cucumber Scenarios

Here are BDD scenarios for CI/CD:

```gherkin
Feature: Python CI/CD Pipeline
  Scenario: Lint and tests on PR
    Given a pull request to main
    When CI runs
    Then flake8 and black pass without errors
    And pytest reports zero failures

  Scenario: Docker build and push on main
    Given a commit to main
    When CI runs
    Then a Docker image is built and pushed to the registry
    And the K8s deployment is updated

  Scenario: Release deployment on tag
    Given a new version tag is pushed
    When CI runs
    Then a Docker image with the tag version is built and pushed
    And the production K8s deployment is updated with approval
```

## 10. Testing the Pipeline

To test the pipeline locally before pushing to GitHub:

1. Install `act` to run GitHub Actions locally:
   ```sh
   # On macOS
   brew install act
   
   # On Linux
   curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

2. Run the lint and test job:
   ```sh
   act -j lint-and-test
   ```

3. Run the build job (requires Docker):
   ```sh
   # Create a .secrets file with your registry credentials
   echo "REGISTRY=docker.io/yourname" > .secrets
   echo "REGISTRY_USER=yourusername" >> .secrets
   echo "REGISTRY_PASSWORD=yourpassword" >> .secrets
   
   act -j build-and-push --secret-file .secrets
   ```

## 11. Conclusion

This CI/CD pipeline ensures:

- Code quality through automated linting and testing
- Reproducible builds via Docker
- Continuous deployment to development environment on merges to main
- Production deployments when version tags are pushed
- Health checks to validate deployed services

All changes go through rigorous testing before deployment, and the pipeline automates the tedious tasks of building, testing, and deploying, allowing developers to focus on implementing features and fixing bugs.

You'd most naturally fold that guidance into **06-python-ci-cd.md** under the "Lint & Format" section. In that doc's CI/CD overview and Dockerfile / Actions steps, add a subsection like:

```
