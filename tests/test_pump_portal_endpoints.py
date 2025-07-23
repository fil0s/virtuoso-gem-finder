#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE PUMP PORTAL ENDPOINTS TEST
Tests all known and potential Pump Portal API endpoints for live token data
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_pump_portal():
    print("🔥 COMPREHENSIVE PUMP PORTAL ENDPOINTS TEST")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Known endpoints from codebase + additional discovery
    endpoints = [
        # From existing codebase
        ("API Coins", "https://api.pumpportal.fun/coins"),
        ("API Latest", "https://api.pumpportal.fun/latest"), 
        ("API New", "https://api.pumpportal.fun/new"),
        ("Trades by Token", "https://pumpportal.fun/api/trades-by-token/"),
        ("API Data", "https://pumpportal.fun/api/data"),
        
        # Additional common patterns
        ("API Tokens", "https://api.pumpportal.fun/tokens"),
        ("API Trending", "https://api.pumpportal.fun/trending"),
        ("API Recent", "https://api.pumpportal.fun/recent"),
        ("API Stats", "https://api.pumpportal.fun/stats"),
        ("API Markets", "https://api.pumpportal.fun/markets"),
        ("API Volume", "https://api.pumpportal.fun/volume"),
        ("API Live", "https://api.pumpportal.fun/live"),
        ("API Search", "https://api.pumpportal.fun/search"),
        
        # Alternative base URLs
        ("Backend Coins", "https://backend.pumpportal.fun/api/coins"),
        ("Data API", "https://data.pumpportal.fun/api/latest"),
        ("Live API", "https://live.pumpportal.fun/api/tokens")
    ]
    
    working = []
    tested_count = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
        for name, url in endpoints:
            tested_count += 1
            try:
                print(f"🔍 Testing: {name}")
                print(f"   📡 URL: {url}")
                
                start_time = time.time()
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    status = response.status
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', 'unknown')
                    
                    print(f"   📊 Status: {status}")
                    print(f"   ⏱️ Response Time: {response_time:.2f}s")
                    print(f"   📋 Content-Type: {content_type}")
                    print(f"   📏 Content-Length: {content_length}")
                    
                    if status == 200:
                        try:
                            if 'application/json' in content_type:
                                data = await response.json()
                                
                                if isinstance(data, list):
                                    print(f"   ✅ SUCCESS: Array with {len(data)} items")
                                    if data and isinstance(data[0], dict):
                                        keys = list(data[0].keys())[:7]
                                        print(f"   🔑 Sample keys: {keys}")
                                        # Show sample data for first item
                                        sample = {k: data[0][k] for k in list(data[0].keys())[:3]}
                                        print(f"   💎 Sample data: {sample}")
                                    working.append({
                                        'name': name,
                                        'url': url,
                                        'type': f'array[{len(data)}]',
                                        'keys': keys if data else [],
                                        'response_time': response_time
                                    })
                                    
                                elif isinstance(data, dict):
                                    keys = list(data.keys())[:7]
                                    print(f"   ✅ SUCCESS: Object with {len(data)} keys")
                                    print(f"   🔑 Keys: {keys}")
                                    # Show sample of top-level data
                                    sample = {k: str(data[k])[:50] for k in list(data.keys())[:3]}
                                    print(f"   💎 Sample data: {sample}")
                                    working.append({
                                        'name': name,
                                        'url': url,
                                        'type': f'object[{len(data)}]',
                                        'keys': keys,
                                        'response_time': response_time
                                    })
                                    
                                else:
                                    print(f"   ⚠️ Unexpected data type: {type(data)}")
                                    
                            else:
                                text = await response.text()
                                print(f"   📄 Non-JSON response ({len(text)} chars)")
                                if len(text) < 300:
                                    print(f"   👀 Preview: {text[:150]}...")
                                    
                        except json.JSONDecodeError as e:
                            text = await response.text()
                            print(f"   ⚠️ Invalid JSON: {e}")
                            print(f"   📄 Content length: {len(text)} chars")
                            
                    elif status == 404:
                        print(f"   ❌ Not Found (404)")
                    elif status == 403:
                        print(f"   ❌ Forbidden (403)")
                    elif status == 503:
                        print(f"   ❌ Service Unavailable (503)")
                    elif status == 429:
                        print(f"   ⏰ Rate Limited (429)")
                    elif status == 500:
                        print(f"   ❌ Internal Server Error (500)")
                    else:
                        print(f"   ❌ HTTP {status}")
                        
            except asyncio.TimeoutError:
                print(f"   ⏰ Request timed out")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()  # Separator
            await asyncio.sleep(0.8)  # Rate limiting
    
    # Results Analysis
    print("=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"🔍 Total endpoints tested: {tested_count}")
    print(f"✅ Working endpoints found: {len(working)}")
    print(f"📈 Success rate: {len(working)/tested_count*100:.1f}%")
    
    if working:
        print(f"\n🔥 WORKING PUMP PORTAL ENDPOINTS:")
        print("-" * 50)
        
        # Sort by response time for performance ranking
        working_sorted = sorted(working, key=lambda x: x['response_time'])
        
        for i, endpoint in enumerate(working_sorted, 1):
            print(f"\n{i}. 🌟 {endpoint['name']}")
            print(f"   📡 URL: {endpoint['url']}")
            print(f"   📊 Response: {endpoint['type']}")
            print(f"   ⚡ Speed: {endpoint['response_time']:.2f}s")
            if endpoint['keys']:
                print(f"   🔑 Available Fields: {endpoint['keys']}")
        
        # Performance Analysis
        avg_response_time = sum(ep['response_time'] for ep in working) / len(working)
        fastest = min(working, key=lambda x: x['response_time'])
        
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print(f"   📊 Average Response Time: {avg_response_time:.2f}s")
        print(f"   🏆 Fastest Endpoint: {fastest['name']} ({fastest['response_time']:.2f}s)")
        
        # Integration Recommendations
        print(f"\n🚀 INTEGRATION RECOMMENDATIONS:")
        print("-" * 40)
        
        # Find best endpoint for tokens
        token_endpoints = [ep for ep in working if 'array' in ep['type'] and len(ep['keys']) > 3]
        
        if token_endpoints:
            best = token_endpoints[0]
            print(f"✅ Recommended for Token Discovery:")
            print(f"   🎯 Endpoint: {best['name']}")
            print(f"   📡 URL: {best['url']}")
            print(f"   ⚡ Response Time: {best['response_time']:.2f}s")
            print(f"   🔑 Data Fields: {len(best['keys'])} fields available")
            
            print(f"\n💡 Integration Steps:")
            print(f"   1. Add to services/pump_fun_api_client.py")
            print(f"   2. Implement rate limiting (0.8s intervals)")
            print(f"   3. Add error handling for 503/429 responses")
            print(f"   4. Test data quality and consistency")
            
        # WebSocket suggestion
        print(f"\n🌐 WebSocket Testing Recommended:")
        print(f"   📡 Test: wss://pumpportal.fun/api/data")
        print(f"   🔄 For real-time trade streams")
        
    else:
        print(f"\n❌ NO WORKING ENDPOINTS FOUND")
        print(f"   • All Pump Portal endpoints are currently unavailable")
        print(f"   • API may be experiencing downtime or maintenance")
        print(f"   • Check official Pump Portal documentation")
        print(f"   • Consider alternative data sources")
    
    return working

async def test_pump_portal_websocket():
    """Test Pump Portal WebSocket endpoints"""
    print(f"\n🌐 TESTING PUMP PORTAL WEBSOCKET")
    print("-" * 40)
    
    ws_url = "wss://pumpportal.fun/api/data"
    
    try:
        import websockets
        print(f"🔌 Testing WebSocket: {ws_url}")
        
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print(f"   ✅ Connected successfully!")
            
            # Try to receive messages
            try:
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"   📨 Message {i+1}: {message[:100]}...")
                    if i == 0:  # Parse first message structure
                        try:
                            data = json.loads(message)
                            if isinstance(data, dict):
                                print(f"   🔑 Message keys: {list(data.keys())}")
                        except:
                            pass
                    
            except asyncio.TimeoutError:
                print(f"   ⏰ No messages received within timeout")
                
        return True
        
    except ImportError:
        print("⚠️ websockets package not available")
        print("   Install with: pip install websockets")
        return False
    except Exception as e:
        print(f"   ❌ WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        try:
            # Test HTTP endpoints
            working_endpoints = await test_pump_portal()
            
            # Test WebSocket if HTTP endpoints work
            if working_endpoints:
                ws_success = await test_pump_portal_websocket()
                
                if ws_success:
                    print(f"\n🎉 PUMP PORTAL INTEGRATION READY!")
                    print(f"   📡 HTTP endpoints: {len(working_endpoints)} working")
                    print(f"   🌐 WebSocket: Available")
                else:
                    print(f"\n✅ PUMP PORTAL PARTIAL INTEGRATION")
                    print(f"   📡 HTTP endpoints: {len(working_endpoints)} working")
                    print(f"   🌐 WebSocket: Not available")
            
            print(f"\n✅ Pump Portal testing completed!")
            
        except KeyboardInterrupt:
            print(f"\n⏹️ Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
    
    asyncio.run(main()) 