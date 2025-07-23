#!/usr/bin/env python3
"""
Investigate Orca and Raydium API structures and endpoints
"""

import asyncio
import aiohttp
import json

async def investigate_api_structures():
    print('🔍 INVESTIGATING API DATA STRUCTURES')
    print('=' * 60)
    
    async with aiohttp.ClientSession() as session:
        # Investigate Orca structure more deeply
        print('\n🌊 ORCA API DEEP DIVE:')
        try:
            async with session.get('https://api.orca.so/pools', timeout=30) as response:
                if response.status == 200:
                    pools = await response.json()
                    print(f'Total pools: {len(pools)}')
                    
                    # Look at different pool types
                    pool_names = [p.get('name', 'Unknown') for p in pools]
                    print(f'Sample pool names: {pool_names[:10]}')
                    
                    # Check what tokens are in pools
                    mint_accounts = set()
                    for pool in pools:
                        if 'mint_account' in pool:
                            mint_accounts.add(pool['mint_account'])
                    
                    print(f'Unique mint accounts found: {len(mint_accounts)}')
                    print(f'Sample mint accounts: {list(mint_accounts)[:5]}')
                    
                    # Look for any pools with high volume
                    high_volume_pools = [p for p in pools if p.get('volume_24h', 0) > 1000]
                    print(f'High volume pools (>1000): {len(high_volume_pools)}')
                    
                    if high_volume_pools:
                        top_pool = max(high_volume_pools, key=lambda x: x.get('volume_24h', 0))
                        print(f'Top volume pool: {top_pool.get("name")} - ${top_pool.get("volume_24h", 0):,.2f}')
                        
        except Exception as e:
            print(f'Error: {e}')
        
        # Investigate Raydium structure
        print('\n⚡ RAYDIUM API DEEP DIVE:')
        try:
            async with session.get('https://api.raydium.io/pools', timeout=60) as response:
                if response.status == 200:
                    pools = await response.json()
                    print(f'Total pools: {len(pools)}')
                    
                    # Look at different pool types
                    identifiers = [p.get('identifier', 'Unknown') for p in pools[:20]]
                    print(f'Sample identifiers: {identifiers}')
                    
                    # Check token-id field
                    token_ids = set()
                    for pool in pools[:10000]:  # Sample first 10k
                        if 'token-id' in pool:
                            token_ids.add(pool['token-id'])
                    
                    print(f'Unique token IDs found (sample): {len(token_ids)}')
                    print(f'Sample token IDs: {list(token_ids)[:5]}')
                    
                    # Look for high liquidity pools
                    high_liquidity = [p for p in pools[:10000] if p.get('liquidity_locked', 0) > 100000]
                    print(f'High liquidity pools (>$100k) in sample: {len(high_liquidity)}')
                    
                    if high_liquidity:
                        top_pool = max(high_liquidity, key=lambda x: x.get('liquidity_locked', 0))
                        print(f'Top liquidity pool: {top_pool.get("identifier")} - ${top_pool.get("liquidity_locked", 0):,.2f}')
                        
                    # Check if there are other fields we missed
                    all_keys = set()
                    for pool in pools[:1000]:
                        all_keys.update(pool.keys())
                    print(f'All fields found in Raydium pools: {sorted(all_keys)}')
                    
        except Exception as e:
            print(f'Error: {e}')
        
        # Test other potential endpoints
        print('\n🔬 TESTING OTHER ENDPOINTS:')
        test_endpoints = [
            'https://api.orca.so/whirlpools',
            'https://api.orca.so/v1/whirlpools',
            'https://api.orca.so/tokens',
            'https://api.raydium.io/tokens',
            'https://api.raydium.io/v1/tokens',
            'https://api.raydium.io/pairs'
        ]
        
        for endpoint in test_endpoints:
            try:
                async with session.get(endpoint, timeout=10) as response:
                    print(f'{endpoint} -> Status: {response.status}')
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list):
                                print(f'  Returns list with {len(data)} items')
                                if data:
                                    print(f'  Sample keys: {list(data[0].keys()) if isinstance(data[0], dict) else "Not dict"}')
                            elif isinstance(data, dict):
                                print(f'  Returns dict with keys: {list(data.keys())}')
                        except:
                            text = await response.text()
                            print(f'  Returns text: {len(text)} chars')
            except Exception as e:
                print(f'{endpoint} -> Error: {type(e).__name__}')

if __name__ == "__main__":
    asyncio.run(investigate_api_structures()) 