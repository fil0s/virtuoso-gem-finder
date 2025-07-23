#!/usr/bin/env python3
"""
Production-ready Orca and Raydium API connectors
Ready for integration into the existing token analysis system
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class OrcaConnector:
    """Production Orca API connector following existing patterns"""
    
    def __init__(self, api_tracking_enabled: bool = True):
        self.base_url = "https://api.orca.so"
        self.session = None
        self.api_tracking_enabled = api_tracking_enabled
        self.api_calls_made = 0
        self.last_call_time = 0
        self.rate_limit_delay = 1.0  # 1 second between calls
        
        # Exclusion list - same pattern as existing connectors
        self.excluded_addresses = {
            # Major stablecoins
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
            # Add more as needed
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, timeout: int = 30) -> Optional[Any]:
        """Make rate-limited API request with tracking"""
        if self.api_tracking_enabled:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
            self.api_calls_made += 1
            self.last_call_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}{endpoint}", timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Orca API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Orca API request failed for {endpoint}: {e}")
            return None
    
    async def get_pools(self) -> List[Dict]:
        """Get all Orca pools"""
        data = await self._make_request("/pools")
        return data if data else []
    
    async def get_whirlpools(self) -> str:
        """Get Orca whirlpools data"""
        try:
            async with self.session.get(f"{self.base_url}/v1/whirlpools", timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                return ""
        except Exception as e:
            logger.error(f"Error fetching Orca whirlpools: {e}")
            return ""
    
    async def get_token_pools(self, token_address: str) -> List[Dict]:
        """Get pools for a specific token"""
        if token_address in self.excluded_addresses:
            return []
            
        pools = await self.get_pools()
        matching_pools = []
        
        for pool in pools:
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                matching_pools.append(pool)
                
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
                'avg_apy': 0
            }
        
        total_liquidity = sum(p.get('liquidity', 0) for p in pools)
        total_volume = sum(p.get('volume_24h', 0) for p in pools)
        apys = [p.get('apy_24h', 0) for p in pools if p.get('apy_24h')]
        avg_apy = sum(apys) / len(apys) if apys else 0
        
        return {
            'found': True,
            'pool_count': len(pools),
            'total_liquidity': total_liquidity,
            'total_volume_24h': total_volume,
            'avg_apy': avg_apy,
            'pools': pools[:3],  # Top 3 pools
            'top_pool': max(pools, key=lambda x: x.get('volume_24h', 0)) if pools else None
        }

class RaydiumConnector:
    """Production Raydium API connector following existing patterns"""
    
    def __init__(self, api_tracking_enabled: bool = True):
        self.base_url = "https://api.raydium.io"
        self.session = None
        self.api_tracking_enabled = api_tracking_enabled
        self.api_calls_made = 0
        self.last_call_time = 0
        self.rate_limit_delay = 1.0  # 1 second between calls
        
        # Exclusion list - same pattern as existing connectors
        self.excluded_addresses = {
            # Major stablecoins
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
            # Add more as needed
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, timeout: int = 60) -> Optional[Any]:
        """Make rate-limited API request with tracking"""
        if self.api_tracking_enabled:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
            self.api_calls_made += 1
            self.last_call_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}{endpoint}", timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Raydium API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Raydium API request failed for {endpoint}: {e}")
            return None
    
    async def get_pools(self, limit: Optional[int] = None) -> List[Dict]:
        """Get Raydium pools"""
        data = await self._make_request("/pools")
        if data and limit:
            return data[:limit]
        return data if data else []
    
    async def get_pairs(self, limit: Optional[int] = None) -> List[Dict]:
        """Get Raydium pairs - more detailed than pools"""
        data = await self._make_request("/pairs")
        if data and limit:
            return data[:limit]
        return data if data else []
    
    async def get_token_pairs(self, token_address: str, search_limit: int = 100000) -> List[Dict]:
        """Get pairs for a specific token"""
        if token_address in self.excluded_addresses:
            return []
            
        pairs = await self.get_pairs(limit=search_limit)
        matching_pairs = []
        
        for pair in pairs:
            pair_str = json.dumps(pair).lower()
            if token_address.lower() in pair_str:
                matching_pairs.append(pair)
                
        return matching_pairs
    
    async def get_volume_trending_pairs(self, min_volume_24h: float = 10000, limit: int = 50) -> List[Dict]:
        """Get trending pairs by volume"""
        pairs = await self.get_pairs(limit=100000)  # Search first 100k
        trending = [
            pair for pair in pairs 
            if pair.get('volume_24h', 0) >= min_volume_24h
        ]
        return sorted(trending, key=lambda x: x.get('volume_24h', 0), reverse=True)[:limit]
    
    async def get_farms_list(self) -> List[Dict]:
        """Get Raydium farms (yield opportunities) - placeholder for future endpoint"""
        # This would be implemented when/if Raydium provides a farms endpoint
        logger.info("Raydium farms endpoint not yet available")
        return []
    
    async def get_pool_stats(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive pool statistics for a token"""
        # Search both pools and pairs
        pools = await self.get_pools(limit=50000)
        pairs = await self.get_token_pairs(token_address, search_limit=100000)
        
        # Find matching pools
        matching_pools = []
        for pool in pools:
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                matching_pools.append(pool)
        
        if not matching_pools and not pairs:
            return {
                'found': False,
                'pool_count': 0,
                'pair_count': 0,
                'total_liquidity': 0,
                'total_volume_24h': 0,
                'avg_apy': 0
            }
        
        # Calculate stats from pools
        pool_liquidity = sum(p.get('liquidity_locked', 0) for p in matching_pools)
        
        # Calculate stats from pairs (more comprehensive)
        pair_liquidity = sum(p.get('liquidity', 0) for p in pairs)
        pair_volume = sum(p.get('volume_24h', 0) for p in pairs)
        
        # APY from pairs
        apys = [p.get('apy', 0) for p in pairs if p.get('apy') and p.get('apy') != 0]
        avg_apy = sum(apys) / len(apys) if apys else 0
        
        return {
            'found': True,
            'pool_count': len(matching_pools),
            'pair_count': len(pairs),
            'total_liquidity': pool_liquidity + pair_liquidity,
            'total_volume_24h': pair_volume,
            'avg_apy': avg_apy,
            'pools': matching_pools[:2],  # Top 2 pools
            'pairs': pairs[:3],  # Top 3 pairs
            'top_pair': max(pairs, key=lambda x: x.get('volume_24h', 0)) if pairs else None
        }

