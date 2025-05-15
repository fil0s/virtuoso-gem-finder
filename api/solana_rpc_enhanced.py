import requests
import logging
from typing import Dict, List, Optional
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class EnhancedSolanaRPC:
    """
    Enhanced Solana RPC functions that can be integrated into the existing SolanaRPC class.
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.logger = logging.getLogger('EnhancedSolanaRPC')
        self.rpc_url = rpc_url
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "VirtuosoGemFinder/1.0"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, method: str, params: List = None) -> Dict:
        """Make RPC request with retry logic"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        try:
            response = requests.post(self.rpc_url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"RPC request failed: {e}")
            raise

    def get_multiple_accounts(self, addresses: List[str]) -> Dict[str, Dict]:
        """
        Get information for multiple accounts in a single request.
        More efficient than individual calls.
        
        Args:
            addresses: List of account addresses to fetch
            
        Returns:
            Dictionary mapping addresses to their account info
        """
        try:
            # Split into chunks of 100 to avoid RPC limitations
            results = {}
            for i in range(0, len(addresses), 100):
                chunk = addresses[i:i+100]
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getMultipleAccounts",
                    "params": [
                        chunk,
                        {"encoding": "jsonParsed", "commitment": "confirmed"}
                    ]
                }
                
                response = requests.post(self.rpc_url, json=payload, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "result" in data and "value" in data["result"]:
                    for idx, account in enumerate(data["result"]["value"]):
                        if account:
                            results[chunk[idx]] = account
                
            return results
        except Exception as e:
            self.logger.error(f"Failed to get multiple accounts: {e}")
            return {}

    def get_program_accounts(self, program_id: str, filters: List[Dict] = None) -> List[Dict]:
        """
        Get all accounts owned by a program, with optional filters.
        Useful for finding all pools or tokens created by a program.
        
        Args:
            program_id: The program ID to query accounts for
            filters: Optional filters to apply
            
        Returns:
            List of matching accounts
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getProgramAccounts",
                "params": [
                    program_id,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed"
                    }
                ]
            }
            
            # Add filters if provided
            if filters:
                payload["params"][1]["filters"] = filters
                
            response = requests.post(self.rpc_url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                return data["result"]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get program accounts: {e}")
            return []

    def get_transaction(self, signature: str) -> Optional[Dict]:
        """
        Get detailed transaction data for a signature.
        
        Args:
            signature: Transaction signature
            
        Returns:
            Transaction data or None if not found
        """
        try:
            result = self._make_request(
                "getTransaction", 
                [signature, {"encoding": "jsonParsed", "commitment": "confirmed"}]
            )
            return result.get("result")
        except Exception as e:
            self.logger.error(f"Failed to get transaction: {e}")
            return None

    def get_recent_token_transactions(self, token_address: str, limit: int = 10) -> List[Dict]:
        """
        Get recent transactions for a specific token.
        
        Args:
            token_address: Token mint address
            limit: Maximum number of transactions to return
            
        Returns:
            List of recent transactions involving this token
        """
        try:
            # First find token's largest accounts (for efficiency)
            largest_accounts = self.get_token_largest_accounts(token_address)
            if not largest_accounts:
                return []
                
            # Get transactions for the largest accounts
            all_txs = []
            for account in largest_accounts[:3]:  # Check top 3 accounts
                account_address = account.get("address")
                if not account_address:
                    continue
                    
                signatures = self.get_signature_history(account_address, limit=limit)
                for sig_info in signatures:
                    sig = sig_info.get("signature")
                    if sig:
                        tx_data = self.get_transaction(sig)
                        if tx_data:
                            all_txs.append(tx_data)
                            
            # Sort by recent first and limit
            sorted_txs = sorted(all_txs, 
                                key=lambda x: x.get("blockTime", 0), 
                                reverse=True)
            return sorted_txs[:limit]
        except Exception as e:
            self.logger.error(f"Failed to get token transactions: {e}")
            return []
            
    def get_token_largest_accounts(self, token_address: str) -> List[Dict]:
        """
        Get the largest accounts holding a specific token.
        Useful for tracking whales and distribution.
        
        Args:
            token_address: Token mint address
            
        Returns:
            List of largest accounts holding this token
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenLargestAccounts",
                "params": [token_address]
            }
            
            response = requests.post(self.rpc_url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "result" in data and "value" in data["result"]:
                return data["result"]["value"]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get token largest accounts: {e}")
            return []
            
    def get_signature_history(self, address: str, limit: int = 10) -> List[Dict]:
        """Get transaction signature history for an address"""
        try:
            result = self._make_request(
                "getSignaturesForAddress",
                [address, {"limit": limit}]
            )
            return result.get('result', [])
        except Exception as e:
            self.logger.error(f"Failed to get signature history: {e}")
            return [] 