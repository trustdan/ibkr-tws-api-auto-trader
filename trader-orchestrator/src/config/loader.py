"""
Configuration loader for trader-orchestrator.
Loads YAML config and applies validation and defaults.
"""
import os
import yaml
from typing import Dict, Any

def load_config(path: str = None) -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.
    
    Args:
        path: Path to config file, defaults to config.yaml in project root
        
    Returns:
        Dict containing validated configuration
    """
    if path is None:
        # Default to config.yaml in project root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root_dir, "config.yaml")
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Ensure required sections exist
    if 'ibkr' not in data:
        data['ibkr'] = {}
    if 'strategy' not in data:
        data['strategy'] = {}
    
    # Set defaults for IBKR connection
    data['ibkr'].setdefault('host', '127.0.0.1')
    data['ibkr'].setdefault('port', 7497)
    data['ibkr'].setdefault('client_id', 1)
    
    # Set defaults for strategy parameters
    data['strategy'].setdefault('sma_period', 50)
    data['strategy'].setdefault('candle_count', 2)
    data['strategy'].setdefault('otm_offset', 1)
    data['strategy'].setdefault('iv_threshold', 0.8)
    data['strategy'].setdefault('min_reward_risk', 1.0)
    
    # Basic type validation
    _validate_config(data)
    
    return data

def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate config types and values.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If validation fails
    """
    # IBKR connection validation
    assert isinstance(config['ibkr']['host'], str), "IBKR host must be a string"
    assert isinstance(config['ibkr']['port'], int), "IBKR port must be an integer"
    assert isinstance(config['ibkr']['client_id'], int), "IBKR client_id must be an integer"
    
    # Strategy validation
    assert isinstance(config['strategy']['sma_period'], int), "SMA period must be an integer"
    assert config['strategy']['sma_period'] > 0, "SMA period must be positive"
    
    assert isinstance(config['strategy']['candle_count'], int), "Candle count must be an integer"
    assert config['strategy']['candle_count'] > 0, "Candle count must be positive"
    
    assert isinstance(config['strategy']['otm_offset'], int), "OTM offset must be an integer"
    assert config['strategy']['otm_offset'] >= 0, "OTM offset must be non-negative"
    
    assert isinstance(config['strategy']['iv_threshold'], float), "IV threshold must be a float"
    assert 0 <= config['strategy']['iv_threshold'] <= 1, "IV threshold must be between 0 and 1"
    
    assert isinstance(config['strategy']['min_reward_risk'], float), "Min reward/risk must be a float"
    assert config['strategy']['min_reward_risk'] > 0, "Min reward/risk must be positive"

if __name__ == "__main__":
    # Simple test to load and print config when run directly
    cfg = load_config()
    print("Loaded config:", cfg) 