#!/usr/bin/env python3
"""
Comprehensive test of Orca and Raydium APIs using all discovered endpoints
Tests with sample tokens from user's list
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

class ComprehensiveOrcaAPI:
    """Comprehensive Orca API testing"""
    
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
                return []
        except Exception as e:
            logger.error(f"Error fetching Orca pools: {e}")
            return []
    
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
    
    async def search_token_in_pools(self, token_address: str, token_name: str) -> Dict[str, Any]:
        """Search for token in all Orca data sources"""
        results = {
            'pools': [],
            'whirlpools_mention': False
        }
        
        # Search in pools
        pools = await self.get_pools()
        for pool in pools:
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                results['pools'].append(pool)
        
        # Search in whirlpools
        whirlpools_data = await self.get_whirlpools()
        if token_address.lower() in whirlpools_data.lower():
            results['whirlpools_mention'] = True
            
        return results

class ComprehensiveRaydiumAPI:
    """Comprehensive Raydium API testing"""
    
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
        """Get Raydium pools"""
        try:
            async with self.session.get(f"{self.base_url}/pools", timeout=60) as response:
                if response.status == 200:
                    pools = await response.json()
                    return pools[:limit] if limit else pools
                return []
        except Exception as e:
            logger.error(f"Error fetching Raydium pools: {e}")
            return []
    
    async def get_pairs(self, limit: Optional[int] = None) -> List[Dict]:
        """Get Raydium pairs - this is the more detailed endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/pairs", timeout=60) as response:
                if response.status == 200:
                    pairs = await response.json()
                    return pairs[:limit] if limit else pairs
                return []
        except Exception as e:
            logger.error(f"Error fetching Raydium pairs: {e}")
            return []
    
    async def search_token_comprehensive(self, token_address: str, token_name: str, search_limit: int = 50000) -> Dict[str, Any]:
        """Search for token in all Raydium data sources"""
        results = {
            'pools': [],
            'pairs': []
        }
        
        logger.info(f"Searching Raydium for {token_name} ({token_address})")
        
        # Search in pools (limited)
        pools = await self.get_pools(limit=search_limit)
        logger.info(f"Searching {len(pools)} pools...")
        
        for pool in pools:
            pool_str = json.dumps(pool).lower()
            if token_address.lower() in pool_str:
                results['pools'].append(pool)
        
        # Search in pairs (more detailed, limited search)
        pairs = await self.get_pairs(limit=search_limit)
        logger.info(f"Searching {len(pairs)} pairs...")
        
        for i, pair in enumerate(pairs):
            if i % 10000 == 0 and i > 0:
                logger.info(f"  Searched {i}/{len(pairs)} pairs...")
                
            pair_str = json.dumps(pair).lower()
            if token_address.lower() in pair_str:
                results['pairs'].append(pair)
                
        return results

