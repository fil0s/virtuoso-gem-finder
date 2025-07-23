#!/usr/bin/env python3
"""
Test actual pump.fun related APIs since pumpportal doesn't have APIs
"""

import asyncio
import aiohttp

async def test_pump_fun_apis():
    print("🔍 TESTING ACTUAL PUMP.FUN APIs")
    print("=" * 40)
    
    # Real pump.fun related endpoints
    endpoints = [
        ("Pump.fun Direct", "https://pump.fun/api/coins"),
        ("Frontend API", "https://frontend-api.pump.fun/coins"),
        ("Client API", "https://client-api.pump.fun/coins"), 
        ("Client API v2", "https://client-api-v2.pump.fun/coins"),
        ("Pump Portal Alt", "https://pumpportal.fun"),
        ("Pump Fun Board", "https://pump.fun/board"),
    ]
    
    working = []
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
        for name, url in endpoints:
            try:
                print(f"🔍 {name:<20}", end="", flush=True)
                async with session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            try:
                                data = await response.json()
                                if isinstance(data, list) and len(data) > 0:
                                    print(f" ✅ JSON Array[{len(data)}]")
                                    working.append((name, url))
                                elif isinstance(data, dict):
                                    print(f" ✅ JSON Object")
                                    working.append((name, url))
                                else:
                                    print(f" ⚠️ Empty JSON")
                            except:
                                print(f" ⚠️ Invalid JSON")
                        else:
                            print(f" 📄 HTML ({response.status})")
                    else:
                        print(f" ❌ {response.status}")
            except Exception as e:
                print(f" ❌ DNS/Connection Error")
            await asyncio.sleep(0.3)
    
    print(f"\n✅ Working pump APIs: {len(working)}")
    for name, url in working:
        print(f"🌟 {name}: {url}")
    
    return working

if __name__ == "__main__":
    asyncio.run(test_pump_fun_apis())
