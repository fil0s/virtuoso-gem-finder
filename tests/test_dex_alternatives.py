#!/usr/bin/env python3
"""
Test DEX and Solana ecosystem APIs as pump.fun alternatives
"""

import asyncio
import aiohttp
import json

async def test_dex_apis():
    print("🔍 TESTING DEX AND SOLANA ECOSYSTEM APIs")
    print("=" * 60)
    
    # DEX and Solana ecosystem endpoints
    endpoints = [
        ("DexScreener Latest", "https://api.dexscreener.com/latest/dex/pairs/solana"),
        ("DexScreener Search", "https://api.dexscreener.com/latest/dex/search/?q=solana"),
        ("Raydium Pairs", "https://api.raydium.io/v2/sdk/liquidity/mainnet.json"),
        ("Jupiter Price", "https://price.jup.ag/v6/price?ids=So11111111111111111111111111111111111111112"),
        ("Jupiter Quote SOL", "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000000"),
        ("Solana Beach", "https://api.solanabeach.io/v1/tokens/latest"),
        ("Orca Pools", "https://api.orca.so/v1/pools/So11111111111111111111111111111111111111112"),
        ("Magic Eden Stats", "https://api-mainnet.magiceden.dev/v2/collections/stats"),
        ("Coingecko New", "https://api.coingecko.com/api/v3/coins/list?include_platform=true"),
        ("Solscan Token Meta", "https://api.solscan.io/token/meta?token=So11111111111111111111111111111111111111112"),
    ]
    
    working = []
    
    async with aiohttp.ClientSession() as session:
        for name, url in endpoints:
            try:
                print(f"🔍 Testing {name}: {url}")
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f"   ✅ SUCCESS: Array with {len(data)} items")
                                sample_keys = list(data[0].keys())[:5] if isinstance(data[0], dict) else []
                                print(f"   📋 Sample keys: {sample_keys}")
                                working.append((name, url, sample_keys, len(data)))
                            elif isinstance(data, dict):
                                keys = list(data.keys())[:5]
                                print(f"   ✅ SUCCESS: Object with keys: {keys}")
                                working.append((name, url, keys, 1))
                            else:
                                print(f"   ⚠️ Unexpected data type: {type(data)}")
                        except Exception as json_error:
                            text = await response.text()
                            print(f"   📄 Non-JSON: {len(text)} chars - {str(json_error)[:50]}")
                    else:
                        print(f"   ❌ HTTP {response.status}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
            
            await asyncio.sleep(1)  # More conservative rate limiting
    
    if working:
        print(f"\n✅ FOUND {len(working)} WORKING APIs!")
        for name, url, keys, count in working:
            print(f"\n🔥 {name}")
            print(f"   URL: {url}")
            print(f"   Data: {count} items, keys: {keys}")
        
        # Recommend best alternative
        best = None
        for name, url, keys, count in working:
            if any(key in ['pairs', 'tokens', 'symbol', 'address'] for key in keys):
                best = (name, url)
                break
        
        if best:
            print(f"\n🎯 RECOMMENDED PUMP.FUN REPLACEMENT:")
            print(f"   API: {best[0]}")
            print(f"   URL: {best[1]}")
            print(f"   Reason: Contains token/pair data suitable for discovery")
    else:
        print("\n❌ No suitable alternatives found")
    
    return working

if __name__ == "__main__":
    results = asyncio.run(test_dex_apis())
