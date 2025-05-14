"""Tests for configuration loader."""
import os
import tempfile
import pytest
import yaml
from src.config import load_config

def test_load_config_defaults():
    """Test that default values are set correctly."""
    # Create a minimal config file
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
        yaml.dump({}, f)
    
    try:
        # Load the config
        config = load_config(f.name)
        
        # Check IBKR defaults
        assert config['ibkr']['host'] == '127.0.0.1'
        assert config['ibkr']['port'] == 7497
        assert config['ibkr']['client_id'] == 1
        
        # Check strategy defaults
        assert config['strategy']['sma_period'] == 50
        assert config['strategy']['candle_count'] == 2
        assert config['strategy']['otm_offset'] == 1
        assert config['strategy']['iv_threshold'] == 0.8
        assert config['strategy']['min_reward_risk'] == 1.0
    finally:
        # Clean up the temporary file
        os.unlink(f.name)

def test_load_config_custom_values():
    """Test that custom values override defaults."""
    # Create a config with custom values
    custom_config = {
        'ibkr': {
            'host': 'localhost',
            'port': 4001,
            'client_id': 2
        },
        'strategy': {
            'sma_period': 100,
            'candle_count': 3,
            'otm_offset': 2,
            'iv_threshold': 0.5,
            'min_reward_risk': 2.0
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
        yaml.dump(custom_config, f)
    
    try:
        # Load the config
        config = load_config(f.name)
        
        # Check IBKR custom values
        assert config['ibkr']['host'] == 'localhost'
        assert config['ibkr']['port'] == 4001
        assert config['ibkr']['client_id'] == 2
        
        # Check strategy custom values
        assert config['strategy']['sma_period'] == 100
        assert config['strategy']['candle_count'] == 3
        assert config['strategy']['otm_offset'] == 2
        assert config['strategy']['iv_threshold'] == 0.5
        assert config['strategy']['min_reward_risk'] == 2.0
    finally:
        # Clean up the temporary file
        os.unlink(f.name)

def test_invalid_config():
    """Test that invalid configs are rejected."""
    # Create an invalid config
    invalid_config = {
        'strategy': {
            'sma_period': -1,  # Invalid: must be positive
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_config, f)
    
    try:
        # Attempt to load the config, should raise an exception
        with pytest.raises(AssertionError):
            load_config(f.name)
    finally:
        # Clean up the temporary file
        os.unlink(f.name) 