# 01-python-setup.md

## 1. Overview

This document describes how to initialize the Python orchestrator component of our trading system.  We will set up a clean project structure, install dependencies, and define a central `config.yaml` schema that captures key trading parameters: a 50‑day SMA period, two‑candle pattern rules, ATM vs. OTM strike offsets, implied volatility thresholds, and minimum 1:1 reward‑risk ratio.  By standardizing our config early, every downstream module (market data, strategy engine, order execution) will read from the same source of truth.

We’ll use a modern Python toolchain: `poetry` for dependency and virtual‑env management, `pytest` and `pytest‑bdd` for testing, and `flake8`/`black` for linting and formatting.  The repository layout will be:

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

## 2. Environment & Dependencies

1. **Install Poetry & initialize**:

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   poetry init --name trader-orchestrator --dependency ib_insync --dependency pyyaml --dev-dependency pytest --dev-dependency pytest-bdd --dev-dependency flake8 --dev-dependency black
   ```
2. **Activate the virtual environment**:

   ```bash
   poetry shell
   ```
3. **Install all dependencies**:

   ```bash
   poetry install
   ```

## 3. Configuration Schema (`config.yaml`)

Define all user‑tunable parameters in YAML:

```yaml
ibkr:
  host: "127.0.0.1"
  port: 7497
  client_id: 1
strategy:
  sma_period: 50
  candle_count: 2
  otm_offset: 1     # number of strikes OTM
  iv_threshold: 0.8 # percentile threshold (0–1)
  min_reward_risk: 1.0
```

Implement a loader (`src/config/loader.py`) that validates types and sets defaults where omitted.

## 4. Cucumber Scenario

```gherkin
Feature: Python Environment Setup
  Scenario: Fresh clone and install
    Given I have cloned the repo
    When I run "poetry install"
    Then all dependencies (ib_insync, PyYAML, pytest, pytest-bdd, flake8, black) are installed
  Scenario: Config file exists
    Given the repository root
    When I list files
    Then "config.yaml" should be present
```

## 5. Pseudocode Outline

```python
# src/config/loader.py
import yaml

def load_config(path="config.yaml"):  # Load and validate
    with open(path) as f:
        data = yaml.safe_load(f)
    # Set defaults
    data["strategy"].setdefault("min_reward_risk", 1.0)
    # Type checks omitted
    return data

# Entry point
if __name__ == "__main__":
    cfg = load_config()
    print("Loaded config:", cfg)
```
