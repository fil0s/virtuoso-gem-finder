#!/usr/bin/env python3
"""
🔍 PUMP PORTAL API DISCOVERY
Find actual working endpoints since api.pumpportal.fun doesn't exist
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def discover_pump_portal_apis():
    print("🔍 PUMP PORTAL API DISCOVERY")
    print("=" * 50)
    print("The DNS error means 'api.pumpportal.fun' doesn't exist")
    print("Testing main domain 'pumpportal.fun' with different API paths...")
    print()
    
    # Since api.pumpportal.fun doesn't exist, test main domain
    base_url = "https://pumpportal.fun"
    
    # API path patterns to test
    api_paths = [
        "/api/v1/coins", "/api/coins", "/api/tokens", "/api/latest",
        "/api/trending", "/api/stats", "/api/data", "/api/live",
        "/coins", "/tokens", "/latest", "/data", "/live",
        "/pump/api/coins", "/pump/coins", "/v1/coins"
    ]
    
    working = []
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
        for path in api_paths:
            url = f"{base_url}{path}"
            try:
                print(f"🔍 {path:<20}", end="", flush=True)
                async with session.get(url) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list) and len(data) > 0:
                                print(f" ✅ Array[{len(data)}] - WORKING!")
                                working.append(url)
                            elif isinstance(data, dict) and len(data) > 0:
                                print(f" ✅ Object - WORKING!")
                                working.append(url)
                            else:
                                print(f" ⚠️ Empty")
                        except:
                            print(f" 📄 Non-JSON")
                    else:
                        print(f" ❌ {response.status}")
            except Exception as e:
                print(f" ❌ Error")
            await asyncio.sleep(0.2)
    
    print(f"\n✅ Found {len(working)} working endpoints:")
    for url in working:
        print(f"🌟 {url}")
    
    return working

if __name__ == "__main__":
    asyncio.run(discover_pump_portal_apis())
