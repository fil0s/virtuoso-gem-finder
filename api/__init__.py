"""
API client modules for the Virtuoso Gem Finder
"""

# Import API modules with try/except to handle missing dependencies gracefully
try:
    from api.jupiter_connector import JupiterAPI
except ImportError:
    # If solana dependency is missing, define a placeholder class
    class JupiterAPI:
        """Placeholder for JupiterAPI when dependencies are missing"""
        def __init__(self, *args, **kwargs):
            raise ImportError("JupiterAPI dependencies not installed. Run 'pip install solana solders jupiter-python-sdk'")

# Helius API doesn't have exotic dependencies, should import fine
from api.helius_connector import HeliusAPI

try:
    from api.solana_rpc_enhanced import EnhancedSolanaRPC, SolanaRPC
except ImportError:
    # Define placeholder classes
    class SolanaRPC:
        """Placeholder for SolanaRPC when dependencies are missing"""
        def __init__(self, *args, **kwargs):
            raise ImportError("SolanaRPC dependencies not installed. Run 'pip install solana solders'")
    
    class EnhancedSolanaRPC(SolanaRPC):
        """Placeholder for EnhancedSolanaRPC when dependencies are missing"""
        pass

try:
    from api.pump_fun_scraper import PumpFunScraper
except ImportError:
    # Define a placeholder class
    class PumpFunScraper:
        """Placeholder for PumpFunScraper when dependencies are missing"""
        def __init__(self, *args, **kwargs):
            raise ImportError("PumpFunScraper dependencies not installed.")

__all__ = [
    'JupiterAPI',
    'HeliusAPI',
    'EnhancedSolanaRPC',
    'SolanaRPC',
    'PumpFunScraper'
]
