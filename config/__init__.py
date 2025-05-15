"""
Configuration module for the Virtuoso Gem Finder
"""

import os
import yaml
from pathlib import Path

def load_config(config_path=None):
    """
    Load the configuration from the config.yaml file
    
    Args:
        config_path: Optional path to the config file. If None, uses the default 
                     location in the config directory.
    
    Returns:
        The loaded configuration as a dictionary
    """
    if config_path is None:
        # Get the directory where this file is located
        config_dir = Path(__file__).parent
        config_path = config_dir / "config.yaml"
    
    # Ensure the config path exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    # Load the configuration
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    return config

__all__ = ['load_config']
