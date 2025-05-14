# TraderAdmin

A desktop application for automating options trading strategies with Interactive Brokers TWS.

## Features

- Connect to IBKR TWS for real-time trading
- Configure trading strategies with dynamic parameters
- Monitor signals and positions in real-time
- Automated scanning for trading opportunities

## Development

### Prerequisites

- Go 1.21+
- Node.js 18+
- NPM
- Wails CLI (`go install github.com/wailsapp/wails/v2/cmd/wails@latest`)
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

#### Using build scripts

On Windows:
```
.\build.bat
```

On macOS/Linux:
```
chmod +x build.sh
./build.sh
```

#### Manual build steps

1. Build the frontend:
   ```bash
   cd frontend
   npm ci
   npm run build
   cd ..
   ```

2. Build the Wails application:
   ```bash
   wails build
   ```

The built application will be available in the `build/bin` directory.

## Releases

Releases are automatically built using GitHub Actions when tags are pushed:

1. Tag a new version:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. GitHub Actions will build the application for Windows, macOS, and Linux and attach the binaries to the release.

## Testing

Run frontend tests:
```bash
cd frontend
npm test
```

Run backend tests:
```bash
go test ./...
```

## License

[MIT License](LICENSE) 