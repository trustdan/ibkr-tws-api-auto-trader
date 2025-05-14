# Docker Compose Setup for IBKR TWS API Auto Trader

This document explains how to use Docker Compose to run the complete trading system locally.

## Prerequisites

- Docker Engine 19.03.0+
- Docker Compose 1.27.0+
- Interactive Brokers TWS or IB Gateway running (for actual trading)

## Services

The Docker Compose setup includes:

1. **Python Orchestrator** - Manages IBKR connections and order execution
2. **Go Scanner** - Scans for trading opportunities based on technical patterns
3. **Redis** - Shared cache for optimization and rate limiting

## Getting Started

### Initial Setup

Create a `.env` file with your environment variables:

```bash
# Windows
copy NUL .env

# Linux/macOS
touch .env
```

Add the following content to the `.env` file:

```
# IBKR TWS API connection details
IB_HOST=localhost
IB_PORT=7497
IB_CLIENT_ID=1

# Docker registry configuration
REGISTRY=localhost:5000
```

### For Linux/macOS Users

1. Make the helper script executable:

```bash
chmod +x compose-manager.sh
```

2. Start all services:

```bash
./compose-manager.sh up
```

### For Windows Users

Use the batch file:

```cmd
compose-manager.bat up
```

The helper scripts will:
- Create necessary directories if they don't exist
- Generate default config files if not present
- Start all services
- Check service health

## Common Commands

View service logs:
```
# Linux/macOS
./compose-manager.sh logs

# Windows
compose-manager.bat logs
```

Check service health:
```
# Linux/macOS
./compose-manager.sh health

# Windows
compose-manager.bat health
```

Stop all services:
```
# Linux/macOS
./compose-manager.sh down

# Windows
compose-manager.bat down
```

## Configuration

### Environment Variables

You can customize the environment by editing the `.env` file with these variables:

```
# IBKR TWS API connection details
IB_HOST=localhost     # Change if TWS runs on a different host
IB_PORT=7497          # Use 7496 for TWS, 4001 for IB Gateway
IB_CLIENT_ID=1        # Change if multiple applications connect

# Docker registry configuration
REGISTRY=localhost:5000
```

### Service Configuration

- **Python Orchestrator**: Edit `trader-orchestrator/config.yaml`
- **Go Scanner**: Edit `trader-scanner/config.json`

Both config files are mounted as volumes, so changes take effect without rebuilding containers.

## Development Workflow

1. Make code changes to the Python or Go services
2. Rebuild the container images:

```
# Linux/macOS
./compose-manager.sh build

# Windows
compose-manager.bat build
```

3. Restart the services:

```
# Linux/macOS
./compose-manager.sh restart

# Windows
compose-manager.bat restart
```

## Troubleshooting

If services aren't healthy, check:

1. Logs for specific errors:
```bash
docker-compose logs python-orch
docker-compose logs go-scanner
```

2. Ensure IB TWS/Gateway is running (if attempting to connect)

3. Confirm port availability (8000, 2112, 50051, 9090, 6379)

4. Check if the configuration files are valid

5. Verify Docker and Docker Compose are installed correctly:
```bash
docker --version
docker-compose --version
``` 