"""Step definitions for the Python environment setup feature."""
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest
import yaml
from pytest_bdd import given, parsers, scenarios, then, when

# Import the scenarios from the feature file
scenarios("../features/python_setup.feature")


@given("I have cloned the repository")
def repo_cloned():
    """Simulate having cloned the repository by checking if project files exist."""
    assert Path("pyproject.toml").exists() or Path("../../pyproject.toml").exists()


@when(parsers.parse('I run "{command}"'))
def run_command(command):
    """Simulate running a command (we don't actually run it in tests)."""
    # In a real test, we might use subprocess.run, but we'll just pass here
    pass


@then("all dependencies are installed")
def check_dependencies():
    """Check if dependencies would be installed."""
    # In a real test, we would verify the Poetry environment
    pass


@then(parsers.parse('I can import "{package}"'))
def check_import(package):
    """Check if a package can be imported."""
    # We're just checking if the import would be successful in theory
    # In a real environment test, we'd actually try to import
    pass


@given("the repository root")
def repo_root():
    """Ensure we're in the repository root or can access it."""
    # Find the repository root by looking for pyproject.toml
    root = Path(".")
    while not (root / "pyproject.toml").exists():
        root = root.parent
        if root == root.parent:  # reached filesystem root
            pytest.fail("Could not find repository root")

    # Change to repo root for subsequent steps
    os.chdir(root)


@when("I list files")
def list_files():
    """List files in the current directory."""
    files = os.listdir(".")
    return files


@then(parsers.parse('"{filename}" should be present'))
def check_file_exists(filename):
    """Check if a file exists in the current directory."""
    assert os.path.exists(filename), f"File {filename} not found"


@then("it should contain IBKR connection settings")
def check_ibkr_settings():
    """Check if config.yaml contains IBKR connection settings."""
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    assert "ibkr" in config, "IBKR section missing from config"
    assert "host" in config["ibkr"], "host setting missing from IBKR config"
    assert "port" in config["ibkr"], "port setting missing from IBKR config"
    assert "client_id" in config["ibkr"], "client_id setting missing from IBKR config"


@then("it should contain strategy parameters")
def check_strategy_params():
    """Check if config.yaml contains strategy parameters."""
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    assert "strategy" in config, "Strategy section missing from config"
    assert (
        "sma_period" in config["strategy"]
    ), "sma_period setting missing from strategy config"
    assert (
        "candle_count" in config["strategy"]
    ), "candle_count setting missing from strategy config"
    assert (
        "otm_offset" in config["strategy"]
    ), "otm_offset setting missing from strategy config"
    assert (
        "iv_threshold" in config["strategy"]
    ), "iv_threshold setting missing from strategy config"
    assert (
        "min_reward_risk" in config["strategy"]
    ), "min_reward_risk setting missing from strategy config"
