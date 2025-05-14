# 01-docker-compose.md

## 1. Overview

This document defines a Docker Compose setup for local development, orchestrating the Python Orchestrator, Go Scanner service, and a Redis cache (for shared state or rate-limiting).  It provides a simple way to spin up all services with one command, facilitating end-to-end testing without Kubernetes.

## 2. docker-compose.yml

Place in the project root:

```yaml
version: '3.8'
services:
  python-orch:
    image: ${REGISTRY:-localhost:5000}/python-orch:latest
    build:
      context: ./trader-orchestrator/src
      dockerfile: Dockerfile
    environment:
      - CONFIG_PATH=/app/config.yaml
    volumes:
      - ./trader-orchestrator/config.yaml:/app/config.yaml:ro
    ports:
      - "8000:8000"   # health & gRPC
    depends_on:
      - redis

  go-scanner:
    image: ${REGISTRY:-localhost:5000}/go-scanner:latest
    build:
      context: ./trader-scanner
      dockerfile: cmd/scanner/Dockerfile
    environment:
      - CONFIG_PATH=/app/config.json
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./trader-scanner/config.json:/app/config.json:ro
    ports:
      - "2112:2112"    # Prometheus metrics
    depends_on:
      - python-orch
      - redis

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

networks:
  default:
    driver: bridge
```

## 3. Usage

* **Start services**:

  ```bash
  docker-compose up --build
  ```
* **Stop services**:

  ```bash
  docker-compose down
  ```
* **Logs**:
  View combined logs:

  ```bash
  docker-compose logs -f
  ```

## 4. Cucumber Scenarios

```gherkin
Feature: Docker Compose Setup
  Scenario: Bring up all services
    Given docker and docker-compose are installed
    When I run "docker-compose up --build"
    Then services python-orch, go-scanner, and redis start successfully

  Scenario: Health endpoints are reachable
    Given services are running
    When I GET http://localhost:8000/health
    Then response.status == 200
    And I GET http://localhost:2112/metrics
    Then response contains "scan_requests_total"
```

## 5. Pseudocode Outline

```text
# Start all containers
$ docker-compose up --build

# Check health
$ curl http://localhost:8000/health
{ "status": "ok" }

# Check metrics
$ curl http://localhost:2112/metrics | grep scan_requests_total
```
