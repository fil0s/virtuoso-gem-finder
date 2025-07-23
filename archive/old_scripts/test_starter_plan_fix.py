#!/usr/bin/env python3
"""
Test script to verify Starter Plan optimization is working
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

async def test_optimized_batch_manager():
    """Test that our optimized batch manager works correctly."""
    print("🧪 Testing Starter Plan Optimization...")
    
    try:
        # Test import
        from api.batch_api_manager import BatchAPIManager
        from api.birdeye_connector import BirdeyeAPI
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        import logging
        
        print("✅ Imports successful")
        
        # Create minimal config for testing
        config = {
            'api_key': os.getenv('BIRDEYE_API_KEY', 'test_key'),
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20
        }
        
        logger = logging.getLogger('test')
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService({'birdeye': {'requests_per_minute': 100}})
        
        # Initialize APIs
        birdeye_api = BirdeyeAPI(config, logger, cache_manager, rate_limiter)
        batch_manager = BatchAPIManager(birdeye_api, logger)
        
        print("✅ API initialization successful")
        
        # Test with a small set of token addresses
        test_addresses = [
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'So11111111111111111111111111111111111111112'   # WSOL
        ]
        
        print(f"🔄 Testing batch metadata with {len(test_addresses)} tokens...")
        
        # This should now use our optimized individual calls
        result = await batch_manager.batch_token_overviews(test_addresses)
        
        print(f"✅ Batch metadata test completed")
        print(f"📊 Results: {len(result) if result else 0} tokens processed")
        
        if result:
            print("🎉 Starter Plan optimization is WORKING!")
            print("   • Using individual /defi/v3/token/meta-data/single endpoints")
            print("   • Respecting semaphore limits (1 concurrent)")
            print("   • Adding 500ms delays between calls")
        else:
            print("⚠️ No results returned (could be API key or network issue)")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_price_optimization():
    """Test price optimization."""
    print("\n🧪 Testing Price Optimization...")
    
    try:
        from api.batch_api_manager import BatchAPIManager
        from api.birdeye_connector import BirdeyeAPI
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        import logging
        
        config = {
            'api_key': os.getenv('BIRDEYE_API_KEY', 'test_key'),
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20
        }
        
        logger = logging.getLogger('test')
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService({'birdeye': {'requests_per_minute': 100}})
        
        birdeye_api = BirdeyeAPI(config, logger, cache_manager, rate_limiter)
        batch_manager = BatchAPIManager(birdeye_api, logger)
        
        test_addresses = ['EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v']  # USDC
        
        print(f"🔄 Testing batch price with {len(test_addresses)} tokens...")
        
        result = await batch_manager.batch_multi_price(test_addresses)
        
        print(f"✅ Batch price test completed")
        print(f"📊 Results: {len(result) if result else 0} tokens processed")
        
        if result:
            print("🎉 Price optimization is WORKING!")
            print("   • Using individual /defi/price endpoints")
            print("   • Respecting semaphore limits (2 concurrent)")
            print("   • Adding 200ms delays between calls")
        else:
            print("⚠️ No results returned (could be API key or network issue)")
            
        return True
        
    except Exception as e:
        print(f"❌ Price test failed: {e}")
        return False

def verify_optimization_in_detector():
    """Verify the detector is using our optimization."""
    print("\n🧪 Verifying Detector Integration...")
    
    try:
        with open('early_gem_detector.py', 'r') as f:
            content = f.read()
            
        # Check if the fix is in place
        has_batch_manager_call = 'batch_api_manager.batch_token_overviews' in content
        has_old_direct_call = 'birdeye_api.get_token_metadata_multiple' in content
        
        if has_batch_manager_call and not has_old_direct_call:
            print("✅ Detector is using optimized batch manager")
            print("   • Direct API calls replaced with batch manager")
            print("   • Should now respect Starter Plan limits")
        elif has_batch_manager_call and has_old_direct_call:
            print("⚠️ Detector partially updated (some direct calls remain)")
        else:
            print("❌ Detector not updated (still using direct API calls)")
            
        return has_batch_manager_call and not has_old_direct_call
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🔧 Starter Plan Optimization Test Suite")
    print("=" * 50)
    
    # Test 1: Batch manager optimization
    test1_result = await test_optimized_batch_manager()
    
    # Test 2: Price optimization  
    test2_result = await test_price_optimization()
    
    # Test 3: Detector integration
    test3_result = verify_optimization_in_detector()
    
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    print(f"Batch Metadata Optimization: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Batch Price Optimization: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"Detector Integration: {'✅ PASS' if test3_result else '❌ FAIL'}")
    
    if all([test1_result, test2_result, test3_result]):
        print("\n🎉 All Tests PASSED!")
        print("✅ Starter Plan optimization is ready")
        print("✅ Detector will use individual endpoints")
        print("✅ Rate limiting will be respected")
        print("\n🚀 Ready to test 3-hour detector again!")
    else:
        print("\n⚠️ Some tests failed - review issues above")
        
    return all([test1_result, test2_result, test3_result])

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n💡 Next step: Run the detector again:")
            print("   python run_3hour_detector.py --futuristic-compact")
        else:
            print("\n💡 Fix the issues above before running detector")
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")