class CrossPlatformDEXAnalyzer:
    """Analyzer that combines Orca and Raydium data like existing CrossPlatformAnalyzer"""
    
    def __init__(self, api_tracking_enabled: bool = True):
        self.api_tracking_enabled = api_tracking_enabled
        self.orca = None
        self.raydium = None
    
    async def __aenter__(self):
        self.orca = await OrcaConnector(self.api_tracking_enabled).__aenter__()
        self.raydium = await RaydiumConnector(self.api_tracking_enabled).__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.orca:
            await self.orca.__aexit__(exc_type, exc_val, exc_tb)
        if self.raydium:
            await self.raydium.__aexit__(exc_type, exc_val, exc_tb)
    
    async def analyze_token_across_dexs(self, token_address: str) -> Dict[str, Any]:
        """Analyze token across both Orca and Raydium"""
        
        # Get data from both DEXs in parallel
        orca_task = self.orca.get_pool_analytics(token_address)
        raydium_task = self.raydium.get_pool_stats(token_address)
        
        orca_data, raydium_data = await asyncio.gather(orca_task, raydium_task)
        
        # Combine results
        total_liquidity = orca_data.get('total_liquidity', 0) + raydium_data.get('total_liquidity', 0)
        total_volume = orca_data.get('total_volume_24h', 0) + raydium_data.get('total_volume_24h', 0)
        
        # Calculate DEX distribution
        dex_distribution = {}
        if orca_data.get('found'):
            dex_distribution['orca'] = {
                'pools': orca_data.get('pool_count', 0),
                'liquidity': orca_data.get('total_liquidity', 0),
                'volume_24h': orca_data.get('total_volume_24h', 0)
            }
        
        if raydium_data.get('found'):
            dex_distribution['raydium'] = {
                'pools': raydium_data.get('pool_count', 0),
                'pairs': raydium_data.get('pair_count', 0),
                'liquidity': raydium_data.get('total_liquidity', 0),
                'volume_24h': raydium_data.get('total_volume_24h', 0)
            }
        
        return {
            'token_address': token_address,
            'found_on_dexs': len(dex_distribution),
            'total_liquidity': total_liquidity,
            'total_volume_24h': total_volume,
            'dex_distribution': dex_distribution,
            'orca_data': orca_data,
            'raydium_data': raydium_data,
            'analysis_timestamp': datetime.now().isoformat(),
            'api_calls_made': {
                'orca': self.orca.api_calls_made,
                'raydium': self.raydium.api_calls_made
            }
        }
    
    async def get_trending_across_dexs(self, min_volume: float = 10000) -> Dict[str, List[Dict]]:
        """Get trending tokens across both DEXs"""
        
        # Get trending from both DEXs in parallel
        orca_task = self.orca.get_trending_pools(min_volume_24h=min_volume)
        raydium_task = self.raydium.get_volume_trending_pairs(min_volume_24h=min_volume)
        
        orca_trending, raydium_trending = await asyncio.gather(orca_task, raydium_task)
        
        return {
            'orca_trending': orca_trending,
            'raydium_trending': raydium_trending,
            'combined_count': len(orca_trending) + len(raydium_trending)
        }

# Example usage and integration patterns
async def demo_integration():
    """Demo showing how to integrate with existing system"""
    
    print("🔗 ORCA AND RAYDIUM INTEGRATION DEMO")
    print("=" * 50)
    
    # Test with TRUMP token (we know it exists)
    trump_address = "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"
    
    async with CrossPlatformDEXAnalyzer() as analyzer:
        # Analyze specific token
        print(f"🔍 Analyzing TRUMP token: {trump_address}")
        result = await analyzer.analyze_token_across_dexs(trump_address)
        
        print(f"✅ Found on {result['found_on_dexs']} DEXs")
        print(f"💰 Total Liquidity: ${result['total_liquidity']:,.2f}")
        print(f"📊 Total Volume 24h: ${result['total_volume_24h']:,.2f}")
        
        if 'orca' in result['dex_distribution']:
            orca = result['dex_distribution']['orca']
            print(f"🌊 Orca: {orca['pools']} pools, ${orca['liquidity']:,.2f} liquidity")
        
        if 'raydium' in result['dex_distribution']:
            raydium = result['dex_distribution']['raydium']
            print(f"⚡ Raydium: {raydium.get('pools', 0)} pools, {raydium.get('pairs', 0)} pairs")
            print(f"   Liquidity: ${raydium['liquidity']:,.2f}, Volume: ${raydium['volume_24h']:,.2f}")
        
        print(f"📞 API calls made: Orca={result['api_calls_made']['orca']}, Raydium={result['api_calls_made']['raydium']}")
        
        # Get trending
        print(f"\n📈 Getting trending tokens...")
        trending = await analyzer.get_trending_across_dexs(min_volume=5000)
        print(f"🌊 Orca trending: {len(trending['orca_trending'])} tokens")
        print(f"⚡ Raydium trending: {len(trending['raydium_trending'])} tokens")

if __name__ == "__main__":
    asyncio.run(demo_integration()) 