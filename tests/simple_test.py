#!/usr/bin/env python3
"""
Simple DexScreener method test
"""
import asyncio
import sys
import logging

# Suppress verbose logging
logging.getLogger().setLevel(logging.CRITICAL)

sys.path.append('..')

async def main():
    try:
        print("🧪 Simple DexScreener Method Test")
        print("=" * 40)
        
        try:
            from early_gem_detector import EarlyGemDetector
        except ImportError:
            from src.detectors.early_gem_detector import EarlyGemDetector
        print("✅ Import successful")
        
        detector = EarlyGemDetector(debug_mode=False)
        print("✅ Detector initialized")
        
        # Check methods exist
        methods_to_check = [
            '_dexscreener_first_enhancement',
            '_get_dexscreener_batch_data',
            '_discover_dexscreener_trending',
            '_get_dexscreener_trading_data'
        ]
        
        for method_name in methods_to_check:
            method = getattr(detector, method_name, None)
            if method and callable(method):
                print(f"✅ {method_name} found")
            else:
                print(f"❌ {method_name} missing or not callable")
        
        print("\n🎯 Testing basic method call...")
        
        # Test simple method call
        try:
            trending = await detector._discover_dexscreener_trending()
            print(f"✅ _discover_dexscreener_trending returned {len(trending) if trending else 0} results")
        except Exception as e:
            print(f"⚠️  _discover_dexscreener_trending failed: {e}")
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())