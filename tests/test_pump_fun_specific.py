#!/usr/bin/env python3
"""
Test specific pump.fun patterns and new endpoints
"""

import asyncio
import aiohttp
import json

async def test_pump_fun_endpoints():
    print("🔍 TESTING SPECIFIC PUMP.FUN ENDPOINT PATTERNS")
    print("=" * 60)
    
    # More targeted pump.fun endpoint possibilities
    endpoints = [
        ("Pump.fun Direct", "https://pump.fun/api/coins"),
        ("Pump.fun Coins Latest", "https://pump.fun/api/coins/latest"),
        ("Pump.fun New", "https://pump.fun/api/new"),
        ("Pump.fun Recent", "https://pump.fun/api/recent"),
        ("Pump.fun Board", "https://pump.fun/api/board"),
        ("Pump.fun Trending", "https://pump.fun/api/trending"),
        ("PumpPortal API", "https://api.pumpportal.fun/coins"),
        ("PumpPortal Latest", "https://api.pumpportal.fun/latest"),
        ("PumpPortal New", "https://api.pumpportal.fun/new"),
        ("Solscan Tokens", "https://public-api.solscan.io/token/list?sortBy=market_cap&direction=desc&size=20"),
        ("Helius API", "https://api.helius.xyz/v0/tokens/metadata"),
        ("Birdeye No Auth", "https://public-api.birdeye.so/public/tokenlist?sort_by=v24hUSD&sort_type=desc&offset=0&limit=50"),
    ]
    
    working = []
    
    async with aiohttp.ClientSession() as session:
        for name, url in endpoints:
            try:
                print(f"🔍 Testing {name}: {url}")
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f"   ✅ SUCCESS: Array with {len(data)} items")
                                print(f"   📋 Sample keys: {list(data[0].keys())[:5] if isinstance(data[0], dict) else 'Not dict'}")
                                working.append((name, url, data[:2]))  # Store sample
                            elif isinstance(data, dict):
                                print(f"   ✅ SUCCESS: Object with keys: {list(data.keys())[:5]}")
                                working.append((name, url, data))
                            else:
                                print(f"   ⚠️ Unexpected data type: {type(data)}")
                        except:
                            text = await response.text()
                            print(f"   📄 Non-JSON: {len(text)} chars")
                    else:
                        print(f"   ❌ HTTP {response.status}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            await asyncio.sleep(0.5)
    
    if working:
        print(f"\n✅ FOUND {len(working)} WORKING ENDPOINTS!")
        for name, url, sample in working:
            print(f"\n🔥 {name}: {url}")
            print(f"   Sample: {json.dumps(sample, indent=2)[:200]}...")
    else:
        print("\n❌ No working endpoints found")
    
    return working

if __name__ == "__main__":
    results = asyncio.run(test_pump_fun_endpoints())
