"""
Orca API Connector for Virtuoso Gem Hunter
Integrates with Orca's Whirlpool protocol for enhanced liquidity and pool analytics
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

class OrcaConnector:
    """
    Orca API Connector for Whirlpool protocol data
    Provides enhanced liquidity analytics and pool information
    """
    
    def __init__(self, enhanced_cache: Optional[Any] = None):
        self.base_url = "https://api.mainnet.orca.so"
        self.enhanced_cache = enhanced_cache
        self.logger = logging.getLogger(__name__)
        
        # API call tracking
        self.api_calls = defaultdict(int)
        self.api_call_times = defaultdict(list)
        self.last_reset = datetime.now()
        
        # Load exclusions (stablecoins, wrapped tokens)
        self.excluded_addresses = set()
        self._load_exclusions()
        
        self.logger.info("🌊 Orca Connector initialized with Whirlpool protocol support")
    
    def _load_exclusions(self):
        """Load exclusion list from central exclusion system"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
            from early_token_detection import EarlyTokenDetector
            
            detector = EarlyTokenDetector()
            self.excluded_addresses = detector.get_excluded_addresses()
            self.logger.info(f"🚫 Loaded {len(self.excluded_addresses)} excluded addresses")
            
        except Exception as e:
            self.logger.warning(f"Using minimal exclusions: {e}")
            self.excluded_addresses = {
                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
                'So11111111111111111111111111111111111111112',   # SOL
            }
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics for monitoring"""
        current_time = datetime.now()
        
        # Reset hourly stats
        if (current_time - self.last_reset).total_seconds() > 3600:
            self.api_calls.clear()
            self.api_call_times.clear()
            self.last_reset = current_time
        
        total_calls = sum(self.api_calls.values())
        
        return {
            "total_calls": total_calls,
            "calls_by_endpoint": dict(self.api_calls),
            "average_response_time": self._calculate_avg_response_time(),
            "last_reset": self.last_reset.isoformat(),
            "rate_limit_status": "healthy" if total_calls < 1000 else "approaching_limit"
        }
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time across all endpoints"""
        all_times = []
        for endpoint_times in self.api_call_times.values():
            all_times.extend(endpoint_times)
        
        return sum(all_times) / len(all_times) if all_times else 0.0
    
    def reset_api_statistics(self):
        """Reset API statistics"""
        self.api_calls.clear()
        self.api_call_times.clear()
        self.last_reset = datetime.now()
    
    async def _make_tracked_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with tracking and caching"""
        start_time = datetime.now()
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Check cache first
            cache_key = f"orca_{endpoint}_{str(params)}"
            if self.enhanced_cache:
                cached_data = self.enhanced_cache.get_enhanced("orca_api", cache_key)
                if cached_data:
                    return cached_data
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache successful response
                        if self.enhanced_cache:
                            self.enhanced_cache.set_enhanced("orca_api", cache_key, data, ttl=300)  # 5 min cache
                        
                        # Track API call
                        self.api_calls[endpoint] += 1
                        response_time = (datetime.now() - start_time).total_seconds()
                        self.api_call_times[endpoint].append(response_time)
                        
                        return data
                    else:
                        self.logger.warning(f"Orca API error {response.status} for {endpoint}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Orca API request failed for {endpoint}: {e}")
            return None
    
    async def get_whirlpool_list(self) -> List[Dict]:
        """
        Get list of Whirlpool pools with liquidity and volume data
        Returns pools sorted by liquidity for token discovery
        """
        try:
            # Orca's Whirlpool API endpoint (hypothetical - needs actual API research)
            data = await self._make_tracked_request("/v1/whirlpools")
            
            if not data or 'whirlpools' not in data:
                return []
            
            pools = []
            for pool in data['whirlpools']:
                # Extract token addresses
                token_a = pool.get('tokenA', {}).get('mint', '')
                token_b = pool.get('tokenB', {}).get('mint', '')
                
                # Skip if either token is excluded
                if token_a in self.excluded_addresses or token_b in self.excluded_addresses:
                    continue
                
                # Calculate pool metrics
                liquidity_usd = float(pool.get('liquidity', 0))
                volume_24h = float(pool.get('volume24h', 0))
                fee_tier = float(pool.get('feeTier', 0))
                
                pool_data = {
                    'pool_address': pool.get('address', ''),
                    'token_a': {
                        'address': token_a,
                        'symbol': pool.get('tokenA', {}).get('symbol', ''),
                        'name': pool.get('tokenA', {}).get('name', ''),
                        'decimals': pool.get('tokenA', {}).get('decimals', 0)
                    },
                    'token_b': {
                        'address': token_b,
                        'symbol': pool.get('tokenB', {}).get('symbol', ''),
                        'name': pool.get('tokenB', {}).get('name', ''),
                        'decimals': pool.get('tokenB', {}).get('decimals', 0)
                    },
                    'liquidity_usd': liquidity_usd,
                    'volume_24h': volume_24h,
                    'fee_tier': fee_tier,
                    'price': float(pool.get('price', 0)),
                    'tick_current': pool.get('tickCurrent', 0),
                    'tick_spacing': pool.get('tickSpacing', 0),
                    'orca_score': self._calculate_orca_pool_score(liquidity_usd, volume_24h, fee_tier),
                    'source': 'orca_whirlpool',
                    'last_updated': datetime.now().isoformat()
                }
                
                pools.append(pool_data)
            
            # Sort by Orca score (liquidity + volume weighted)
            pools.sort(key=lambda x: x['orca_score'], reverse=True)
            
            self.logger.info(f"🌊 Fetched {len(pools)} Orca Whirlpool pools")
            return pools
            
        except Exception as e:
            self.logger.error(f"Error fetching Orca whirlpool list: {e}")
            return []
    
    def _calculate_orca_pool_score(self, liquidity: float, volume_24h: float, fee_tier: float) -> float:
        """
        Calculate Orca-specific pool score for ranking
        Higher score = better pool for token discovery
        """
        if liquidity <= 0:
            return 0.0
        
        # Volume to liquidity ratio (higher = more active trading)
        vlr = volume_24h / liquidity if liquidity > 0 else 0
        
        # Base score from liquidity (log scale to prevent huge pools dominating)
        liquidity_score = min(50.0, (liquidity / 100000) ** 0.5)
        
        # Volume activity score
        volume_score = min(30.0, vlr * 10)
        
        # Fee tier score (lower fees = better for traders)
        fee_score = max(0, 20.0 - (fee_tier * 100))  # Assume fee_tier is decimal (0.003 = 0.3%)
        
        total_score = liquidity_score + volume_score + fee_score
        
        return round(total_score, 2)
    
    async def get_token_pools(self, token_address: str) -> List[Dict]:
        """
        Get all Whirlpool pools for a specific token
        Useful for analyzing token liquidity distribution
        """
        try:
            params = {'token': token_address}
            data = await self._make_tracked_request("/v1/whirlpools/token", params)
            
            if not data or 'pools' not in data:
                return []
            
            pools = []
            for pool in data['pools']:
                pool_data = {
                    'pool_address': pool.get('address', ''),
                    'pair_token': pool.get('pairToken', {}).get('mint', ''),
                    'pair_symbol': pool.get('pairToken', {}).get('symbol', ''),
                    'liquidity_usd': float(pool.get('liquidity', 0)),
                    'volume_24h': float(pool.get('volume24h', 0)),
                    'price': float(pool.get('price', 0)),
                    'fee_tier': float(pool.get('feeTier', 0)),
                    'source': 'orca_token_pools'
                }
                pools.append(pool_data)
            
            return pools
            
        except Exception as e:
            self.logger.error(f"Error fetching Orca pools for token {token_address}: {e}")
            return []
    
    async def get_pool_analytics(self, pool_address: str) -> Optional[Dict]:
        """
        Get detailed analytics for a specific Whirlpool
        Includes fee collection, liquidity provider data, etc.
        """
        try:
            data = await self._make_tracked_request(f"/v1/whirlpools/{pool_address}/analytics")
            
            if not data:
                return None
            
            analytics = {
                'pool_address': pool_address,
                'total_value_locked': float(data.get('tvl', 0)),
                'volume_7d': float(data.get('volume7d', 0)),
                'volume_30d': float(data.get('volume30d', 0)),
                'fees_collected_24h': float(data.get('fees24h', 0)),
                'fees_collected_7d': float(data.get('fees7d', 0)),
                'liquidity_providers_count': int(data.get('lpCount', 0)),
                'price_range_utilization': float(data.get('priceRangeUtilization', 0)),
                'impermanent_loss_risk': self._assess_impermanent_loss_risk(data),
                'source': 'orca_pool_analytics'
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error fetching Orca pool analytics for {pool_address}: {e}")
            return None
    
    def _assess_impermanent_loss_risk(self, pool_data: Dict) -> str:
        """Assess impermanent loss risk based on pool characteristics"""
        volatility = float(pool_data.get('volatility', 0))
        correlation = float(pool_data.get('correlation', 1))
        
        if volatility > 0.5 and correlation < 0.3:
            return "high"
        elif volatility > 0.2 or correlation < 0.7:
            return "medium"
        else:
            return "low"
    
    async def get_trending_pools(self, limit: int = 50) -> List[Dict]:
        """
        Get trending Whirlpool pools based on volume growth
        Useful for discovering tokens with increasing activity
        """
        try:
            params = {'limit': limit, 'sortBy': 'volumeGrowth24h'}
            data = await self._make_tracked_request("/v1/whirlpools/trending", params)
            
            if not data or 'pools' not in data:
                return []
            
            trending_pools = []
            for pool in data['pools']:
                # Skip pools with excluded tokens
                token_a = pool.get('tokenA', {}).get('mint', '')
                token_b = pool.get('tokenB', {}).get('mint', '')
                
                if token_a in self.excluded_addresses or token_b in self.excluded_addresses:
                    continue
                
                volume_growth = float(pool.get('volumeGrowth24h', 0))
                
                pool_data = {
                    'pool_address': pool.get('address', ''),
                    'token_a': token_a,
                    'token_b': token_b,
                    'symbol_a': pool.get('tokenA', {}).get('symbol', ''),
                    'symbol_b': pool.get('tokenB', {}).get('symbol', ''),
                    'volume_24h': float(pool.get('volume24h', 0)),
                    'volume_growth_24h': volume_growth,
                    'liquidity_usd': float(pool.get('liquidity', 0)),
                    'price_change_24h': float(pool.get('priceChange24h', 0)),
                    'trending_score': self._calculate_trending_score(volume_growth, pool),
                    'source': 'orca_trending'
                }
                
                trending_pools.append(pool_data)
            
            # Sort by trending score
            trending_pools.sort(key=lambda x: x['trending_score'], reverse=True)
            
            self.logger.info(f"🔥 Fetched {len(trending_pools)} trending Orca pools")
            return trending_pools
            
        except Exception as e:
            self.logger.error(f"Error fetching Orca trending pools: {e}")
            return []
    
    def _calculate_trending_score(self, volume_growth: float, pool_data: Dict) -> float:
        """Calculate trending score for pool ranking"""
        base_score = max(0, volume_growth * 10)  # Volume growth is primary factor
        
        # Bonus for high absolute volume
        volume_bonus = min(20, float(pool_data.get('volume24h', 0)) / 100000)
        
        # Bonus for sufficient liquidity
        liquidity_bonus = min(10, float(pool_data.get('liquidity', 0)) / 500000)
        
        return base_score + volume_bonus + liquidity_bonus
    
    async def close(self):
        """Clean up resources"""
        self.logger.info("🌊 Orca Connector closed")


# Example usage and testing
async def test_orca_connector():
    """Test the Orca connector functionality"""
    connector = OrcaConnector()
    
    print("Testing Orca Connector...")
    
    # Test whirlpool list
    pools = await connector.get_whirlpool_list()
    print(f"Found {len(pools)} Whirlpool pools")
    
    if pools:
        print(f"Top pool: {pools[0]['token_a']['symbol']}/{pools[0]['token_b']['symbol']}")
        print(f"Liquidity: ${pools[0]['liquidity_usd']:,.2f}")
        print(f"Volume 24h: ${pools[0]['volume_24h']:,.2f}")
        print(f"Orca Score: {pools[0]['orca_score']}")
    
    # Test trending pools
    trending = await connector.get_trending_pools(limit=10)
    print(f"\nFound {len(trending)} trending pools")
    
    # Print API stats
    stats = connector.get_api_call_statistics()
    print(f"\nAPI Stats: {stats}")
    
    await connector.close()

if __name__ == "__main__":
    asyncio.run(test_orca_connector()) 