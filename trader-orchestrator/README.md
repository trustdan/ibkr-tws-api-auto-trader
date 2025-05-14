# Trader Orchestrator

A Python-based system for automated trading via Interactive Brokers TWS API.

## Overview

This project implements a trading system using `ib_insync` to connect to Interactive Brokers TWS API. It follows a strategy based on SMA period, candle patterns, and vertical spread options trading.

## Project Structure

```
trader-orchestrator/
├── src/               # application code
│   ├── config/        # config loader & schema
│   ├── ibkr/          # ib‑insync wrapper
│   ├── strategies/    # strategy implementations
│   └── orders/        # execution code
├── tests/             # pytest + pytest‑bdd scenarios
├── config.yaml        # master configuration file
├── pyproject.toml     # Poetry project file
└── README.md          # high‑level documentation
```

## Installation

1. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install project dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Configuration

Edit the `config.yaml` file to adjust trading parameters, connection settings, and strategy rules.

## Testing

Run the test suite:

```bash
pytest
``` 