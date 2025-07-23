#!/usr/bin/env python3
"""
Test script for Raydium v3 API migration
Validates that the new v3 endpoints work with fallback to v2
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.raydium_connector import RaydiumConnector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_raydium_v3_migration():
    """Test Raydium v3 API endpoints with fallback"""
    print("🚀 Testing Raydium v3 API Migration")
    print("=" * 50)
    
    async with RaydiumConnector() as connector:
        # Test 1: Get pools
        print("\n📊 Test 1: Getting Raydium pools...")
        try:
            pools = await connector.get_pools(limit=10)
            if pools:
                print(f"✅ Successfully retrieved {len(pools)} pools")
                print(f"   Sample pool keys: {list(pools[0].keys()) if pools else []}")
            else:
                print("❌ No pools retrieved")
        except Exception as e:
            print(f"❌ Error getting pools: {e}")
        
        # Test 2: Get pairs
        print("\n💱 Test 2: Getting Raydium pairs...")
        try:
            pairs = await connector.get_pairs(limit=10)
            if pairs:
                print(f"✅ Successfully retrieved {len(pairs)} pairs")
                print(f"   Sample pair keys: {list(pairs[0].keys()) if pairs else []}")
            else:
                print("❌ No pairs retrieved")
        except Exception as e:
            print(f"❌ Error getting pairs: {e}")
        
        # Test 3: Get WSOL trending pairs 
        print("\n🌊 Test 3: Getting WSOL trending pairs...")
        try:
            wsol_pairs = await connector.get_wsol_trending_pairs(limit=5)
            if wsol_pairs:
                print(f"✅ Successfully retrieved {len(wsol_pairs)} WSOL pairs")
                for i, pair in enumerate(wsol_pairs[:2]):
                    print(f"   {i+1}. {pair.get('symbol', 'Unknown')} - Volume: ${pair.get('volume_24h', 0):,.2f}")
            else:
                print("❌ No WSOL pairs retrieved")
        except Exception as e:
            print(f"❌ Error getting WSOL pairs: {e}")
        
        # Test 4: API Statistics
        print("\n📈 Test 4: API call statistics...")
        stats = connector.get_api_call_statistics()
        print(f"   Total calls: {stats['total_calls']}")
        print(f"   Success rate: {stats['success_rate']:.2%}")
        print(f"   Average response time: {stats['average_response_time']:.2f}s")
        
        # Test 5: Direct endpoint test
        print("\n🔗 Test 5: Direct endpoint test...")
        try:
            # Test v3 endpoint directly
            direct_response = await connector._make_tracked_request(
                connector.v3_endpoints['pools'], 
                use_v2_fallback=False
            )
            if direct_response:
                print("✅ Direct v3 endpoint successful")
            else:
                print("⚠️ Direct v3 endpoint failed, fallback needed")
                
                # Test v2 fallback
                fallback_response = await connector._make_tracked_request(
                    '/pools', 
                    use_v2_fallback=True
                )
                if fallback_response:
                    print("✅ v2 fallback successful")
                else:
                    print("❌ Both v3 and v2 failed")
        except Exception as e:
            print(f"❌ Direct endpoint test error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Raydium v3 Migration Test Complete")

if __name__ == "__main__":
    asyncio.run(test_raydium_v3_migration())