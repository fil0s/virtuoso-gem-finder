#!/usr/bin/env python3
"""
Test script to demonstrate enhanced Stage 0 debugging capabilities
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

async def test_stage0_debug():
    """Test Stage 0 debug logging with a small sample"""
    print("🧪 Testing Stage 0 Enhanced Debug Logging")
    print("=" * 50)
    
    try:
        from early_gem_detector import EarlyGemDetector
        
        # Initialize detector with debug mode
        print("🔧 Initializing detector with debug mode...")
        detector = EarlyGemDetector(debug_mode=True)
        
        print("✅ Detector initialized successfully")
        print(f"🔍 Debug mode: {detector.debug_mode}")
        
        # Test Stage 0 discovery
        print("\n🚀 Testing Stage 0 pump.fun discovery...")
        candidates = []
        
        # Run Moralis discovery with debug logging
        if hasattr(detector, '_discover_pump_fun_via_moralis'):
            print("📡 Running Moralis pump.fun discovery...")
            await detector._discover_pump_fun_via_moralis(candidates)
            
            print(f"\n📊 Results:")
            print(f"   🎯 Candidates found: {len(candidates)}")
            
            if candidates:
                print(f"   🔍 Sample candidates:")
                for i, candidate in enumerate(candidates[:3]):
                    symbol = candidate.get('symbol', 'NO_SYMBOL')
                    source = candidate.get('source', 'unknown')
                    mcap = candidate.get('market_cap', 0)
                    stage = candidate.get('pump_fun_stage', 'unknown')
                    print(f"     {i+1}. {symbol} - ${mcap:,.0f} mcap - {stage} - {source}")
            else:
                print("   ⚠️ No candidates found (may be due to rate limits or no available tokens)")
        else:
            print("❌ _discover_pump_fun_via_moralis method not found")
            
        print("\n✅ Stage 0 debug test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Stage 0 Enhanced Debug Test")
    print("This script demonstrates the new comprehensive debug logging for pump.fun discovery")
    print()
    
    try:
        asyncio.run(test_stage0_debug())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")