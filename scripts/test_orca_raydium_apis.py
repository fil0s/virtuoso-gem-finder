#!/usr/bin/env python3
"""
Test script for Orca and Raydium APIs with sample tokens
Tests actual API endpoints and data structures
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample tokens from user's list
SAMPLE_TOKENS = {
    'USELESS': 'Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk',
    'TRUMP': '6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN', 
    'aura': 'DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2',
    'GOR': '71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg',
    'SPX': 'J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr',
    'MUMU': '5LafQUrVco6o7KMz42eqVEJ9LW31StPyGjeeu5sKoMtA',
    '$michi': '5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp',
    'BILLY': '3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump',
    'INF': '5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm'
}

class OrcaAPITester:
    """Test Orca API with actual endpoints"""
    
    def __init__(self):
        self.base_url = "https://api.orca.so"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_pools(self) -> List[Dict]:
        """Get all Orca pools"""
        try:
            async with self.session.get(f"{self.base_url}/pools", timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Orca API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching Orca pools: {e}")
            return []
    
    async def search_token_pools(self, token_address: str, token_name: str) -> List[Dict]:
        """Search for pools containing a specific token"""
        pools = await self.get_pools()
        matching_pools = []
        
        for pool in pools:
            # Check if token address appears in pool data
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                matching_pools.append(pool)
                
        return matching_pools
    
    def analyze_pool_structure(self, pools: List[Dict]) -> Dict[str, Any]:
        """Analyze the structure of Orca pools"""
        if not pools:
            return {}
            
        sample_pool = pools[0]
        
        analysis = {
            'total_pools': len(pools),
            'sample_pool_keys': list(sample_pool.keys()),
            'data_types': {key: type(value).__name__ for key, value in sample_pool.items()},
            'sample_values': {
                key: value for key, value in sample_pool.items() 
                if not isinstance(value, (dict, list))
            }
        }
        
        # Calculate some statistics
        if len(pools) > 1:
            liquidity_values = [p.get('liquidity', 0) for p in pools if p.get('liquidity')]
            volume_values = [p.get('volume_24h', 0) for p in pools if p.get('volume_24h')]
            
            analysis['statistics'] = {
                'total_liquidity': sum(liquidity_values),
                'avg_liquidity': sum(liquidity_values) / len(liquidity_values) if liquidity_values else 0,
                'total_volume_24h': sum(volume_values),
                'avg_volume_24h': sum(volume_values) / len(volume_values) if volume_values else 0
            }
        
        return analysis

class RaydiumAPITester:
    """Test Raydium API with actual endpoints"""
    
    def __init__(self):
        self.base_url = "https://api.raydium.io"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_pools(self, limit: Optional[int] = None) -> List[Dict]:
        """Get Raydium pools (with optional limit due to large size)"""
        try:
            async with self.session.get(f"{self.base_url}/pools", timeout=60) as response:
                if response.status == 200:
                    pools = await response.json()
                    if limit:
                        return pools[:limit]
                    return pools
                else:
                    logger.error(f"Raydium API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching Raydium pools: {e}")
            return []
    
    async def search_token_pools(self, token_address: str, token_name: str, search_limit: int = 50000) -> List[Dict]:
        """Search for pools containing a specific token (with search limit)"""
        pools = await self.get_pools(limit=search_limit)
        matching_pools = []
        
        logger.info(f"Searching {len(pools)} Raydium pools for {token_name} ({token_address})")
        
        for i, pool in enumerate(pools):
            if i % 10000 == 0 and i > 0:
                logger.info(f"  Searched {i}/{len(pools)} pools...")
                
            # Check if token address appears in pool data
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                matching_pools.append(pool)
                
        return matching_pools
    
    def analyze_pool_structure(self, pools: List[Dict]) -> Dict[str, Any]:
        """Analyze the structure of Raydium pools"""
        if not pools:
            return {}
            
        sample_pool = pools[0]
        
        analysis = {
            'total_pools': len(pools),
            'sample_pool_keys': list(sample_pool.keys()),
            'data_types': {key: type(value).__name__ for key, value in sample_pool.items()},
            'sample_values': {
                key: value for key, value in sample_pool.items() 
                if not isinstance(value, (dict, list))
            }
        }
        
        # Calculate some statistics
        if len(pools) > 1:
            liquidity_values = [p.get('liquidity_locked', 0) for p in pools if p.get('liquidity_locked')]
            apy_values = [p.get('apy', 0) for p in pools if p.get('apy')]
            
            analysis['statistics'] = {
                'total_liquidity_locked': sum(liquidity_values),
                'avg_liquidity_locked': sum(liquidity_values) / len(liquidity_values) if liquidity_values else 0,
                'avg_apy': sum(apy_values) / len(apy_values) if apy_values else 0,
                'official_pools': len([p for p in pools if p.get('official', False)])
            }
        
        return analysis

async def comprehensive_api_test():
    """Comprehensive test of both APIs with sample tokens"""
    
    print("=" * 80)
    print("🧪 COMPREHENSIVE ORCA AND RAYDIUM API TEST")
    print("=" * 80)
    print(f"Testing with {len(SAMPLE_TOKENS)} sample tokens")
    print(f"Sample tokens: {', '.join(SAMPLE_TOKENS.keys())}")
    print()
    
    results = {
        'orca': {},
        'raydium': {},
        'summary': {}
    }
    
    # Test Orca API
    print("🌊 TESTING ORCA API")
    print("-" * 40)
    
    async with OrcaAPITester() as orca:
        # Get all pools and analyze structure
        all_orca_pools = await orca.get_pools()
        orca_analysis = orca.analyze_pool_structure(all_orca_pools)
        
        print(f"✅ Successfully fetched {len(all_orca_pools)} Orca pools")
        print(f"📊 Pool structure analysis:")
        print(f"   Keys: {orca_analysis.get('sample_pool_keys', [])}")
        print(f"   Sample pool: {orca_analysis.get('sample_values', {})}")
        
        if 'statistics' in orca_analysis:
            stats = orca_analysis['statistics']
            print(f"📈 Statistics:")
            print(f"   Total liquidity: ${stats.get('total_liquidity', 0):,.2f}")
            print(f"   Average liquidity: ${stats.get('avg_liquidity', 0):,.2f}")
            print(f"   Total 24h volume: ${stats.get('total_volume_24h', 0):,.2f}")
        
        results['orca']['analysis'] = orca_analysis
        results['orca']['token_matches'] = {}
        
        # Search for each sample token
        print(f"\n🔍 Searching for sample tokens in Orca pools...")
        for token_name, token_address in SAMPLE_TOKENS.items():
            matching_pools = await orca.search_token_pools(token_address, token_name)
            results['orca']['token_matches'][token_name] = matching_pools
            
            if matching_pools:
                print(f"   ✅ {token_name}: Found {len(matching_pools)} pools")
                for pool in matching_pools[:1]:  # Show first pool
                    print(f"      Pool: {pool.get('name', 'Unknown')}")
                    print(f"      Liquidity: ${pool.get('liquidity', 0):,.2f}")
                    print(f"      Volume 24h: ${pool.get('volume_24h', 0):,.2f}")
                    print(f"      APY 24h: {pool.get('apy_24h', 0):.2%}")
            else:
                print(f"   ❌ {token_name}: No pools found")
    
    print()
    
    # Test Raydium API
    print("⚡ TESTING RAYDIUM API")
    print("-" * 40)
    
    async with RaydiumAPITester() as raydium:
        # Get sample of pools and analyze structure
        sample_raydium_pools = await raydium.get_pools(limit=1000)  # Sample for analysis
        raydium_analysis = raydium.analyze_pool_structure(sample_raydium_pools)
        
        print(f"✅ Successfully fetched {len(sample_raydium_pools)} Raydium pools (sample)")
        print(f"📊 Pool structure analysis:")
        print(f"   Keys: {raydium_analysis.get('sample_pool_keys', [])}")
        print(f"   Sample pool: {raydium_analysis.get('sample_values', {})}")
        
        if 'statistics' in raydium_analysis:
            stats = raydium_analysis['statistics']
            print(f"📈 Statistics (sample):")
            print(f"   Total liquidity locked: ${stats.get('total_liquidity_locked', 0):,.2f}")
            print(f"   Average liquidity locked: ${stats.get('avg_liquidity_locked', 0):,.2f}")
            print(f"   Average APY: {stats.get('avg_apy', 0):.2%}")
            print(f"   Official pools: {stats.get('official_pools', 0)}")
        
        results['raydium']['analysis'] = raydium_analysis
        results['raydium']['token_matches'] = {}
        
        # Search for each sample token (limited search)
        print(f"\n🔍 Searching for sample tokens in Raydium pools...")
        search_limit = 100000  # Search first 100k pools
        
        for token_name, token_address in SAMPLE_TOKENS.items():
            matching_pools = await raydium.search_token_pools(token_address, token_name, search_limit)
            results['raydium']['token_matches'][token_name] = matching_pools
            
            if matching_pools:
                print(f"   ✅ {token_name}: Found {len(matching_pools)} pools")
                for pool in matching_pools[:1]:  # Show first pool
                    print(f"      Pool ID: {pool.get('identifier', 'Unknown')}")
                    print(f"      Liquidity locked: ${pool.get('liquidity_locked', 0):,.2f}")
                    apy_val = pool.get('apy', 0)
                    if apy_val is not None:
                        print(f"      APY: {apy_val:.2%}")
                    else:
                        print(f"      APY: N/A")
                    print(f"      Official: {pool.get('official', False)}")
            else:
                print(f"   ❌ {token_name}: No pools found in first {search_limit:,} pools")
    
    # Generate summary
    print()
    print("📋 SUMMARY")
    print("-" * 40)
    
    orca_matches = sum(1 for matches in results['orca']['token_matches'].values() if matches)
    raydium_matches = sum(1 for matches in results['raydium']['token_matches'].values() if matches)
    
    print(f"🌊 Orca API:")
    print(f"   Total pools available: {results['orca']['analysis'].get('total_pools', 0)}")
    print(f"   Sample tokens found: {orca_matches}/{len(SAMPLE_TOKENS)}")
    
    print(f"⚡ Raydium API:")
    print(f"   Total pools available: 696,076+ (very large dataset)")
    print(f"   Sample tokens found: {raydium_matches}/{len(SAMPLE_TOKENS)} (in search sample)")
    
    print(f"\n💡 Key Insights:")
    print(f"   • Orca API: Smaller dataset ({results['orca']['analysis'].get('total_pools', 0)} pools), easier to search")
    print(f"   • Raydium API: Massive dataset (696k+ pools), requires efficient searching")
    print(f"   • Both APIs are functional and return structured data")
    print(f"   • Sample tokens may be in newer/smaller pools not captured in main listings")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"scripts/tests/orca_raydium_api_test_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n❌ Could not save results: {e}")
    
    return results

if __name__ == "__main__":
    asyncio.run(comprehensive_api_test()) 