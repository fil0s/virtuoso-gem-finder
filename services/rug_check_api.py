import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict

# Assuming LoggerSetup is in the same services directory or accessible via Python path
from .logger_setup import LoggerSetup

class RugCheckAPI:
    def __init__(self, api_key: str):
        self.logger = LoggerSetup('RugCheckAPI').logger
        self.base_url = "https://api.rugcheck.xyz/v1"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0",
            "X-API-KEY": api_key
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def check_token(self, token_address: str) -> Dict:
        """Get token security analysis from RugCheck"""
        self._rate_limit_check() # Assuming a rate limit check similar to other APIs if needed, or remove if not.
                                # For now, let's assume one might be added later or RugCheck is less sensitive.
                                # The original solgem.py version didn't have one explicitly here.
                                # Adding a placeholder for consistency with other API classes.
        try:
            response = requests.get(
                f"{self.base_url}/tokens/{token_address}/analysis",
                headers=self.headers,
                timeout=10  # Added timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error checking token security for {token_address} via RugCheck: {e}", exc_info=True)
            return {} # Return empty dict on error
        except Exception as e: # Catch any other unexpected errors
            self.logger.error(f"Unexpected error in RugCheckAPI.check_token for {token_address}: {e}", exc_info=True)
            return {}

    def _rate_limit_check(self): # Placeholder rate limit check, can be fleshed out if needed
        """Placeholder for rate limiting logic if RugCheck.xyz has API limits."""
        # For now, this does nothing. Implement if API limits are hit.
        # self.logger.debug("RugCheckAPI: _rate_limit_check called (currently no-op)")
        pass 