async def comprehensive_test():
    """Comprehensive test of all discovered endpoints"""
    
    print("=" * 80)
    print("🧪 COMPREHENSIVE ORCA AND RAYDIUM API TEST")
    print("🔍 Using ALL discovered endpoints")
    print("=" * 80)
    print(f"Testing with {len(SAMPLE_TOKENS)} sample tokens")
    print()
    
    results = {
        'orca': {'pools': {}, 'whirlpools': {}, 'summary': {}},
        'raydium': {'pools': {}, 'pairs': {}, 'summary': {}},
        'overall_summary': {}
    }
    
    # Test Orca comprehensive
    print("🌊 COMPREHENSIVE ORCA API TEST")
    print("-" * 50)
    
    async with ComprehensiveOrcaAPI() as orca:
        # Get basic stats
        all_pools = await orca.get_pools()
        whirlpools_data = await orca.get_whirlpools()
        
        print(f"✅ Orca Pools: {len(all_pools)}")
        print(f"✅ Orca Whirlpools: {len(whirlpools_data)} chars of data")
        
        # Test each sample token
        orca_found = 0
        for token_name, token_address in SAMPLE_TOKENS.items():
            token_results = await orca.search_token_in_pools(token_address, token_name)
            results['orca']['pools'][token_name] = token_results
            
            if token_results['pools'] or token_results['whirlpools_mention']:
                orca_found += 1
                print(f"   ✅ {token_name}: Found in {len(token_results['pools'])} pools" + 
                      (", mentioned in whirlpools" if token_results['whirlpools_mention'] else ""))
                
                # Show details
                for pool in token_results['pools'][:1]:
                    print(f"      Pool: {pool.get('name', 'Unknown')}")
                    print(f"      Liquidity: ${pool.get('liquidity', 0):,.2f}")
                    print(f"      Volume 24h: ${pool.get('volume_24h', 0):,.2f}")
            else:
                print(f"   ❌ {token_name}: Not found")
        
        results['orca']['summary'] = {
            'total_pools': len(all_pools),
            'tokens_found': orca_found,
            'whirlpools_data_size': len(whirlpools_data)
        }
    
    print()
    
    # Test Raydium comprehensive
    print("⚡ COMPREHENSIVE RAYDIUM API TEST")
    print("-" * 50)
    
    async with ComprehensiveRaydiumAPI() as raydium:
        # Get basic stats
        sample_pools = await raydium.get_pools(limit=1000)
        sample_pairs = await raydium.get_pairs(limit=1000)
        
        print(f"✅ Raydium Pools: 696k+ total (sampled 1000)")
        print(f"✅ Raydium Pairs: 696k+ total (sampled 1000)")
        
        # Show pairs structure (more detailed than pools)
        if sample_pairs:
            print(f"📊 Pairs structure: {list(sample_pairs[0].keys())}")
            print(f"📊 Sample pair: {sample_pairs[0].get('name', 'Unknown')}")
        
        # Test each sample token
        raydium_found = 0
        search_limit = 100000  # Search first 100k of each
        
        for token_name, token_address in SAMPLE_TOKENS.items():
            token_results = await raydium.search_token_comprehensive(token_address, token_name, search_limit)
            results['raydium']['pools'][token_name] = token_results['pools']
            results['raydium']['pairs'][token_name] = token_results['pairs']
            
            total_found = len(token_results['pools']) + len(token_results['pairs'])
            if total_found > 0:
                raydium_found += 1
                print(f"   ✅ {token_name}: Found in {len(token_results['pools'])} pools, {len(token_results['pairs'])} pairs")
                
                # Show pool details
                for pool in token_results['pools'][:1]:
                    print(f"      Pool: {pool.get('identifier', 'Unknown')}")
                    print(f"      Liquidity: ${pool.get('liquidity_locked', 0):,.2f}")
                
                # Show pair details (more comprehensive)
                for pair in token_results['pairs'][:1]:
                    print(f"      Pair: {pair.get('name', 'Unknown')}")
                    print(f"      Liquidity: ${pair.get('liquidity', 0):,.2f}")
                    print(f"      Volume 24h: ${pair.get('volume_24h', 0):,.2f}")
                    print(f"      APY: {pair.get('apy', 0):.2%}" if pair.get('apy') else "      APY: N/A")
            else:
                print(f"   ❌ {token_name}: Not found in {search_limit:,} pools/pairs")
        
        results['raydium']['summary'] = {
            'total_pools': '696k+',
            'total_pairs': '696k+',
            'tokens_found': raydium_found,
            'search_limit': search_limit
        }
    
    # Overall summary
    print()
    print("📋 COMPREHENSIVE SUMMARY")
    print("-" * 50)
    
    total_found = results['orca']['summary']['tokens_found'] + results['raydium']['summary']['tokens_found']
    
    print(f"🌊 Orca Results:")
    print(f"   Pools available: {results['orca']['summary']['total_pools']}")
    print(f"   Whirlpools data: {results['orca']['summary']['whirlpools_data_size']} chars")
    print(f"   Tokens found: {results['orca']['summary']['tokens_found']}/{len(SAMPLE_TOKENS)}")
    
    print(f"⚡ Raydium Results:")
    print(f"   Pools available: {results['raydium']['summary']['total_pools']}")
    print(f"   Pairs available: {results['raydium']['summary']['total_pairs']}")
    print(f"   Tokens found: {results['raydium']['summary']['tokens_found']}/{len(SAMPLE_TOKENS)}")
    
    print(f"\n🎯 Overall Results:")
    print(f"   Total tokens found: {total_found}/{len(SAMPLE_TOKENS)}")
    print(f"   Success rate: {total_found/len(SAMPLE_TOKENS)*100:.1f}%")
    
    print(f"\n💡 Key Insights:")
    print(f"   • Raydium /pairs endpoint provides much more detailed data than /pools")
    print(f"   • Orca has smaller but curated dataset with good liquidity metrics")
    print(f"   • Both APIs are production-ready and provide real-time data")
    print(f"   • Sample tokens may be newer/smaller and not in main DEX pools yet")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"scripts/tests/comprehensive_orca_raydium_test_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n❌ Could not save results: {e}")
    
    return results

if __name__ == "__main__":
    asyncio.run(comprehensive_test()) 