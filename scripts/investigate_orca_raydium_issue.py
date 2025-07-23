#!/usr/bin/env python3
"""
Investigate Orca and Raydium No Data Issue
"""

import asyncio
import sys
import os
import json
import aiohttp
import time
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer

async def test_orca_api_directly():
    """Test Orca API endpoints directly"""
    print("🐋 Testing Orca API Directly")
    print("-" * 50)
    
    # Common Orca API endpoints
    endpoints = [
        "https://api.mainnet.orca.so/v1/whirlpool/list",
        "https://api.orca.so/v1/whirlpool/list", 
        "https://orca-api.dolphins.ai/v1/whirlpool/list",
        "https://api.orca.so/v1/whirlpools",
        "https://api.mainnet.orca.so/v1/whirlpools"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(endpoints, 1):
            print(f"\n📡 Testing endpoint {i}/5: {url}")
            try:
                async with session.get(url, timeout=10) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            print(f"   Keys: {list(data.keys())}")
                            if 'whirlpools' in data:
                                pools = data.get('whirlpools', [])
                                print(f"   Whirlpools found: {len(pools)}")
                                if pools:
                                    sample_pool = pools[0]
                                    print(f"   Sample pool keys: {list(sample_pool.keys()) if isinstance(sample_pool, dict) else 'Not dict'}")
                                    return {'working_endpoint': url, 'data': data, 'pool_count': len(pools)}
                        elif isinstance(data, list):
                            print(f"   Direct list length: {len(data)}")
                            if data:
                                print(f"   Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not dict'}")
                                return {'working_endpoint': url, 'data': data, 'pool_count': len(data)}
                    else:
                        print(f"   Error: {response.status}")
                        error_text = await response.text()
                        print(f"   Error text: {error_text[:200]}...")
                        
            except Exception as e:
                print(f"   Exception: {e}")
                
    print("❌ No working Orca endpoints found")
    return None

async def test_raydium_api_directly():
    """Test Raydium API endpoints directly"""
    print("\n⚡ Testing Raydium API Directly")
    print("-" * 50)
    
    # Common Raydium API endpoints
    endpoints = [
        "https://api.raydium.io/v2/main/pairs",
        "https://api.raydium.io/pairs",
        "https://api.raydium.io/v2/pairs",
        "https://raydium.io/api/pairs",
        "https://api-v3.raydium.io/pools/info/list"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(endpoints, 1):
            print(f"\n📡 Testing endpoint {i}/5: {url}")
            try:
                async with session.get(url, timeout=10) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            print(f"   Keys: {list(data.keys())}")
                            # Check various possible data structures
                            possible_keys = ['pairs', 'data', 'pools', 'result']
                            for key in possible_keys:
                                if key in data:
                                    pools = data[key]
                                    if isinstance(pools, list):
                                        print(f"   {key} found: {len(pools)} items")
                                        if pools:
                                            sample = pools[0]
                                            print(f"   Sample {key} keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not dict'}")
                                            return {'working_endpoint': url, 'data': data, 'pool_count': len(pools)}
                        elif isinstance(data, list):
                            print(f"   Direct list length: {len(data)}")
                            if data:
                                print(f"   Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not dict'}")
                                return {'working_endpoint': url, 'data': data, 'pool_count': len(data)}
                    else:
                        print(f"   Error: {response.status}")
                        error_text = await response.text()
                        print(f"   Error text: {error_text[:200]}...")
                        
            except Exception as e:
                print(f"   Exception: {e}")
                
    print("❌ No working Raydium endpoints found")
    return None

async def test_cross_platform_analyzer_connectors():
    """Test the actual connectors used by CrossPlatformAnalyzer"""
    print("\n🔍 Testing CrossPlatformAnalyzer Connectors")
    print("-" * 50)
    
    analyzer = CrossPlatformAnalyzer()
    
    try:
        # Get raw platform data directly
        print("📡 Calling analyzer.collect_all_data()...")
        start_time = time.time()
        platform_data = await analyzer.collect_all_data()
        end_time = time.time()
        
        print(f"⏱️ Data collection took: {end_time - start_time:.1f}s")
        print(f"📊 Platform data keys: {list(platform_data.keys())}")
        
        # Analyze each platform's data
        for platform_key, data in platform_data.items():
            print(f"\n🔍 {platform_key}:")
            print(f"   Type: {type(data)}")
            print(f"   Length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
            
            if isinstance(data, list) and data:
                sample = data[0]
                print(f"   Sample keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not dict'}")
                
                # Check for WSOL pairs specifically
                wsol_count = sum(1 for item in data if isinstance(item, dict) and item.get('is_wsol_pair', False))
                print(f"   WSOL pairs: {wsol_count}")
                
                if wsol_count > 0:
                    wsol_samples = [item for item in data if isinstance(item, dict) and item.get('is_wsol_pair', False)][:2]
                    for i, sample in enumerate(wsol_samples, 1):
                        print(f"   WSOL sample {i}: {sample.get('symbol', 'Unknown')} | {sample.get('address', 'Unknown')[:8]}...")
                        
            elif isinstance(data, dict):
                print(f"   Dict keys: {list(data.keys())}")
        
        return platform_data
        
    except Exception as e:
        print(f"❌ Error in CrossPlatformAnalyzer: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await analyzer.close()

async def investigate_specific_connectors():
    """Investigate Orca and Raydium connectors specifically"""
    print("\n🔬 Investigating Specific Connectors")
    print("-" * 50)
    
    # Test if we can import the connectors
    try:
        from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
        analyzer = CrossPlatformAnalyzer()
        
        # Check if analyzer has connector methods
        print("🔍 Checking analyzer methods...")
        methods = [method for method in dir(analyzer) if not method.startswith('_')]
        connector_methods = [method for method in methods if 'orca' in method.lower() or 'raydium' in method.lower()]
        print(f"   Connector-related methods: {connector_methods}")
        
        # Check what connectors are actually being used
        print(f"\n🔍 Analyzer attributes:")
        for attr in dir(analyzer):
            if not attr.startswith('_') and ('connector' in attr.lower() or 'orca' in attr.lower() or 'raydium' in attr.lower()):
                value = getattr(analyzer, attr, None)
                print(f"   {attr}: {type(value)} - {value}")
        
        await analyzer.close()
        
    except Exception as e:
        print(f"❌ Error investigating connectors: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run comprehensive investigation"""
    print("🔍 Investigating Orca and Raydium 'No Data' Issue")
    print("=" * 70)
    
    # Test 1: Direct API tests
    orca_result = await test_orca_api_directly()
    raydium_result = await test_raydium_api_directly()
    
    # Test 2: CrossPlatformAnalyzer test
    platform_data = await test_cross_platform_analyzer_connectors()
    
    # Test 3: Connector investigation
    await investigate_specific_connectors()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 INVESTIGATION SUMMARY")
    print("=" * 70)
    
    print(f"🐋 Orca API: {'✅ WORKING' if orca_result else '❌ NO DATA'}")
    if orca_result:
        print(f"   Working endpoint: {orca_result['working_endpoint']}")
        print(f"   Pools found: {orca_result['pool_count']}")
    
    print(f"⚡ Raydium API: {'✅ WORKING' if raydium_result else '❌ NO DATA'}")
    if raydium_result:
        print(f"   Working endpoint: {raydium_result['working_endpoint']}")
        print(f"   Pools found: {raydium_result['pool_count']}")
    
    if platform_data:
        orca_data = [k for k in platform_data.keys() if 'orca' in k.lower()]
        raydium_data = [k for k in platform_data.keys() if 'raydium' in k.lower()]
        
        print(f"🔗 CrossPlatformAnalyzer:")
        print(f"   Orca data sources: {orca_data}")
        print(f"   Raydium data sources: {raydium_data}")
        
        for source in orca_data + raydium_data:
            data = platform_data[source]
            count = len(data) if isinstance(data, list) else 0
            print(f"   {source}: {count} items")
    
    # Save detailed results
    timestamp = int(time.time())
    results_file = f"orca_raydium_investigation_{timestamp}.json"
    
    investigation_results = {
        'timestamp': timestamp,
        'orca_api_result': orca_result,
        'raydium_api_result': raydium_result,
        'platform_data_summary': {
            k: {
                'type': str(type(v)),
                'length': len(v) if isinstance(v, (list, dict)) else None,
                'sample_keys': list(v[0].keys()) if isinstance(v, list) and v and isinstance(v[0], dict) else None
            }
            for k, v in (platform_data or {}).items()
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(investigation_results, f, indent=2, default=str)
    
    print(f"\n📁 Investigation results saved to: {results_file}")
    print("\n🎯 Next steps:")
    
    if not orca_result:
        print("   • Check Orca API documentation for correct endpoints")
        print("   • Verify if Orca API requires authentication")
        print("   • Check if Orca API is currently operational")
    
    if not raydium_result:
        print("   • Check Raydium API documentation for correct endpoints")
        print("   • Verify if Raydium API requires authentication")
        print("   • Check if Raydium API is currently operational")
    
    if not (orca_result or raydium_result):
        print("   • Consider using alternative data sources")
        print("   • Check if our network/firewall is blocking these APIs")
        print("   • Verify if rate limiting is affecting multiple requests")

if __name__ == "__main__":
    asyncio.run(main()) 