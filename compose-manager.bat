@echo off
:: Helper script for managing the Docker Compose environment on Windows

:: Create required directories if they don't exist
if not exist ".\trader-orchestrator" mkdir ".\trader-orchestrator"
if not exist ".\trader-scanner" mkdir ".\trader-scanner"

:: Generate default config.yaml if it doesn't exist
if not exist ".\trader-orchestrator\config.yaml" (
  echo # Default Python orchestrator configuration > ".\trader-orchestrator\config.yaml"
  echo sma_period: 50 >> ".\trader-orchestrator\config.yaml"
  echo candle_count: 2 >> ".\trader-orchestrator\config.yaml"
  echo iv_threshold: 0.3 >> ".\trader-orchestrator\config.yaml"
  echo reward_risk_ratio: 1.0 >> ".\trader-orchestrator\config.yaml"
  echo strike_offset: 1  # 1 = ATM, 2 = 1 strike OTM >> ".\trader-orchestrator\config.yaml"
)

:: Generate default config.json if it doesn't exist
if not exist ".\trader-scanner\config.json" (
  echo { > ".\trader-scanner\config.json"
  echo   "sma_period": 50, >> ".\trader-scanner\config.json"
  echo   "candle_count": 2, >> ".\trader-scanner\config.json"
  echo   "iv_threshold": 0.3, >> ".\trader-scanner\config.json"
  echo   "symbols": ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA"] >> ".\trader-scanner\config.json"
  echo } >> ".\trader-scanner\config.json"
)

:: Process arguments
if "%1"=="" goto usage
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="health" goto health
if "%1"=="build" goto build
goto usage

:up
echo Starting all services...
docker-compose up -d
timeout /t 5 /nobreak
goto health

:down
echo Stopping all services...
docker-compose down
goto end

:restart
echo Restarting all services...
docker-compose down
docker-compose up -d
timeout /t 5 /nobreak
goto health

:logs
echo Showing logs...
docker-compose logs
goto end

:health
echo Checking service health...
:: Use PowerShell for more sophisticated web requests
powershell -Command "try { $python = (Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing).StatusCode } catch { $python = 'error' }"
powershell -Command "try { $scanner = (Invoke-WebRequest -Uri 'http://localhost:2112/health' -UseBasicParsing).StatusCode } catch { $scanner = 'error' }"

echo Python Orchestrator: %python%
echo Go Scanner: %scanner%

if "%python%"=="200" if "%scanner%"=="200" (
  echo All services are healthy!
) else (
  echo Some services are not healthy. Check logs with 'docker-compose logs'
)
goto end

:build
echo Building images...
docker-compose build --no-cache
goto end

:usage
echo Usage: %0 {up^|down^|restart^|logs^|health^|build}
goto end

:end 