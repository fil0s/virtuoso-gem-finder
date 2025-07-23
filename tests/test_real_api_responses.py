#!/usr/bin/env python3
"""
🧪 REAL API RESPONSES TEST
Test to ensure we're getting REAL API data, not mock/test data
Verify: Real Moralis, LaunchLab, Birdeye API responses (no mock generation)
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_mock_data(data):
    """🔍 Detect if data appears to be mock/test data"""
    if not data:
        return False, "No data to analyze"
    
    mock_indicators = []
    
    # Check for systematic naming patterns
    if isinstance(data, dict):
        symbol = data.get('symbol', '')
        address = data.get('address', '')
        
        if symbol.startswith('LIVE') and symbol[4:].isdigit():
            mock_indicators.append(f"Systematic symbol: {symbol}")
        
        if 'LIVE_' in address and '_' in address:
            mock_indicators.append(f"Pattern address: {address}")
        
        # Check for systematic market caps (increments of 100)
        mc = data.get('market_cap', 0)
        if mc > 0 and mc % 100 == 0 and 180000 <= mc <= 250000:
            mock_indicators.append(f"Systematic market cap: ${mc:,}")
        
        # Check detection method
        detection_method = data.get('detection_method', '')
        if 'websocket_rpc_enhanced' in detection_method:
            mock_indicators.append(f"Test detection method: {detection_method}")
    
    elif isinstance(data, list):
        # Check if all items in list follow patterns
        for i, item in enumerate(data[:5]):  # Check first 5
            is_mock, reason = is_mock_data(item)
            if is_mock:
                mock_indicators.append(f"Item {i+1}: {reason}")
    
    is_mock = len(mock_indicators) > 0
    return is_mock, "; ".join(mock_indicators) if is_mock else "Data appears real"

async def test_real_moralis_api():
    """🔍 Test real Moralis API responses"""
    print("\n🧪 TEST 1: Real Moralis API")
    print("-" * 30)
    
    try:
        from api.moralis_connector import MoralisAPI
        
        moralis_api_key = os.getenv('MORALIS_API_KEY')
        if not moralis_api_key:
            print("   ⚠️ MORALIS_API_KEY not set - skipping test")
            return False
        
        moralis_api = MoralisAPI(api_key=moralis_api_key, logger=logger)
        
        print("   🔍 Testing Moralis bonding tokens endpoint...")
        async with moralis_api:
            bonding_tokens = await moralis_api.get_bonding_tokens_by_exchange(
                exchange="pumpfun",
                limit=5  # Small limit for testing
            )
        
        if bonding_tokens:
            print(f"   ✅ Received {len(bonding_tokens)} bonding tokens")
            
            # Analyze first token for mock data
            first_token = bonding_tokens[0]
            is_mock, reason = is_mock_data(first_token)
            
            if is_mock:
                print(f"   🚨 MOCK DATA DETECTED: {reason}")
                print(f"   📋 Token: {first_token.get('symbol', 'NO_SYMBOL')}")
                print(f"   📍 Address: {first_token.get('token_address', 'NO_ADDRESS')}")
                return False
            else:
                print(f"   ✅ REAL DATA: {reason}")
                print(f"   📋 Token: {first_token.get('symbol', 'NO_SYMBOL')}")
                print(f"   📍 Address: {first_token.get('token_address', 'NO_ADDRESS')[:10]}...")
                return True
        else:
            print("   ⚠️ No bonding tokens returned")
            return True  # Empty response is valid for real API
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_real_launchlab_api():
    """🎯 Test real LaunchLab API responses"""
    print("\n🧪 TEST 2: Real LaunchLab API")
    print("-" * 30)
    
    try:
        from services.raydium_launchlab_api_client import RaydiumLaunchLabAPIClient
        
        api_client = RaydiumLaunchLabAPIClient()
        
        print("   🔍 Testing LaunchLab API connectivity...")
        is_connected = await api_client.test_api_connectivity()
        
        if is_connected:
            print("   ✅ LaunchLab API connection successful")
            
            print("   🔍 Testing LaunchLab priority queue...")
            queue = await api_client.get_launchlab_priority_queue()
            
            if queue:
                print(f"   ✅ Received {len(queue)} LaunchLab tokens")
                
                # Analyze first token for mock data
                first_token = queue[0]
                is_mock, reason = is_mock_data(first_token)
                
                if is_mock:
                    print(f"   🚨 MOCK DATA DETECTED: {reason}")
                    return False
                else:
                    print(f"   ✅ REAL DATA: {reason}")
                    return True
            else:
                print("   ✅ Empty queue (valid for real API)")
                return True
        else:
            print("   ❌ LaunchLab API connection failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_real_birdeye_api():
    """📊 Test real Birdeye API responses"""
    print("\n🧪 TEST 3: Real Birdeye API")
    print("-" * 30)
    
    try:
        from api.birdeye_connector import BirdeyeAPI
        from api.cache_manager import EnhancedAPICacheManager
        from services.rate_limiter_service import RateLimiterService
        
        birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
        if not birdeye_api_key:
            print("   ⚠️ BIRDEYE_API_KEY not set - skipping test")
            return False
        
        config = {'api_key': birdeye_api_key}
        cache_manager = EnhancedAPICacheManager()
        rate_limiter = RateLimiterService()
        
        birdeye_api = BirdeyeAPI(
            config=config,
            logger=logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        print("   🔍 Testing Birdeye trending tokens...")
        trending_data = await birdeye_api.get_trending_tokens()
        
        if trending_data and 'data' in trending_data:
            tokens = trending_data['data']
            print(f"   ✅ Received {len(tokens)} trending tokens")
            
            if tokens:
                # Analyze first token for mock data
                first_token = tokens[0]
                is_mock, reason = is_mock_data(first_token)
                
                if is_mock:
                    print(f"   🚨 MOCK DATA DETECTED: {reason}")
                    return False
                else:
                    print(f"   ✅ REAL DATA: {reason}")
                    print(f"   📋 Token: {first_token.get('symbol', 'NO_SYMBOL')}")
                    print(f"   📍 Address: {first_token.get('address', 'NO_ADDRESS')[:10]}...")
                    return True
            else:
                print("   ✅ Empty trending list (valid)")
                return True
        else:
            print("   ❌ Invalid response format")
            return False
            
        await birdeye_api.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_early_gem_detector_without_mocks():
    """🚀 Test Early Gem Detector with REAL data only"""
    print("\n🧪 TEST 4: Early Gem Detector (Real Data Only)")
    print("-" * 50)
    
    try:
        from scripts.early_gem_detector import EarlyGemDetector
        
        # Initialize detector with debug mode
        detector = EarlyGemDetector(debug_mode=True)
        
        print("   🔍 Running token discovery (avoiding mock data)...")
        candidates = await detector.discover_early_tokens()
        
        print(f"   📊 Found {len(candidates)} total candidates")
        
        # Analyze candidates for mock data
        mock_count = 0
        real_count = 0
        
        for i, candidate in enumerate(candidates):
            is_mock, reason = is_mock_data(candidate)
            
            if is_mock:
                mock_count += 1
                if mock_count <= 3:  # Log first 3 mock detections
                    symbol = candidate.get('symbol', 'NO_SYMBOL')
                    source = candidate.get('source', 'unknown')
                    print(f"   🚨 MOCK #{mock_count}: {symbol} from {source} - {reason}")
            else:
                real_count += 1
                if real_count <= 3:  # Log first 3 real detections
                    symbol = candidate.get('symbol', 'NO_SYMBOL')
                    source = candidate.get('source', 'unknown')
                    print(f"   ✅ REAL #{real_count}: {symbol} from {source}")
        
        print(f"   📊 SUMMARY: {real_count} real, {mock_count} mock candidates")
        
        await detector.cleanup()
        
        return mock_count == 0  # Pass if no mock data detected
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def main():
    """🚀 Main test runner"""
    print("🧪 REAL API RESPONSES TEST")
    print("=" * 50)
    print("🎯 Goal: Verify we're getting REAL data, not mock/test data")
    print("🔍 Will check for systematic patterns indicating mock data")
    print()
    
    test_results = []
    
    # Test 1: Moralis API
    result1 = await test_real_moralis_api()
    test_results.append(("Moralis API", result1))
    
    # Test 2: LaunchLab API  
    result2 = await test_real_launchlab_api()
    test_results.append(("LaunchLab API", result2))
    
    # Test 3: Birdeye API
    result3 = await test_real_birdeye_api()
    test_results.append(("Birdeye API", result3))
    
    # Test 4: Early Gem Detector
    result4 = await test_early_gem_detector_without_mocks()
    test_results.append(("Early Gem Detector", result4))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🧪 REAL API RESPONSES TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ REAL DATA" if result else "🚨 MOCK/ERROR"
        print(f"{test_name:20}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{len(test_results)} tests show real data")
    
    if passed == len(test_results):
        print("✅ SUCCESS: All APIs returning real data!")
    else:
        print("⚠️ WARNING: Some APIs returning mock data or errors")
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Check for background mock data generators")
        print("   2. Verify API keys are set correctly")  
        print("   3. Ensure no test/demo modes are active")
        print("   4. Check for cached mock responses")

if __name__ == "__main__":
    asyncio.run(main()) 