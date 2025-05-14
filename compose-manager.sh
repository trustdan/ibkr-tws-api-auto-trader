#!/bin/bash
# Helper script for managing the Docker Compose environment

set -e

# Create required directories if they don't exist
mkdir -p ./trader-orchestrator
mkdir -p ./trader-scanner

# Generate default config.yaml if it doesn't exist
if [ ! -f "./trader-orchestrator/config.yaml" ]; then
  cat > ./trader-orchestrator/config.yaml <<EOL
# Default Python orchestrator configuration
sma_period: 50
candle_count: 2
iv_threshold: 0.3
reward_risk_ratio: 1.0
strike_offset: 1  # 1 = ATM, 2 = 1 strike OTM
EOL
fi

# Generate default config.json if it doesn't exist
if [ ! -f "./trader-scanner/config.json" ]; then
  cat > ./trader-scanner/config.json <<EOL
{
  "sma_period": 50,
  "candle_count": 2,
  "iv_threshold": 0.3,
  "symbols": ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA"]
}
EOL
fi

# Function to check service health
check_health() {
  echo "Checking service health..."
  python_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "error")
  scanner_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:2112/health || echo "error")
  
  echo "Python Orchestrator: $python_health"
  echo "Go Scanner: $scanner_health"
  
  if [ "$python_health" == "200" ] && [ "$scanner_health" == "200" ]; then
    echo "All services are healthy!"
    return 0
  else
    echo "Some services are not healthy. Check logs with 'docker-compose logs'"
    return 1
  fi
}

case "$1" in
  up)
    echo "Starting all services..."
    docker-compose up -d
    sleep 5
    check_health
    ;;
  down)
    echo "Stopping all services..."
    docker-compose down
    ;;
  restart)
    echo "Restarting all services..."
    docker-compose down
    docker-compose up -d
    sleep 5
    check_health
    ;;
  logs)
    echo "Showing logs..."
    docker-compose logs -f
    ;;
  health)
    check_health
    ;;
  build)
    echo "Building images..."
    docker-compose build --no-cache
    ;;
  *)
    echo "Usage: $0 {up|down|restart|logs|health|build}"
    exit 1
    ;;
esac

exit 0 