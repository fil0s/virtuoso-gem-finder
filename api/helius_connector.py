"""
Helius API connector for the Solana gem finder application.

This module provides access to Helius Solana API, which offers enhanced 
Solana data, including token holder metrics, transaction history, 
and NFT information.
"""

import logging
import requests
import time
from typing import Dict, List, Optional, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.env_loader import get_helius_api_key

class HeliusAPI:
    """
    A connector for the Helius API for enhanced Solana data.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_key_name: str = "LEGROOT"):
        """
        Initialize the Helius API connector.
        
        Args:
            api_key: Optional explicit API key. If not provided, will be loaded from environment.
            api_key_name: Which named API key to use from environment (LEGROOT or GEMNOON)
        """
        self.logger = logging.getLogger('helius_api')
        
        # Get API key from parameters or from environment
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = get_helius_api_key(api_key_name)
            
        if not self.api_key:
            self.logger.warning("No Helius API key provided. API calls will fail.")
            
        # API endpoints
        self.base_url = "https://api.helius.xyz/v0"
        self.rpc_url = "https://mainnet.helius-rpc.com"
        
        # Standard headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0"
        }
        
        self.logger.info("Helius API connector initialized")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_token_metadata(self, mint_address: str) -> Optional[Dict]:
        """
        Get metadata for a specific token.
        
        Args:
            mint_address: The mint address of the token
            
        Returns:
            Token metadata or None if not found/error
        """
        try:
            url = f"{self.base_url}/tokens?api-key={self.api_key}"
            payload = {"mintAccounts": [mint_address]}
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            return None
        except Exception as e:
            self.logger.error(f"Error fetching token metadata for {mint_address}: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_token_holders(self, mint_address: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Get the current holders of a token.
        
        Args:
            mint_address: The mint address of the token
            limit: Maximum number of holders to return (default 100)
            
        Returns:
            List of token holders or None if error
        """
        try:
            url = f"{self.base_url}/token-accounts?api-key={self.api_key}"
            payload = {
                "mintAccount": mint_address,
                "limit": limit
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching token holders for {mint_address}: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_transaction_history(self, address: str, type: str = "TOKEN", limit: int = 100) -> Optional[List[Dict]]:
        """
        Get transaction history for an address.
        
        Args:
            address: The address to get transactions for
            type: Transaction type filter ("TOKEN", "NFT", "SOL", etc.)
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions or None if error
        """
        try:
            url = f"{self.base_url}/addresses/{address}/transactions?api-key={self.api_key}"
            payload = {
                "type": type,
                "limit": limit
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching transaction history for {address}: {e}")
            return None
    
    def get_current_holder_count(self, token_mint: str) -> Optional[int]:
        """
        Get the current number of holders for a token.
        
        Args:
            token_mint: The mint address of the token
            
        Returns:
            Number of holders or None if not available
        """
        try:
            # First try to get metadata which may include holder count
            metadata = self.get_token_metadata(token_mint)
            if metadata and "offChainData" in metadata and "holderCount" in metadata["offChainData"]:
                return metadata["offChainData"]["holderCount"]
                
            # If not in metadata, make a custom RPC call to count holders
            url = self.rpc_url
            payload = {
                "jsonrpc": "2.0",
                "id": "helius-holder-count",
                "method": "getProgramAccounts",
                "params": [
                    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                    {
                        "encoding": "jsonParsed",
                        "filters": [
                            {
                                "dataSize": 165  # Size of token account data
                            },
                            {
                                "memcmp": {
                                    "offset": 0,  # Offset for mint address
                                    "bytes": token_mint
                                }
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            result = response.json().get("result", [])
            # Filter to only include accounts with non-zero balance
            active_accounts = [
                account for account in result 
                if int(account.get("account", {}).get("data", {}).get("parsed", {})
                      .get("info", {}).get("tokenAmount", {}).get("amount", "0")) > 0
            ]
            
            return len(active_accounts)
            
        except Exception as e:
            self.logger.error(f"Error getting holder count for {token_mint}: {e}")
            return None
    
    def get_historical_holder_counts(self, token_mint: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical holder counts for a token over time.
        PLACEHOLDER: Actual implementation would need additional API support or data analysis.
        
        Args:
            token_mint: The mint address of the token
            days: Number of days to retrieve historical data for
            
        Returns:
            List of historical holder counts by date or None if not available
        """
        self.logger.warning(
            f"get_historical_holder_counts for {token_mint} is a placeholder and not fully implemented."
        )
        
        # For now, just return the current holder count
        current_count = self.get_current_holder_count(token_mint)
        if current_count is None:
            return None
            
        # Mock historical data with slight decrease in past days
        now = int(time.time())
        day_seconds = 86400  # seconds in a day
        
        result = []
        for day in range(days):
            timestamp = now - (day * day_seconds)
            # Gradually decrease the count for past days (10% variance max)
            day_count = max(1, int(current_count * (1 - (day * 0.01))))
            result.append({
                "timestamp": timestamp,
                "holderCount": day_count
            })
            
        return sorted(result, key=lambda x: x["timestamp"])
    
    def get_transaction_count_for_token(self, token_mint: str, days: int = 1) -> Optional[int]:
        """
        Get the number of transactions involving a specific token.
        
        Args:
            token_mint: The mint address of the token
            days: Number of days to look back
            
        Returns:
            Number of transactions or None if not available
        """
        try:
            url = f"{self.base_url}/token-metrics?api-key={self.api_key}"
            payload = {
                "mintAccounts": [token_mint],
                "granularity": "ONE_DAY",
                "startTime": int(time.time() - (days * 86400)),
                "endTime": int(time.time())
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if not data or not data.get(token_mint, {}).get("tokenTransfers"):
                return 0
                
            # Sum all token transfers over the period
            transfers = data[token_mint]["tokenTransfers"]
            return sum(transfer.get("count", 0) for transfer in transfers)
            
        except Exception as e:
            self.logger.error(f"Error getting transaction count for {token_mint}: {e}")
            return None
            
    def get_wallet_type(self, address: str) -> Optional[str]:
        """
        Determine the type of wallet based on its activity.
        
        Args:
            address: The wallet address to analyze
            
        Returns:
            Wallet type classification or None if couldn't determine
        """
        try:
            # Get transaction history for this wallet
            tx_history = self.get_transaction_history(address, limit=50)
            
            if not tx_history or len(tx_history) == 0:
                return "inactive"
                
            # Analyze transaction patterns to categorize wallet
            # This is a simplified placeholder - real implementation would be more sophisticated
            
            # Check if it's a high-volume trader
            if len(tx_history) >= 40:  # lots of transactions
                return "trader"
                
            # Check if it's a long-term holder
            # Look for early transactions with few recent ones
            sorted_txs = sorted(tx_history, key=lambda x: x.get("timestamp", 0))
            if sorted_txs and (time.time() - sorted_txs[-1].get("timestamp", 0)) > (30 * 86400):
                return "holder"  # No transactions in last 30 days
                
            # Default to regular user
            return "user"
            
        except Exception as e:
            self.logger.error(f"Error determining wallet type for {address}: {e}")
            return None 