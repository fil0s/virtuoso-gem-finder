import requests
import time
import threading
from typing import List, Dict, Optional, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential

# Assuming LoggerSetup is in the same directory or accessible via Python path
from .logger_setup import LoggerSetup
# from typing import List, Dict, Optional # Already imported List, Dict, Optional in solgem.py

class DexScreenerAPI:
    def __init__(self):
        self.logger = LoggerSetup('DexScreenerAPI').logger # LoggerSetup will be imported
        self.base_url = "https://api.dexscreener.com/latest/dex"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0"
        }
        self.request_timestamps = []
        self.rate_limit = 300  # requests per minute
        self.rate_window = 60  # seconds
        self.tokens = float(self.rate_limit) # Ensure tokens is float for calculations
        self.last_update = time.time()
        self.lock = threading.Lock()

    def _rate_limit_check(self):
        """Rate limiting with debug logging"""
        with self.lock:
            current_time = time.time()
            time_passed = current_time - self.last_update
            self.tokens = min(
                float(self.rate_limit),
                self.tokens + time_passed * (float(self.rate_limit) / self.rate_window)
            )
            self.last_update = current_time # Update last_update regardless of sleep
            
            if self.tokens < 1.0:
                sleep_time = (1.0 - self.tokens) * (self.rate_window / float(self.rate_limit))
                # Ensure sleep_time is not negative due to precision issues
                sleep_time = max(0, sleep_time) 
                self.logger.debug(
                    f"Rate limit reached. Sleeping for {sleep_time:.2f}s. "
                    f"Available tokens: {self.tokens:.2f}"
                )
                time.sleep(sleep_time)
                # After sleeping, recalculate tokens based on sleep duration
                # This ensures more accurate token count after wait
                current_time_after_sleep = time.time()
                time_passed_during_sleep = current_time_after_sleep - current_time
                self.tokens += time_passed_during_sleep * (float(self.rate_limit) / self.rate_window)
                self.tokens = min(float(self.rate_limit), self.tokens) # Cap at max
                self.last_update = current_time_after_sleep
            
            if self.tokens >= 1.0: # Check again if tokens are sufficient
                self.tokens -= 1.0
            else:
                # This case should ideally not be hit if logic is correct, but as a fallback:
                self.logger.warning("Still rate-limited after sleep, something might be off or extreme load.")
                # Force a small wait and decrement, hoping for recovery
                time.sleep(0.1)
                self.tokens = 0 # Penalize slightly

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        # Ensure retry_error_callback returns a value that matches expected return type (List[Dict])
        retry_error_callback=lambda retry_state: [] 
    )
    def get_solana_pairs(self) -> List[Dict[str, Any]]:
        """Fetch Solana pairs with retry logic"""
        self._rate_limit_check()
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": "solana"}, # Only Solana pairs
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('pairs', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching Solana pairs: {e}", exc_info=True)
            raise  # Let retry handle it

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: None
    )
    def get_pair_details(self, pair_address: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific pair"""
        self._rate_limit_check()
        try:
            response = requests.get(
                f"{self.base_url}/pairs/solana/{pair_address}",
                headers=self.headers,
                timeout=10 # Added timeout
            )
            response.raise_for_status() # Check for HTTP errors
            pairs = response.json().get('pairs', [])
            return pairs[0] if pairs else None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching pair details for {pair_address}: {e}", exc_info=True)
            raise # Let retry handle it
        except (KeyError, IndexError) as e:
            self.logger.error(f"Unexpected response structure for pair {pair_address}: {e}", exc_info=True)
            return None # Return None if data structure is not as expected

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: []
    )
    def get_token_info(self, token_addresses: List[str]) -> List[Dict[str, Any]]:
        """Get information about specific tokens"""
        if not token_addresses: # Handle empty list case
            return []
        self._rate_limit_check()
        addresses = ','.join(token_addresses[:30])  # API limit of 30 addresses
        try:
            response = requests.get(
                f"{self.base_url}/tokens/{addresses}",
                headers=self.headers,
                timeout=10 # Added timeout
            )
            response.raise_for_status()
            return response.json().get('pairs', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching token info for {addresses}: {e}", exc_info=True)
            raise # Let retry handle it
