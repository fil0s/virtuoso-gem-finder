"""
Environment variable loader for the Virtuoso Gem Finder.
This module provides utilities for loading API keys and configuration from environment variables.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

logger = logging.getLogger(__name__)

def load_environment(env_file: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file: Optional path to the .env file. If None, tries to find
                  .env in the current directory and parent directories.
    
    Returns:
        True if environment variables were loaded successfully, False otherwise.
    """
    if env_file:
        env_path = Path(env_file)
    else:
        # Try to find .env in current directory and parent directories
        current_dir = Path.cwd()
        env_path = current_dir / '.env'
        
        parent_count = 0
        while not env_path.exists() and parent_count < 3:
            # Look up to 3 parent directories
            current_dir = current_dir.parent
            env_path = current_dir / '.env'
            parent_count += 1
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    else:
        logger.warning("No .env file found, using environment variables if available")
        return False

def get_helius_api_key(key_name: str = "LEGROOT") -> Optional[str]:
    """
    Get the Helius API key from environment variables.
    
    Args:
        key_name: The identifier for which API key to use (LEGROOT or GEMNOON)
        
    Returns:
        The API key or None if not found
    """
    env_var_name = f"HELIUS_API_KEY_{key_name.upper()}"
    api_key = os.getenv(env_var_name)
    
    if not api_key:
        logger.warning(f"Helius API key '{key_name}' not found in environment variables")
        return None
        
    return api_key

def get_solana_rpc_endpoint() -> str:
    """
    Get the Solana RPC endpoint from environment variables.
    
    Returns:
        The RPC endpoint URL, or the default public endpoint if not found
    """
    return os.getenv("SOLANA_RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

def get_dexscreener_rate_limit() -> int:
    """
    Get the DexScreener API rate limit from environment variables.
    
    Returns:
        The rate limit as an integer, or the default value of 300
    """
    try:
        return int(os.getenv("DEXSCREENER_RATE_LIMIT", "300"))
    except ValueError:
        logger.warning("Invalid DEXSCREENER_RATE_LIMIT, using default of 300")
        return 300

def get_jupiter_timeout() -> int:
    """
    Get the Jupiter API timeout from environment variables.
    
    Returns:
        The timeout in seconds, or the default value of 10
    """
    try:
        return int(os.getenv("JUPITER_TIMEOUT_SECONDS", "10"))
    except ValueError:
        logger.warning("Invalid JUPITER_TIMEOUT_SECONDS, using default of 10")
        return 10 