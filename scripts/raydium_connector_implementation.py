"""
Raydium API Connector for Virtuoso Gem Hunter
Integrates with Raydium's AMM and CLMM protocols for enhanced liquidity and pool analytics
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

class RaydiumConnector:
    """
    Raydium API Connector for AMM and CLMM protocol data
    Provides enhanced liquidity analytics and pool information
    """
    
    def __init__(self, enhanced_cache: Optional[Any] = None):
        self.base_url = "https://api.raydium.io"
        self.enhanced_cache = enhanced_cache
        self.logger = logging.getLogger(__name__)
        
        # API call tracking
        self.api_calls = defaultdict(int)
        self.api_call_times = defaultdict(list)
        self.last_reset = datetime.now()
        
        # Load exclusions (stablecoins, wrapped tokens)
        self.excluded_addresses = set()
        self._load_exclusions()
        
        self.logger.info("⚡ Raydium Connector initialized with AMM and CLMM support")
    
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
                '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',   # RAY
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
            cache_key = f"raydium_{endpoint}_{str(params)}"
            if self.enhanced_cache:
                cached_data = self.enhanced_cache.get_enhanced("raydium_api", cache_key)
                if cached_data:
                    return cached_data
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache successful response
                        if self.enhanced_cache:
                            self.enhanced_cache.set_enhanced("raydium_api", cache_key, data, ttl=300)  # 5 min cache
                        
                        # Track API call
                        self.api_calls[endpoint] += 1
                        response_time = (datetime.now() - start_time).total_seconds()
                        self.api_call_times[endpoint].append(response_time)
                        
                        return data
                    else:
                        self.logger.warning(f"Raydium API error {response.status} for {endpoint}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Raydium API request failed for {endpoint}: {e}")
            return None
    
    async def get_pool_list(self) -> List[Dict]:
        """
        Get list of Raydium AMM and CLMM pools with liquidity and volume data
        Returns pools sorted by liquidity for token discovery
        """
        try:
            # Raydium's pool API endpoint (hypothetical - needs actual API research)
            data = await self._make_tracked_request("/v1/pools")
            
            if not data or 'pools' not in data:
                return []
            
            pools = []
            for pool in data['pools']:
                # Extract token addresses
                token_a = pool.get('baseMint', '')
                token_b = pool.get('quoteMint', '')
                
                # Skip if either token is excluded
                if token_a in self.excluded_addresses or token_b in self.excluded_addresses:
                    continue
                
                # Calculate pool metrics
                liquidity_usd = float(pool.get('liquidity', 0))
                volume_24h = float(pool.get('volume24h', 0))
                fee_rate = float(pool.get('feeRate', 0))
                pool_type = pool.get('poolType', 'AMM')  # AMM or CLMM
                
                pool_data = {
                    'pool_address': pool.get('id', ''),
                    'pool_type': pool_type,
                    'token_a': {
                        'address': token_a,
                        'symbol': pool.get('baseToken', {}).get('symbol', ''),
                        'name': pool.get('baseToken', {}).get('name', ''),
                        'decimals': pool.get('baseToken', {}).get('decimals', 0)
                    },
                    'token_b': {
                        'address': token_b,
                        'symbol': pool.get('quoteToken', {}).get('symbol', ''),
                        'name': pool.get('quoteToken', {}).get('name', ''),
                        'decimals': pool.get('quoteToken', {}).get('decimals', 0)
                    },
                    'liquidity_usd': liquidity_usd,
                    'volume_24h': volume_24h,
                    'fee_rate': fee_rate,
                    'price': float(pool.get('price', 0)),
                    'apr': float(pool.get('apr', 0)),
                    'raydium_score': self._calculate_raydium_pool_score(liquidity_usd, volume_24h, pool_type),
                    'source': 'raydium_pools',
                    'last_updated': datetime.now().isoformat()
                }
                
                pools.append(pool_data)
            
            # Sort by Raydium score (liquidity + volume weighted)
            pools.sort(key=lambda x: x['raydium_score'], reverse=True)
            
            self.logger.info(f"⚡ Fetched {len(pools)} Raydium pools")
            return pools
            
        except Exception as e:
            self.logger.error(f"Error fetching Raydium pool list: {e}")
            return []
    
    def _calculate_raydium_pool_score(self, liquidity: float, volume_24h: float, pool_type: str) -> float:
        """
        Calculate Raydium-specific pool score for ranking
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
        
        # Pool type bonus (CLMM = concentrated liquidity = better efficiency)
        type_bonus = 15.0 if pool_type == 'CLMM' else 5.0
        
        total_score = liquidity_score + volume_score + type_bonus
        
        return round(total_score, 2)
    
    async def get_farms_list(self) -> List[Dict]:
        """
        Get list of Raydium farms for yield farming analysis
        Useful for identifying tokens with high APR opportunities
        """
        try:
            data = await self._make_tracked_request("/v1/farms")
            
            if not data or 'farms' not in data:
                return []
            
            farms = []
            for farm in data['farms']:
                # Skip farms with excluded tokens
                lp_token = farm.get('lpMint', '')
                reward_tokens = [r.get('mint', '') for r in farm.get('rewards', [])]
                
                if any(token in self.excluded_addresses for token in [lp_token] + reward_tokens):
                    continue
                
                farm_data = {
                    'farm_id': farm.get('id', ''),
                    'lp_mint': lp_token,
                    'pool_id': farm.get('poolId', ''),
                    'base_token': farm.get('baseToken', {}).get('symbol', ''),
                    'quote_token': farm.get('quoteToken', {}).get('symbol', ''),
                    'apr': float(farm.get('apr', 0)),
                    'apy': float(farm.get('apy', 0)),
                    'tvl': float(farm.get('tvl', 0)),
                    'rewards': [
                        {
                            'token': reward.get('symbol', ''),
                            'mint': reward.get('mint', ''),
                            'apr': float(reward.get('apr', 0))
                        }
                        for reward in farm.get('rewards', [])
                    ],
                    'farm_score': self._calculate_farm_score(farm),
                    'source': 'raydium_farms'
                }
                
                farms.append(farm_data)
            
            # Sort by farm score (APR + TVL weighted)
            farms.sort(key=lambda x: x['farm_score'], reverse=True)
            
            self.logger.info(f"🚜 Fetched {len(farms)} Raydium farms")
            return farms
            
        except Exception as e:
            self.logger.error(f"Error fetching Raydium farms: {e}")
            return []
    
    def _calculate_farm_score(self, farm_data: Dict) -> float:
        """Calculate farm attractiveness score"""
        apr = float(farm_data.get('apr', 0))
        tvl = float(farm_data.get('tvl', 0))
        
        # APR score (capped to prevent extremely high APR from dominating)
        apr_score = min(50.0, apr * 2)
        
        # TVL score (indicates stability and trust)
        tvl_score = min(30.0, (tvl / 1000000) ** 0.5)
        
        # Bonus for multiple rewards
        reward_bonus = min(20.0, len(farm_data.get('rewards', [])) * 5)
        
        return apr_score + tvl_score + reward_bonus
    
    async def get_token_pools(self, token_address: str) -> List[Dict]:
        """
        Get all Raydium pools for a specific token
        Useful for analyzing token liquidity distribution
        """
        try:
            params = {'token': token_address}
            data = await self._make_tracked_request("/v1/pools/token", params)
            
            if not data or 'pools' not in data:
                return []
            
            pools = []
            for pool in data['pools']:
                pool_data = {
                    'pool_address': pool.get('id', ''),
                    'pool_type': pool.get('poolType', 'AMM'),
                    'pair_token': pool.get('pairToken', {}).get('mint', ''),
                    'pair_symbol': pool.get('pairToken', {}).get('symbol', ''),
                    'liquidity_usd': float(pool.get('liquidity', 0)),
                    'volume_24h': float(pool.get('volume24h', 0)),
                    'price': float(pool.get('price', 0)),
                    'fee_rate': float(pool.get('feeRate', 0)),
                    'apr': float(pool.get('apr', 0)),
                    'source': 'raydium_token_pools'
                }
                pools.append(pool_data)
            
            return pools
            
        except Exception as e:
            self.logger.error(f"Error fetching Raydium pools for token {token_address}: {e}")
            return []
    
    async def get_volume_trending_pools(self, limit: int = 50) -> List[Dict]:
        """
        Get Raydium pools trending by volume growth
        Similar to Meteora but for Raydium ecosystem
        """
        try:
            params = {'limit': limit, 'sortBy': 'volumeGrowth'}
            data = await self._make_tracked_request("/v1/pools/trending", params)
            
            if not data or 'pools' not in data:
                return []
            
            trending_pools = []
            for pool in data['pools']:
                # Skip pools with excluded tokens
                token_a = pool.get('baseMint', '')
                token_b = pool.get('quoteMint', '')
                
                if token_a in self.excluded_addresses or token_b in self.excluded_addresses:
                    continue
                
                volume_growth = float(pool.get('volumeGrowth24h', 0))
                
                pool_data = {
                    'pool_address': pool.get('id', ''),
                    'pool_type': pool.get('poolType', 'AMM'),
                    'token_a': token_a,
                    'token_b': token_b,
                    'symbol_a': pool.get('baseToken', {}).get('symbol', ''),
                    'symbol_b': pool.get('quoteToken', {}).get('symbol', ''),
                    'volume_24h': float(pool.get('volume24h', 0)),
                    'volume_growth_24h': volume_growth,
                    'liquidity_usd': float(pool.get('liquidity', 0)),
                    'price_change_24h': float(pool.get('priceChange24h', 0)),
                    'trending_score': self._calculate_trending_score(volume_growth, pool),
                    'source': 'raydium_trending'
                }
                
                trending_pools.append(pool_data)
            
            # Sort by trending score
            trending_pools.sort(key=lambda x: x['trending_score'], reverse=True)
            
            self.logger.info(f"📈 Fetched {len(trending_pools)} trending Raydium pools")
            return trending_pools
            
        except Exception as e:
            self.logger.error(f"Error fetching Raydium trending pools: {e}")
            return []
    
    def _calculate_trending_score(self, volume_growth: float, pool_data: Dict) -> float:
        """Calculate trending score for pool ranking"""
        base_score = max(0, volume_growth * 10)  # Volume growth is primary factor
        
        # Bonus for high absolute volume
        volume_bonus = min(20, float(pool_data.get('volume24h', 0)) / 100000)
        
        # Bonus for sufficient liquidity
        liquidity_bonus = min(10, float(pool_data.get('liquidity', 0)) / 500000)
        
        # Bonus for CLMM pools (more efficient)
        clmm_bonus = 5.0 if pool_data.get('poolType') == 'CLMM' else 0.0
        
        return base_score + volume_bonus + liquidity_bonus + clmm_bonus
    
    async def get_pool_stats(self, pool_address: str) -> Optional[Dict]:
        """
        Get detailed statistics for a specific Raydium pool
        Includes historical data, fee collection, etc.
        """
        try:
            data = await self._make_tracked_request(f"/v1/pools/{pool_address}/stats")
            
            if not data:
                return None
            
            stats = {
                'pool_address': pool_address,
                'total_value_locked': float(data.get('tvl', 0)),
                'volume_7d': float(data.get('volume7d', 0)),
                'volume_30d': float(data.get('volume30d', 0)),
                'fees_collected_24h': float(data.get('fees24h', 0)),
                'fees_collected_7d': float(data.get('fees7d', 0)),
                'liquidity_providers_count': int(data.get('lpCount', 0)),
                'transactions_24h': int(data.get('transactions24h', 0)),
                'unique_traders_24h': int(data.get('uniqueTraders24h', 0)),
                'pool_health_score': self._calculate_pool_health(data),
                'source': 'raydium_pool_stats'
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error fetching Raydium pool stats for {pool_address}: {e}")
            return None
    
    def _calculate_pool_health(self, pool_data: Dict) -> str:
        """Assess pool health based on various metrics"""
        tvl = float(pool_data.get('tvl', 0))
        volume_24h = float(pool_data.get('volume24h', 0))
        traders = int(pool_data.get('uniqueTraders24h', 0))
        
        # Health criteria
        if tvl > 1000000 and volume_24h > 100000 and traders > 50:
            return "excellent"
        elif tvl > 500000 and volume_24h > 50000 and traders > 20:
            return "good"
        elif tvl > 100000 and volume_24h > 10000 and traders > 5:
            return "fair"
        else:
            return "poor"
    
    async def close(self):
        """Clean up resources"""
        self.logger.info("⚡ Raydium Connector closed")


# Example usage and testing
async def test_raydium_connector():
    """Test the Raydium connector functionality"""
    connector = RaydiumConnector()
    
    print("Testing Raydium Connector...")
    
    # Test pool list
    pools = await connector.get_pool_list()
    print(f"Found {len(pools)} Raydium pools")
    
    if pools:
        print(f"Top pool: {pools[0]['token_a']['symbol']}/{pools[0]['token_b']['symbol']}")
        print(f"Type: {pools[0]['pool_type']}")
        print(f"Liquidity: ${pools[0]['liquidity_usd']:,.2f}")
        print(f"Volume 24h: ${pools[0]['volume_24h']:,.2f}")
        print(f"Raydium Score: {pools[0]['raydium_score']}")
    
    # Test farms
    farms = await connector.get_farms_list()
    print(f"\nFound {len(farms)} Raydium farms")
    
    if farms:
        print(f"Top farm: {farms[0]['base_token']}/{farms[0]['quote_token']}")
        print(f"APR: {farms[0]['apr']:.2f}%")
        print(f"TVL: ${farms[0]['tvl']:,.2f}")
    
    # Test trending pools
    trending = await connector.get_volume_trending_pools(limit=10)
    print(f"\nFound {len(trending)} trending pools")
    
    # Print API stats
    stats = connector.get_api_call_statistics()
    print(f"\nAPI Stats: {stats}")
    
    await connector.close()

if __name__ == "__main__":
    asyncio.run(test_raydium_connector()) 