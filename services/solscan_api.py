import requests
import time
import threading # For self.lock
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Optional # For type hints

from .logger_setup import LoggerSetup

class SolscanAPI:
    def __init__(self, config: Dict): # Added config initialization
        self.logger = LoggerSetup('SolscanAPI').logger
        self.base_url = "https://api.solscan.io"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0"
        }
        self.config = config # Store config for whale_threshold
        self.rate_limit = 60  # Adjust based on Solscan's rate limits
        self.rate_window = 60
        self.tokens = float(self.rate_limit) # Ensure tokens is float
        self.last_update = time.time()
        self.lock = threading.Lock()

    def _rate_limit_check(self): # Copied and adapted from DexScreenerAPI for consistency
        """Rate limiting with debug logging"""
        with self.lock:
            current_time = time.time()
            time_passed = current_time - self.last_update
            self.tokens = min(
                float(self.rate_limit),
                self.tokens + time_passed * (float(self.rate_limit) / self.rate_window)
            )
            self.last_update = current_time
            
            if self.tokens < 1.0:
                sleep_time = (1.0 - self.tokens) * (self.rate_window / float(self.rate_limit))
                sleep_time = max(0, sleep_time)
                self.logger.debug(
                    f"Rate limit reached. Sleeping for {sleep_time:.2f}s. "
                    f"Available tokens: {self.tokens:.2f}"
                )
                time.sleep(sleep_time)
                current_time_after_sleep = time.time()
                time_passed_during_sleep = current_time_after_sleep - current_time
                self.tokens += time_passed_during_sleep * (float(self.rate_limit) / self.rate_window)
                self.tokens = min(float(self.rate_limit), self.tokens)
                self.last_update = current_time_after_sleep
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
            else:
                self.logger.warning("Still rate-limited after sleep in SolscanAPI, something might be off or extreme load.")
                time.sleep(0.1)
                self.tokens = 0

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_token_holders(self, token_address: str) -> int:
        """Get accurate holder count from Solscan"""
        self._rate_limit_check()
        try:
            response = requests.get(
                f"{self.base_url}/token/holders",
                params={"tokenAddress": token_address}, # Changed param name based on typical Solscan API
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and 'data' in data and 'total' in data['data']:
                 return data['data']['total']
            elif isinstance(data, dict) and 'total' in data: 
                 return data['total']
            self.logger.warning(f"Unexpected response structure for get_token_holders {token_address}: {data}")
            return 0
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching holder count for {token_address}: {e}", exc_info=True)
            return 0 
        except Exception as e:
            self.logger.error(f"Unexpected error in get_token_holders for {token_address}: {e}", exc_info=True)
            return 0

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_whale_holdings(self, token_address: str) -> Dict[str, float]:
        """Get top holder information from Solscan"""
        self._rate_limit_check()
        try:
            response = requests.get(
                f"{self.base_url}/token/holders", 
                params={"tokenAddress": token_address, "limit": 20, "offset": 0},  # Top 20 holders
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            whale_holdings: Dict[str, float] = {}
            total_supply_from_data = 0
            decimals = 0

            # Try to find total supply and decimals from common Solscan structures
            if isinstance(data, dict):
                if data.get('token', {}).get('tokenSupply'):
                    total_supply_from_data = float(data['token']['tokenSupply'])
                    decimals = int(data.get('token', {}).get('decimals', 0))
                elif data.get('data', {}).get('token',{}).get('tokenSupply'):
                     total_supply_from_data = float(data['data']['token']['tokenSupply'])
                     decimals = int(data.get('data', {}).get('token',{}).get('decimals', 0))
            
            holders_list = data.get('data', {}).get('holders', []) if isinstance(data.get('data'), dict) else data.get('holders', [])

            if total_supply_from_data > 0 and holders_list:
                # If decimals were not found with total supply, try to get from first holder (assuming homogeneity)
                if decimals == 0 and holders_list and 'decimals' in holders_list[0]:
                    decimals = int(holders_list[0].get('decimals', 0))
                    if decimals > 0:
                        self.logger.debug(f"Using decimals {decimals} from first holder for {token_address}")

                # Convert total_supply_from_data from basic units to actual units
                actual_total_supply = total_supply_from_data / (10**decimals) if decimals > 0 else total_supply_from_data
                if actual_total_supply <=0: # Prevent division by zero
                    self.logger.warning(f"Actual total supply for {token_address} is zero or negative after decimal adjustment. Cannot calculate percentages.")
                    return {}

                for holder_info in holders_list:
                    amount_in_basic_units = float(holder_info.get('amount', 0))
                    # Use token-specific decimals if available, else assume it's already adjusted or use global if any
                    holder_decimals = int(holder_info.get('decimals', decimals)) # Prefer holder-specific, then token-global
                    actual_amount = amount_in_basic_units / (10**holder_decimals) if holder_decimals > 0 else amount_in_basic_units
                    
                    percentage = actual_amount / actual_total_supply
                    whale_threshold = self.config.get('whale_threshold', 0.05) 
                    if percentage >= whale_threshold:
                        whale_holdings[holder_info['address']] = percentage 
            elif holders_list:
                self.logger.warning(f"Could not determine total supply for {token_address} from /token/holders response to calculate whale percentages.")
            
            return whale_holdings
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching whale holdings for {token_address}: {e}", exc_info=True)
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error in get_whale_holdings for {token_address}: {e}", exc_info=True)
            return {} 