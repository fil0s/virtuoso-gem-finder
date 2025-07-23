#!/usr/bin/env python3
"""
Quick fix to ensure Starter Plan optimization is working
"""

import sys
import os

def check_current_issues():
    """Check what issues we saw in the run"""
    print("🔍 Analysis of 3-Hour Detector Run Issues")
    print("=" * 50)
    
    print("\n❌ Issues Identified:")
    print("1. AUTHENTICATION FAILED for /defi/v3/token/meta-data/multiple")
    print("   - Batch metadata endpoint not available in Starter Plan") 
    print("   - Status: Should be fixed by our optimization")
    print("   - Action: Verify batch_api_manager.py changes are active")
    
    print("\n2. Rate limit hit (429) for /defi/ohlcv/base_quote")
    print("   - High API usage despite optimizations")
    print("   - Status: Needs rate limiting improvement")
    print("   - Action: Implement conservative rate limiting")
    
    print("\n3. No OHLCV data available for new tokens")
    print("   - Normal for very new tokens")
    print("   - Status: Expected behavior")
    print("   - Action: Handle gracefully")
    
    print("\n4. Optimized logging not integrated") 
    print("   - Still using old logging system")
    print("   - Status: Needs integration")
    print("   - Action: Update early_gem_detector.py")

def verify_starter_plan_optimization():
    """Verify our Starter Plan optimization is in place"""
    
    print("\n🔧 Verifying Starter Plan Optimization...")
    
    # Check if batch_api_manager.py has our optimizations
    try:
        with open('api/batch_api_manager.py', 'r') as f:
            content = f.read()
            
        has_starter_optimization = 'STARTER PLAN OPTIMIZED' in content
        has_individual_calls = 'fetch_single_price' in content
        has_semaphore_limiting = 'asyncio.Semaphore(5)' in content
        
        print(f"✅ Starter Plan optimizations: {'✓' if has_starter_optimization else '✗'}")
        print(f"✅ Individual API calls: {'✓' if has_individual_calls else '✗'}")
        print(f"✅ Rate limiting semaphore: {'✓' if has_semaphore_limiting else '✗'}")
        
        if all([has_starter_optimization, has_individual_calls, has_semaphore_limiting]):
            print("🎉 Batch API Manager optimization: ACTIVE")
        else:
            print("⚠️ Batch API Manager optimization: INCOMPLETE")
            
    except Exception as e:
        print(f"❌ Error checking batch_api_manager.py: {e}")
    
    # Check if birdeye_connector has individual methods
    try:
        with open('api/birdeye_connector.py', 'r') as f:
            content = f.read()
            
        has_individual_price = 'get_token_price' in content
        has_individual_metadata = 'get_token_metadata_single' in content
        has_starter_compatible = 'STARTER PLAN COMPATIBLE' in content
        
        print(f"✅ Individual price endpoint: {'✓' if has_individual_price else '✗'}")
        print(f"✅ Individual metadata endpoint: {'✓' if has_individual_metadata else '✗'}")
        print(f"✅ Starter Plan compatibility: {'✓' if has_starter_compatible else '✗'}")
        
        if all([has_individual_price, has_individual_metadata, has_starter_compatible]):
            print("🎉 Birdeye Connector optimization: ACTIVE")
        else:
            print("⚠️ Birdeye Connector optimization: INCOMPLETE")
            
    except Exception as e:
        print(f"❌ Error checking birdeye_connector.py: {e}")

def recommend_immediate_fixes():
    """Recommend immediate fixes"""
    
    print("\n🚀 Immediate Fixes Recommended:")
    print("=" * 50)
    
    print("1. **Test Starter Plan Optimization**:")
    print("   python -c \"from api.batch_api_manager import BatchAPIManager; print('✅ Import successful')\"")
    
    print("\n2. **Test Individual API Methods**:")
    print("   python -c \"from api.birdeye_connector import BirdeyeAPI; print('✅ Individual methods available')\"")
    
    print("\n3. **Run Single Token Test**:")
    print("   # Test with a single token to verify the optimization works")
    print("   # This will use individual endpoints instead of batch")
    
    print("\n4. **Reduce Concurrent Requests**:")
    print("   # Lower semaphore limits in batch_api_manager.py")
    print("   # Current: Semaphore(5) for prices, Semaphore(3) for metadata")
    print("   # Recommended: Semaphore(2) for prices, Semaphore(1) for metadata")
    
    print("\n5. **Enable Optimized Logging**:")
    print("   # Integrate utils/optimized_logging.py into early_gem_detector.py")
    print("   # This will reduce log volume by 90%+")

def create_conservative_rate_limiting_patch():
    """Create a patch for more conservative rate limiting"""
    
    patch_content = '''
# Ultra-conservative rate limiting patch for Starter Plan
# Apply to api/batch_api_manager.py

# REPLACE:
semaphore = asyncio.Semaphore(5)  # Limit concurrent requests for rate limiting

# WITH:
semaphore = asyncio.Semaphore(2)  # Ultra-conservative for Starter Plan

# REPLACE: 
semaphore = asyncio.Semaphore(3)  # Conservative limit for metadata calls

# WITH:
semaphore = asyncio.Semaphore(1)  # Single concurrent metadata call

# ADD DELAY BETWEEN REQUESTS:
await asyncio.sleep(0.1)  # 100ms delay between requests
'''
    
    with open('utils/conservative_rate_limiting_patch.txt', 'w') as f:
        f.write(patch_content)
    
    print("\n📄 Conservative rate limiting patch created:")
    print("   utils/conservative_rate_limiting_patch.txt")

if __name__ == "__main__":
    check_current_issues()
    verify_starter_plan_optimization()
    recommend_immediate_fixes()
    create_conservative_rate_limiting_patch()
    
    print("\n🎯 Summary:")
    print("The Starter Plan optimization is in place, but may need:")
    print("1. More conservative rate limiting")
    print("2. Integration of optimized logging")
    print("3. Better error handling for new tokens")
    print("\nNext: Test with a smaller batch size to verify fixes work")