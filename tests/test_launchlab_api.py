#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.getcwd())

async def test_launchlab():
    try:
        from services.raydium_launchlab_api_client import RaydiumLaunchLabAPIClient
        
        client = RaydiumLaunchLabAPIClient()
        print("🎯 Testing LaunchLab API...")
        
        # Test connectivity
        connected = await client.test_api_connectivity()
        print(f"📡 API Status: {'✅ CONNECTED' if connected else '❌ FAILED'}")
        
        if connected:
            # Test getting LaunchLab tokens
            tokens = await client.get_launchlab_priority_queue()
            print(f"🔍 Found {len(tokens)} LaunchLab tokens")
            
            for token in tokens[:2]:
                print(f"   - {token['symbol']}: {token['sol_raised_current']:.1f} SOL raised")
        
        await client.cleanup()
        return connected
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_launchlab())
    print(f"\n🎯 LaunchLab API: {'WORKING ✅' if result else 'NEEDS SETUP ⚠️'}")
