#!/usr/bin/env python3
"""
Test correct pump.fun API endpoints based on official patterns
"""

import asyncio
import aiohttp
import json

async def test_pump_fun_official_endpoints():
    print("🔍 TESTING OFFICIAL PUMP.FUN API PATTERNS")
    print("=" * 60)
    
    # Based on the official docs, let's try more methodical endpoint patterns
    base_domains = [
        "https://frontend-api.pump.fun",
        "https://api.pump.fun", 
        "https://client-api.pump.fun",
        "https://backend-api.pump.fun",
        "https://data-api.pump.fun",
        "https://public-api.pump.fun"
    ]
    
    endpoints = [
        "/coins",
        "/coins/latest", 
        "/coins/new",
        "/coins/trending",
        "/tokens",
        "/tokens/latest",
        "/tokens/new",
        "/board",
        "/recent",
        "/api/coins",
        "/api/tokens",
        "/api/latest"
    ]
    
    working_endpoints = []
    
    async with aiohttp.ClientSession() as session:
        for base in base_domains:
            print(f"\n🔍 Testing base domain: {base}")
            
            for endpoint in endpoints:
                url = f"{base}{endpoint}"
                try:
                    async with session.get(url, timeout=10) as response:
                        print(f"   {endpoint}: HTTP {response.status}", end="")
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                if isinstance(data, list) and len(data) > 0:
                                    print(f" ✅ Array({len(data)} items)")
                                    working_endpoints.append((base, endpoint, len(data)))
                                    
                                    # Show sample data structure
                                    if isinstance(data[0], dict):
                                        keys = list(data[0].keys())[:5]
                                        print(f"      Sample keys: {keys}")
                                elif isinstance(data, dict):
                                    print(f" ✅ Object({len(data.keys())} keys)")
                                    working_endpoints.append((base, endpoint, f"dict-{len(data.keys())}"))
                                else:
                                    print(f" ⚠️ Unexpected type: {type(data)}")
                            except:
                                text = await response.text()
                                print(f" 📄 Non-JSON ({len(text)} chars)")
                        elif response.status == 503:
                            print(" ❌ Service Unavailable")
                        elif response.status == 404:
                            print(" ❌ Not Found")
                        else:
                            print(f" ❌ Error {response.status}")
                            
                except asyncio.TimeoutError:
                    print(f"   {endpoint}: ⏰ Timeout")
                except Exception as e:
                    print(f"   {endpoint}: ❌ {str(e)[:30]}...")
                
                await asyncio.sleep(0.2)  # Rate limiting
    
    if working_endpoints:
        print(f"\n✅ FOUND {len(working_endpoints)} WORKING ENDPOINTS!")
        for base, endpoint, info in working_endpoints:
            print(f"🔥 {base}{endpoint} - {info}")
        
        # Recommend the best one
        best = working_endpoints[0]
        print(f"\n🎯 RECOMMENDED REPLACEMENT:")
        print(f"   BASE_URL: '{best[0]}'")
        print(f"   Endpoint: '{best[1]}'")
        print(f"   Full URL: {best[0]}{best[1]}")
    else:
        print(f"\n❌ NO WORKING PUMP.FUN ENDPOINTS FOUND")
        print("   All tested endpoints are currently unavailable")
        print("   pump.fun API may be experiencing downtime")
    
    return working_endpoints

if __name__ == "__main__":
    results = asyncio.run(test_pump_fun_official_endpoints())
