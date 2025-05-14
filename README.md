# TraderAdmin

A desktop application for automating options trading strategies with Interactive Brokers TWS.

## Features

- Connect to IBKR TWS for real-time trading
- Configure trading strategies with dynamic parameters
- Monitor signals and positions in real-time
- Automated scanning for trading opportunities

## Components

TraderAdmin consists of several integrated components:

1. **Desktop GUI** - Cross-platform Wails application for configuration and monitoring
2. **Python Orchestrator** - Connects to IBKR TWS and executes trading strategies
3. **Go Scanner** - High-performance market data scanner that identifies opportunities

## Development

### Prerequisites

- Go 1.21+
- Node.js 18+
- NPM
- Wails CLI (`go install github.com/wailsapp/wails/v2/cmd/wails@latest`)
- Docker and Docker Compose
- Python 3.10+
- Interactive Brokers TWS or IB Gateway

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trader-admin.git
   cd trader-admin
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. Start development server:
   ```bash
   wails dev
   ```

### Building

#### Desktop Application

On Windows:
```
.\build.bat
```

On macOS/Linux:
```
chmod +x build.sh
./build.sh
```

#### Docker Images

To build Docker images locally:

```bash
# Build Python Orchestrator
cd python
docker build -t traderadmin/python-orchestrator:latest .
cd ..

# Build Go Scanner
cd go
docker build -t traderadmin/go-scanner:latest .
cd ..
```

## Deployments

### Desktop App

Desktop builds are automatically created when you tag a release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will build the application for Windows, macOS, and Linux and attach the binaries to the release.

### Docker Images

Docker images are automatically built and pushed to Docker Hub when code is pushed to the main branch or tagged with a version:

```bash
# Latest images
docker pull yourusername/python-orchestrator:latest
docker pull yourusername/go-scanner:latest

# Version-specific images
docker pull yourusername/python-orchestrator:v0.1.0
docker pull yourusername/go-scanner:v0.1.0
```

### Kubernetes

The application can be deployed to Kubernetes clusters:

```bash
# For development environment
kubectl apply -f k8s/dev/

# For production environment
kubectl apply -f k8s/prod/
```

Automated deployments are handled by GitHub Actions when new Docker images are built.

## Testing

Run frontend tests:
```bash
cd frontend
npm test
```

Run Python tests:
```bash
cd python
pytest
```

Run Go tests:
```bash
cd go
go test ./...
```

## CI/CD

For details on CI/CD setup, see [CI/CD Setup Guide](docs/CI_CD_Setup.md).

## License

[MIT License](LICENSE) 