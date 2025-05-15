import aiohttp
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class HeliusAPI:
    """
    Connector for Helius API to get enhanced transaction data and token information.
    Uses the free tier which provides 100M credits/month (~3.3M transactions).
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.helius.xyz/v0"
        self.logger = logging.getLogger('HeliusAPI')
        
    async def get_enhanced_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """
        Get detailed transaction history with enriched metadata.
        
        Args:
            address: Solana address to get transactions for
            limit: Number of transactions to return (max 100)
            
        Returns:
            List of enriched transaction data
        """
        try:
            url = f"{self.base_url}/addresses/{address}/transactions"
            params = {
                "api-key": self.api_key,
                "limit": min(limit, 100)  # Ensure we don't exceed max
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        self.logger.error(f"Helius API error: {await response.text()}")
                        return []
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Error fetching Helius transactions: {e}")
            return []
    
    async def get_nft_events(self, token_address: str, days: int = 7) -> List[Dict]:
        """
        Get NFT events related to a token, useful for analyzing NFT collections.
        
        Args:
            token_address: Token mint address
            days: Number of days of historical data to retrieve
            
        Returns:
            List of NFT events
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            url = f"{self.base_url}/nft-events"
            payload = {
                "api-key": self.api_key,
                "query": {
                    "mintA": token_address
                },
                "options": {
                    "limit": 100
                },
                "startDate": start_date
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error(f"Helius NFT API error: {await response.text()}")
                        return []
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Error fetching NFT events: {e}")
            return []
    
    async def get_token_metadata(self, token_addresses: List[str]) -> Dict[str, Any]:
        """
        Get detailed token metadata including name, symbol, and metadata URL.
        
        Args:
            token_addresses: List of token mint addresses
            
        Returns:
            Dictionary mapping token addresses to their metadata
        """
        try:
            url = f"{self.base_url}/token-metadata"
            payload = {
                "api-key": self.api_key,
                "mintAccounts": token_addresses
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error(f"Helius token metadata error: {await response.text()}")
                        return {}
                    data = await response.json()
                    # Format as address -> metadata dictionary
                    return {item.get('mint', ''): item for item in data}
        except Exception as e:
            self.logger.error(f"Error fetching token metadata: {e}")
            return {}
            
    async def get_current_holder_count(self, token_mint: str) -> Optional[int]:
        """
        Get the current holder count for a token.
        PLACEHOLDER: Assumes get_token_metadata might return this or a similar dedicated endpoint exists.
        The actual Helius API response for token-metadata needs to be checked for holder count fields.
        """
        self.logger.warning(
            f"get_current_holder_count for {token_mint} is a placeholder. "
            f"Verify Helius 'token-metadata' endpoint for holder count data or find an alternative."
        )
        # Example: Fetch full metadata and try to extract holder count
        # metadata = await self.get_token_metadata([token_mint])
        # if token_mint in metadata and metadata[token_mint].get("holder_count_field_name"): # Replace with actual field name
        #     return metadata[token_mint]["holder_count_field_name"]
        # Mock response for testing:
        if token_mint == "So11111111111111111111111111111111111111112": # WSOL, for example
             # Simulate some holder count, e.g., based on a hash of the mint to make it vary a bit for tests
            return 1000 + (hash(token_mint) % 100)
        elif len(token_mint) > 10: # Generic mock for other tokens
            return 50 + (hash(token_mint) % 50)
        return None

    async def get_historical_holder_counts(
        self, 
        token_mint: str, 
        timeframes: List[str] # e.g., ["24h", "7d"]
    ) -> Dict[str, Optional[int]]:
        """
        Get historical holder counts for a token at the start of different timeframes.
        PLACEHOLDER: This is a highly simplified placeholder. True historical holder counts
        are hard to get and usually require snapshotting or specialized APIs.
        This placeholder simulates fetching a count for the start of each timeframe.
        """
        self.logger.warning(
            f"get_historical_holder_counts for {token_mint} is a placeholder. "
            f"Actual implementation is complex and may require snapshotting or other services."
        )
        holder_counts_by_timeframe: Dict[str, Optional[int]] = {}

        # Mock implementation: Simulate a decrease from a base mock current holder count
        # A real implementation would need to query historical states or a snapshot DB.
        current_mock_holders = 0
        if token_mint == "So11111111111111111111111111111111111111112":
            current_mock_holders = 1000 + (hash(token_mint) % 100)
        elif len(token_mint) > 10:
            current_mock_holders = 50 + (hash(token_mint) % 50)
        else:
            return {tf: None for tf in timeframes}

        for tf in timeframes:
            # Simulate a slightly lower holder count in the past
            if tf == "1h":
                holder_counts_by_timeframe[tf] = max(0, current_mock_holders - (hash(tf) % 5) -1)
            elif tf == "6h":
                holder_counts_by_timeframe[tf] = max(0, current_mock_holders - (hash(tf) % 10) -2)
            elif tf == "24h":
                holder_counts_by_timeframe[tf] = max(0, current_mock_holders - (hash(tf) % 20) -5)
            elif tf == "7d":
                holder_counts_by_timeframe[tf] = max(0, current_mock_holders - (hash(tf) % 50) -10)
            else:
                holder_counts_by_timeframe[tf] = None # Unknown timeframe
        
        return holder_counts_by_timeframe

    async def get_transaction_count_for_token(self, token_mint: str, lookback_seconds: int) -> Optional[int]:
        """
        Get the number of transactions involving a specific token mint over a lookback period.
        PLACEHOLDER: Helius API for parsed transaction history with account filtering would be needed.
        This is a simplified placeholder.

        Args:
            token_mint: The mint address of the token.
            lookback_seconds: The period to count transactions for (e.g., 3600 for 1 hour).

        Returns:
            The number of transactions, or None if an error occurs.
        """
        self.logger.warning(
            f"get_transaction_count_for_token for {token_mint} is a placeholder. "
            f"Requires querying Helius parsed transaction history with appropriate filters."
        )
        # Mock implementation: Simulate some transaction count
        # A real implementation would query Helius, e.g., /v0/transactions with filters
        # and potentially pagination if the count is high.
        # For example, the query might involve looking for the token_mint in accountKeys involved in transactions.
        
        # Simulate based on lookback and token hash to make it somewhat dynamic for tests
        base_tx_rate_per_hour = 10 + (hash(token_mint[:5]) % 90) # Base rate: 10-100 tx/hr
        simulated_tx_count = int(base_tx_rate_per_hour * (lookback_seconds / 3600.0))
        
        # Add some randomness
        simulated_tx_count += (hash(token_mint[-5:]) % (simulated_tx_count // 10 + 1)) - (simulated_tx_count // 20)
        simulated_tx_count = max(0, simulated_tx_count)

        if token_mint == "So11111111111111111111111111111111111111112": # WSOL often has high velocity
            return simulated_tx_count * 5 # Boost for SOL
        elif len(token_mint) > 10:
            return simulated_tx_count
        return None

    async def analyze_wallet(self, address: str) -> Dict[str, Any]:
        """
        Perform comprehensive wallet analysis to detect bots or smart money.
        
        Args:
            address: Wallet address to analyze
            
        Returns:
            Analysis results with key metrics
        """
        try:
            # Get transaction history
            transactions = await self.get_enhanced_transactions(address, 100)
            
            if not transactions:
                return {"analysis": "insufficient_data"}
                
            # Analyze transaction patterns
            transactions_by_day = {}
            transaction_types = {}
            tokens_interacted = set()
            
            for tx in transactions:
                # Extract date for grouping
                timestamp = tx.get('timestamp', 0) / 1000  # Convert to seconds
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                # Count by day
                if date not in transactions_by_day:
                    transactions_by_day[date] = 0
                transactions_by_day[date] += 1
                
                # Categorize transaction types
                tx_type = tx.get('type', 'UNKNOWN')
                if tx_type not in transaction_types:
                    transaction_types[tx_type] = 0
                transaction_types[tx_type] += 1
                
                # Track tokens interacted with
                for token in tx.get('tokenTransfers', []):
                    mint = token.get('mint')
                    if mint:
                        tokens_interacted.add(mint)
            
            # Calculate metrics
            days_active = len(transactions_by_day)
            avg_tx_per_active_day = sum(transactions_by_day.values()) / max(days_active, 1)
            
            return {
                "address": address,
                "transactions_analyzed": len(transactions),
                "days_active": days_active,
                "avg_tx_per_active_day": avg_tx_per_active_day,
                "transaction_types": transaction_types,
                "unique_tokens_interacted": len(tokens_interacted),
                "is_likely_bot": avg_tx_per_active_day > 50,  # Simple heuristic
                "last_active": max(transactions_by_day.keys()) if transactions_by_day else "unknown"
            }
                
        except Exception as e:
            self.logger.error(f"Error analyzing wallet: {e}")
            return {"error": str(e)} 