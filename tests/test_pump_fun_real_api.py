#!/usr/bin/env python3
"""
🧪 Test Real Pump.fun API Client
"""

import asyncio
import sys
import os
sys.path.append(os.getcwd())

async def test_pump_fun_api():
    print("🧪 Testing REAL Pump.fun API Client")
    print("=" * 50)
    
    try:
        from services.pump_fun_api_client import PumpFunAPIClient
        
        # Initialize client
        client = PumpFunAPIClient()
        print("✅ API client initialized")
        
        # Test fetching tokens
        print("\n🔍 Fetching latest tokens...")
        tokens = await client.get_latest_tokens(limit=10)
        
        print(f"📊 Results: {len(tokens)} tokens fetched")
        
        if tokens:
            print("\n🔥 Sample tokens:")
            for i, token in enumerate(tokens[:3]):
                symbol = token.get('symbol', 'UNKNOWN')
                market_cap = token.get('market_cap', 0)
                age = token.get('estimated_age_minutes', 'unknown')
                print(f"   {i+1}. {symbol}: ${market_cap:,.0f} MC, {age} min old")
            
            print(f"\n✅ SUCCESS: Pump.fun API is WORKING!")
            print(f"   📡 Base URL: {client.BASE_URL}")
            print(f"   🔢 API calls made: {client.api_calls_made}")
            print(f"   🎯 Tokens discovered: {client.tokens_discovered}")
            
        else:
            print("⚠️ No tokens returned - API may have issues")
            
        # Cleanup
        await client.cleanup()
        return len(tokens) > 0
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

async def test_early_gem_detector():
    print("\n\n🧪 Testing Early Gem Detector with Real API")
    print("=" * 50)
    
    try:
        from scripts.early_gem_detector import EarlyGemDetector
        
        # Initialize detector
        detector = EarlyGemDetector()
        
        # Test pump.fun discovery
        print("🔍 Testing pump.fun Stage 0 discovery...")
        pump_tokens = await detector._discover_pump_fun_stage0()
        
        print(f"📊 Results: {len(pump_tokens)} Stage 0 candidates")
        
        if pump_tokens:
            print("🔥 Stage 0 candidates found:")
            for token in pump_tokens[:2]:
                symbol = token.get('symbol', 'UNKNOWN')
                mc = token.get('market_cap', 0)
                age = token.get('estimated_age_minutes', 'unknown')
                source = token.get('source', 'unknown')
                print(f"   - {symbol}: ${mc:,.0f}, {age}min, from {source}")
            
            print("✅ SUCCESS: Early Gem Detector is using REAL pump.fun API!")
        else:
            print("⚠️ No Stage 0 candidates - may need better filtering")
            
        await detector.cleanup()
        return len(pump_tokens) > 0
        
    except Exception as e:
        print(f"❌ Early Gem Detector test failed: {e}")
        return False

async def main():
    print("🚀 COMPREHENSIVE PUMP.FUN API TEST")
    print("Testing both API client and Early Gem Detector integration")
    print()
    
    # Test 1: API Client
    api_works = await test_pump_fun_api()
    
    # Test 2: Early Gem Detector
    detector_works = await test_early_gem_detector()
    
    print("\n\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"🔥 Pump.fun API Client: {'✅ WORKING' if api_works else '❌ FAILED'}")
    print(f"💎 Early Gem Detector: {'✅ WORKING' if detector_works else '❌ FAILED'}")
    
    if api_works and detector_works:
        print("\n🎉 SUCCESS: Pump.fun integration is NOW FULLY FUNCTIONAL!")
        print("   The early gem detector will now find REAL tokens!")
    else:
        print("\n⚠️ Some components still need fixes")

if __name__ == "__main__":
    asyncio.run(main()) 