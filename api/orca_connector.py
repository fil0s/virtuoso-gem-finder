"""
Orca DEX API connector for enhanced liquidity and pool analysis
Integrates with existing virtuoso_gem_hunter API system
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class OrcaConnector:
    """Production Orca API connector following existing system patterns"""
    
    def __init__(self, enhanced_cache=None, api_tracking_enabled: bool = True):
        self.base_url = "https://api.mainnet.orca.so/v1"  # Fixed to working endpoint
        self.session = None
        self.enhanced_cache = enhanced_cache
        self.api_tracking_enabled = api_tracking_enabled
        
        # API tracking stats
        self.api_calls_made = 0
        self.last_call_time = 0
        self.rate_limit_delay = 1.0  # 1 second between calls
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0
        
        # WSOL filtering
        self.wsol_address = 'So11111111111111111111111111111111111111112'
        
        # Load exclusion list (same pattern as existing connectors)
        self._load_exclusions()
    
    def _load_exclusions(self):
        """Load token exclusion list following existing patterns"""
        self.excluded_addresses = {
            # Major stablecoins
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
            'EjmyN6qEC1Tf1JxiG1ae7UTJhUxSwk1TCWNWqxWV4J6o',  # DAI
            '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',  # BTC
            '2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk',  # ETH
            # Wrapped tokens
            'So11111111111111111111111111111111111111112',   # SOL
            'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',  # BONK
            # Add more as needed
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics following existing patterns"""
        avg_response_time = (self.total_response_time / max(1, self.successful_calls))
        
        return {
            'total_calls': self.api_calls_made,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': self.successful_calls / max(1, self.api_calls_made),
            'average_response_time': avg_response_time,
            'last_call_time': self.last_call_time
        }
    
    def reset_api_statistics(self):
        """Reset API statistics"""
        self.api_calls_made = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_response_time = 0
        self.last_call_time = 0
    
    async def _make_tracked_request(self, endpoint: str, timeout: int = 30) -> Optional[Any]:
        """Make rate-limited API request with tracking"""
        if self.api_tracking_enabled:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
            self.api_calls_made += 1
            self.last_call_time = time.time()
        
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}{endpoint}", timeout=timeout) as response:
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                if response.status == 200:
                    self.successful_calls += 1
                    return await response.json()
                else:
                    self.failed_calls += 1
                    logger.warning(f"Orca API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            self.failed_calls += 1
            response_time = time.time() - start_time
            self.total_response_time += response_time
            logger.error(f"Orca API request failed for {endpoint}: {e}")
            return None
    
    async def get_pools(self) -> List[Dict]:
        """Get all Orca whirlpools using the correct endpoint"""
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("orca_pools", "all_pools")
            if cached_data:
                return cached_data
        
        # Use the correct working endpoint
        data = await self._make_tracked_request("/whirlpool/list")
        
        # Handle the response structure correctly
        if data and isinstance(data, dict) and 'whirlpools' in data:
            pools = data['whirlpools']
        else:
            pools = data if data else []
        
        # Cache the results
        if self.enhanced_cache and pools:
            self.enhanced_cache.set_enhanced("orca_pools", "all_pools", pools)
        
        return pools
    
    async def get_whirlpools(self) -> str:
        """Get Orca whirlpools data - Updated to use correct API"""
        pools = await self.get_pools()
        return json.dumps(pools) if pools else ""
    
    async def get_token_pools(self, token_address: str) -> List[Dict]:
        """Get pools for a specific token"""
        if token_address in self.excluded_addresses:
            return []
        
        # Check cache first
        if self.enhanced_cache:
            cached_data = self.enhanced_cache.get_enhanced("orca_token_pools", token_address)
            if cached_data:
                return cached_data
            
        pools = await self.get_pools()
        matching_pools = []
        
        for pool in pools:
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                matching_pools.append(pool)
        
        # Cache the results
        if self.enhanced_cache:
            self.enhanced_cache.set_enhanced("orca_token_pools", token_address, matching_pools)
                
        return matching_pools
    
    async def get_trending_pools(self, min_volume_24h: float = 1000) -> List[Dict]:
        """Get trending pools by volume"""
        pools = await self.get_pools()
        trending = [
            pool for pool in pools 
            if pool.get('volume_24h', 0) >= min_volume_24h
        ]
        return sorted(trending, key=lambda x: x.get('volume_24h', 0), reverse=True)
    
    async def get_pool_analytics(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive pool analytics for a token"""
        pools = await self.get_token_pools(token_address)
        
        if not pools:
            return {
                'found': False,
                'pool_count': 0,
                'total_liquidity': 0,
                'total_volume_24h': 0,
                'avg_apy': 0,
                'quality_score': 0
            }
        
        # Calculate aggregated metrics
        total_liquidity = sum(p.get('liquidity', 0) for p in pools)
        total_volume = sum(p.get('volume_24h', 0) for p in pools)
        apys = [p.get('apy_24h', 0) for p in pools if p.get('apy_24h')]
        avg_apy = sum(apys) / len(apys) if apys else 0
        
        # Calculate quality score based on liquidity and volume
        quality_score = self._calculate_orca_quality_score(total_liquidity, total_volume, len(pools))
        
        return {
            'found': True,
            'pool_count': len(pools),
            'total_liquidity': total_liquidity,
            'total_volume_24h': total_volume,
            'avg_apy': avg_apy,
            'quality_score': quality_score,
            'pools': pools[:3],  # Top 3 pools
            'top_pool': max(pools, key=lambda x: x.get('volume_24h', 0)) if pools else None,
            'dex_name': 'Orca'
        }
    
    def _calculate_orca_quality_score(self, liquidity: float, volume: float, pool_count: int) -> float:
        """Calculate Orca-specific quality score"""
        # Base score from liquidity (0-40 points)
        liquidity_score = min(40, liquidity / 1000)  # 1 point per $1k liquidity, max 40
        
        # Volume score (0-30 points)
        volume_score = min(30, volume / 100)  # 1 point per $100 volume, max 30
        
        # Pool diversity score (0-20 points)
        diversity_score = min(20, pool_count * 5)  # 5 points per pool, max 20
        
        # APY bonus (0-10 points) - will be added if APY data available
        apy_bonus = 10 if liquidity > 10000 and volume > 1000 else 0
        
        return liquidity_score + volume_score + diversity_score + apy_bonus
    
    async def get_batch_token_analytics(self, token_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get analytics for multiple tokens efficiently"""
        results = {}
        
        # Get all pools once
        all_pools = await self.get_pools()
        
        for token_address in token_addresses:
            if token_address in self.excluded_addresses:
                continue
                
            # Find matching pools for this token
            matching_pools = []
            for pool in all_pools:
                pool_str = json.dumps(pool).lower()
                if token_address.lower() in pool_str:
                    matching_pools.append(pool)
            
            # Calculate analytics
            if matching_pools:
                total_liquidity = sum(p.get('liquidity', 0) for p in matching_pools)
                total_volume = sum(p.get('volume_24h', 0) for p in matching_pools)
                apys = [p.get('apy_24h', 0) for p in matching_pools if p.get('apy_24h')]
                avg_apy = sum(apys) / len(apys) if apys else 0
                quality_score = self._calculate_orca_quality_score(total_liquidity, total_volume, len(matching_pools))
                
                results[token_address] = {
                    'found': True,
                    'pool_count': len(matching_pools),
                    'total_liquidity': total_liquidity,
                    'total_volume_24h': total_volume,
                    'avg_apy': avg_apy,
                    'quality_score': quality_score,
                    'dex_name': 'Orca'
                }
            else:
                results[token_address] = {
                    'found': False,
                    'pool_count': 0,
                    'total_liquidity': 0,
                    'total_volume_24h': 0,
                    'avg_apy': 0,
                    'quality_score': 0,
                    'dex_name': 'Orca'
                }
        
        return results
    
    async def get_wsol_trending_pools(self, limit: int = 50) -> List[Dict]:
        """Get trending WSOL-paired pools for WSOL filtering mode"""
        pools = await self.get_pools()
        
        if not pools:
            return []
        
        wsol_pools = []
        excluded_count = 0
        
        for pool in pools:
            # Extract token addresses from pool
            token_a = pool.get('tokenA', {}).get('mint', '') if isinstance(pool.get('tokenA'), dict) else ''
            token_b = pool.get('tokenB', {}).get('mint', '') if isinstance(pool.get('tokenB'), dict) else ''
            
            # Only include pools where one side is WSOL and the other is not excluded
            if token_a == self.wsol_address and token_b and token_b not in self.excluded_addresses:
                # WSOL-tokenB pair
                wsol_pools.append({
                    'address': token_b,
                    'symbol': pool.get('tokenB', {}).get('symbol', 'Unknown') if isinstance(pool.get('tokenB'), dict) else 'Unknown',
                    'pool_address': pool.get('address', ''),
                    'tvl': pool.get('tvl', 0),
                    'volume': pool.get('volume', {}).get('day', 0) if isinstance(pool.get('volume'), dict) else 0,
                    'volume_24h': pool.get('volume', {}).get('day', 0) if isinstance(pool.get('volume'), dict) else 0,
                    'price': pool.get('price', 0),
                    'fee_apr': pool.get('feeApr', 0),
                    'reward_apr': pool.get('totalApr', 0),
                    'liquidity': pool.get('tvl', 0),
                    'discovery_source': 'orca_whirlpool_trending',
                    'is_wsol_pair': True,
                    'pair_type': f'WSOL-{token_b[:8]}...',
                    'raw_pool_data': pool
                })
                
            elif token_b == self.wsol_address and token_a and token_a not in self.excluded_addresses:
                # tokenA-WSOL pair
                wsol_pools.append({
                    'address': token_a,
                    'symbol': pool.get('tokenA', {}).get('symbol', 'Unknown') if isinstance(pool.get('tokenA'), dict) else 'Unknown',
                    'pool_address': pool.get('address', ''),
                    'tvl': pool.get('tvl', 0),
                    'volume': pool.get('volume', {}).get('day', 0) if isinstance(pool.get('volume'), dict) else 0,
                    'volume_24h': pool.get('volume', {}).get('day', 0) if isinstance(pool.get('volume'), dict) else 0,
                    'price': pool.get('price', 0),
                    'fee_apr': pool.get('feeApr', 0),
                    'reward_apr': pool.get('totalApr', 0),
                    'liquidity': pool.get('tvl', 0),
                    'discovery_source': 'orca_whirlpool_trending',
                    'is_wsol_pair': True,
                    'pair_type': f'{token_a[:8]}...-WSOL',
                    'raw_pool_data': pool
                })
            else:
                excluded_count += 1
        
        # Sort by volume/TVL and limit results
        wsol_pools.sort(key=lambda x: x.get('volume_24h', 0) + x.get('tvl', 0), reverse=True)
        
        logger.info(f"🌀 Orca WSOL filtering: Found {len(wsol_pools)} WSOL pairs, excluded {excluded_count} non-WSOL pairs")
        
        return wsol_pools[:limit]
    
    async def close(self):
        """Close the connector"""
        if self.session:
            await self.session.close() 