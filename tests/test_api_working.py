#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.getcwd())

async def test_api():
    try:
        from services.pump_fun_api_client import PumpFunAPIClient
        client = PumpFunAPIClient()
        tokens = await client.get_latest_tokens(limit=5)
        print(f"🔥 SUCCESS: {len(tokens)} tokens fetched from pump.fun API")
        
        if tokens:
            for token in tokens[:2]:
                print(f"   - {token.get('symbol', 'UNKNOWN')}: ${token.get('market_cap', 0):,.0f}")
        
        await client.cleanup()
        return len(tokens) > 0
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_api())
    print(f"\n🎯 API Status: {'WORKING ✅' if result else 'BROKEN ❌'}")
