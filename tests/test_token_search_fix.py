#!/usr/bin/env python3
"""
Test to verify token search logic and identify the real issue
"""

import asyncio
import json
from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector

async def test_token_search_logic():
    print("🔍 Testing Token Search Logic")
    print("="*50)
    
    # Test with both excluded and non-excluded tokens
    test_tokens = {
        "USDC (excluded)": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "SOL (excluded)": "So11111111111111111111111111111111111111112", 
        "BONK (excluded)": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        # Test with a random token that should NOT be excluded
        "Random Token": "9rguDaKqTrVjaDXafq6E7rKGn7NPHomkdb8RKpjKCDm2"  # SAMO from sample
    }
    
    print("\n🌊 TESTING ORCA:")
    async with OrcaConnector(enhanced_cache=None) as orca:
        # First, let's examine the actual pool structure
        pools = await orca.get_pools()
        print(f"📊 Retrieved {len(pools)} Orca pools")
        
        if pools:
            print("\n📋 Sample Orca Pool Structure:")
            sample_pool = pools[0]
            print(json.dumps(sample_pool, indent=2))
            
            # Check if our test tokens appear in ANY pool
            print("\n🔍 Searching for token addresses in pool data:")
            for token_name, token_address in test_tokens.items():
                found_pools = []
                for pool in pools:
                    pool_str = json.dumps(pool).lower()
                    if token_address.lower() in pool_str:
                        found_pools.append(pool)
                
                print(f"  {token_name}: {len(found_pools)} pools found via string search")
                
                # Test actual connector method
                connector_result = await orca.get_token_pools(token_address)
                print(f"    Connector method: {len(connector_result)} pools")
                
                # Check if token is excluded
                is_excluded = token_address in orca.excluded_addresses
                print(f"    Excluded: {is_excluded}")
        
        print(f"\n📊 Orca Exclusion List Size: {len(orca.excluded_addresses)}")
        print(f"    Excluded tokens: {list(orca.excluded_addresses)[:5]}...")
    
    print("\n☀️ TESTING RAYDIUM:")
    async with RaydiumConnector(enhanced_cache=None) as raydium:
        # Test pairs (limit to avoid huge download)
        pairs = await raydium.get_pairs(limit=100)
        print(f"📊 Retrieved {len(pairs)} Raydium pairs")
        
        if pairs:
            print("\n📋 Sample Raydium Pair Structure:")
            sample_pair = pairs[0]
            print(json.dumps(sample_pair, indent=2))
            
            # Check if our test tokens appear in ANY pair
            print("\n🔍 Searching for token addresses in pair data:")
            for token_name, token_address in test_tokens.items():
                found_pairs = []
                for pair in pairs:
                    pair_str = json.dumps(pair).lower()
                    if token_address.lower() in pair_str:
                        found_pairs.append(pair)
                
                print(f"  {token_name}: {len(found_pairs)} pairs found via string search")
                
                # Test actual connector method
                connector_result = await raydium.get_token_pairs(token_address, search_limit=1000)
                print(f"    Connector method: {len(connector_result)} pairs")
                
                # Check if token is excluded
                is_excluded = token_address in raydium.excluded_addresses
                print(f"    Excluded: {is_excluded}")
        
        print(f"\n📊 Raydium Exclusion List Size: {len(raydium.excluded_addresses)}")
        print(f"    Excluded tokens: {list(raydium.excluded_addresses)[:5]}...")

async def test_with_working_token():
    """Test with a token that should definitely work"""
    print("\n" + "="*50)
    print("🎯 TESTING WITH NON-EXCLUDED TOKEN")
    print("="*50)
    
    # Use SAMO token from the sample Orca pool
    samo_address = "9rguDaKqTrVjaDXafq6E7rKGn7NPHomkdb8RKpjKCDm2"
    
    print(f"Testing with SAMO: {samo_address}")
    
    async with OrcaConnector(enhanced_cache=None) as orca:
        pools = await orca.get_token_pools(samo_address)
        analytics = await orca.get_pool_analytics(samo_address)
        
        print(f"🌊 ORCA Results for SAMO:")
        print(f"   Pools found: {len(pools)}")
        print(f"   Analytics found: {analytics.get('found', False)}")
        print(f"   Total liquidity: ${analytics.get('total_liquidity', 0):,.2f}")
        print(f"   Quality score: {analytics.get('quality_score', 0)}")
    
    # For Raydium, let's try to find a token that appears in the first 100 pairs
    async with RaydiumConnector(enhanced_cache=None) as raydium:
        pairs = await raydium.get_pairs(limit=100)
        
        # Extract some token addresses from the pairs
        if pairs:
            print(f"\n☀️ RAYDIUM - Analyzing first pair for token addresses:")
            first_pair = pairs[0]
            print(f"   Pair structure keys: {list(first_pair.keys())}")
            
            # Let's try to extract token addresses from the pair
            # They might be in different fields like lp_mint, market, etc.
            potential_addresses = []
            for key, value in first_pair.items():
                if isinstance(value, str) and len(value) > 32:  # Likely an address
                    potential_addresses.append((key, value))
            
            print(f"   Potential token addresses in first pair:")
            for key, addr in potential_addresses[:3]:  # Test first 3
                print(f"     {key}: {addr}")
                
                pairs_found = await raydium.get_token_pairs(addr, search_limit=200)
                stats = await raydium.get_pool_stats(addr)
                
                print(f"       Pairs found: {len(pairs_found)}")
                print(f"       Stats found: {stats.get('found', False)}")
                print(f"       Total liquidity: ${stats.get('total_liquidity', 0):,.2f}")

async def main():
    await test_token_search_logic()
    await test_with_working_token()

if __name__ == "__main__":
    asyncio.run(main()) 