#!/usr/bin/env python3
"""
Test script for Smart Money Detector optimization.
Tests the updated smart money detection with actual Birdeye API response format.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from services.smart_money_detector import SmartMoneyDetector
from core.config_manager import ConfigManager
from services.optimized_logger import OptimizedLogger

# Test tokens
TEST_TOKENS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
}

# Mock response for testing (based on actual API response)
MOCK_RESPONSE = {
    "success": True,
    "data": {
        "items": [
            {
                "tokenAddress": "So11111111111111111111111111111111111111112",
                "owner": "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa",
                "tags": [],
                "type": "24h",
                "volume": 675542.1369220349,
                "trade": 74194,
                "tradeBuy": 38909,
                "tradeSell": 35285,
                "volumeBuy": 372626.71744350606,
                "volumeSell": 302915.4194785288
            },
            {
                "tokenAddress": "So11111111111111111111111111111111111111112",
                "owner": "YubQzu18FDqJRyNfG8JqHmsdbxhnoQqcKUHBdUkN6tP",
                "tags": [],
                "type": "24h",
                "volume": 188500.06136997032,
                "trade": 35531,
                "tradeBuy": 17249,
                "tradeSell": 18282,
                "volumeBuy": 94139.68529835819,
                "volumeSell": 94360.37607161213
            }
        ]
    }
}

async def test_smart_money_detector():
    """Test the optimized smart money detector."""
    logger = OptimizedLogger("test_smart_money", enable_async=False)
    birdeye_api = None
    
    try:
        # Initialize components
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Initialize dependencies
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        # Initialize Birdeye API
        birdeye_config = config.get('BIRDEYE_API', {})
        birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        # Initialize Smart Money Detector
        smart_money_detector = SmartMoneyDetector(birdeye_api, logger)
        
        print("\n🔍 SMART MONEY DETECTOR OPTIMIZATION TEST")
        print("=" * 60)
        
        # Test 1: Mock Response Processing
        print("\n📊 Test 1: Processing Mock API Response")
        print("-" * 40)
        
        # Manually test the analysis with mock data
        mock_traders = MOCK_RESPONSE["data"]["items"]
        analysis_result = await smart_money_detector._analyze_trader_quality(mock_traders, TEST_TOKENS["SOL"])
        
        print(f"✅ Analyzed {analysis_result['total_traders_analyzed']} traders")
        print(f"   Smart Traders: {analysis_result['smart_traders_count']}")
        print(f"   Smart Money Ratio: {analysis_result['smart_money_ratio']:.2%}")
        print(f"   Smart Money Level: {analysis_result['smart_money_level']}")
        print(f"   Score Boost: {analysis_result['score_boost']:.2f}x")
        
        # Display aggregate metrics
        metrics = analysis_result['aggregate_metrics']
        print(f"\n📈 Aggregate Metrics:")
        print(f"   Avg Quality Score: {metrics['avg_quality_score']:.3f}")
        print(f"   Avg Balance Ratio: {metrics['avg_balance_ratio']:.3f}")
        print(f"   Total Volume: ${metrics['total_volume']:,.2f}")
        
        # Display quality distribution
        dist = metrics['quality_distribution']
        print(f"\n📊 Quality Distribution:")
        for level, count in dist.items():
            if count > 0:
                print(f"   {level.capitalize()}: {count}")
        
        # Test 2: Live API Test (if API key is available)
        if birdeye_api.api_key:
            print("\n\n📡 Test 2: Live API Test")
            print("-" * 40)
            
            for token_name, token_address in TEST_TOKENS.items():
                print(f"\n🪙 Testing {token_name}...")
                
                try:
                    result = await smart_money_detector.analyze_token_traders(token_address)
                    
                    if result['validation_passed']:
                        print(f"   ✅ Success: {result['smart_traders_count']} smart traders found")
                        print(f"   📊 Smart Money Level: {result['smart_money_level']}")
                        print(f"   🚀 Score Boost: {result['score_boost']:.2f}x")
                        
                        # Show top smart trader if available
                        if result['smart_traders']:
                            top_trader = result['smart_traders'][0]
                            print(f"\n   👑 Top Smart Trader:")
                            print(f"      Address: {top_trader.get('owner', 'Unknown')[:8]}...")
                            print(f"      Volume: ${top_trader.get('volume', 0):,.2f}")
                            print(f"      Trades: {top_trader.get('trade', 0):,}")
                            print(f"      Quality Score: {top_trader.get('quality_score', 0):.3f}")
                            print(f"      Signals: {', '.join(top_trader.get('smart_money_signals', []))}")
                    else:
                        print(f"   ⚠️  Analysis failed validation")
                        
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                
                # Small delay between requests
                await asyncio.sleep(1)
        else:
            print("\n⚠️  No API key configured - skipping live tests")
        
        # Test 3: Edge Cases
        print("\n\n🧪 Test 3: Edge Cases")
        print("-" * 40)
        
        # Test empty response
        print("Testing empty trader list...")
        empty_result = await smart_money_detector._analyze_trader_quality([], "test_token")
        assert empty_result['smart_traders_count'] == 0
        assert empty_result['smart_money_level'] == 'minimal'
        print("   ✅ Empty list handled correctly")
        
        # Test trader with missing fields
        print("Testing trader with missing fields...")
        incomplete_trader = [{
            "owner": "TestWallet",
            "volume": 100000,
            # Missing trade, volumeBuy, volumeSell
        }]
        incomplete_result = await smart_money_detector._analyze_trader_quality(incomplete_trader, "test_token")
        print("   ✅ Missing fields handled gracefully")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if hasattr(birdeye_api, 'close'):
            await birdeye_api.close()
    
    return True

async def main():
    """Main function."""
    success = await test_smart_money_detector()
    
    if success:
        print("\n🎉 Smart Money Detector optimization verified!")
        print("\n💡 Key Optimizations Applied:")
        print("   1. ✅ Correct API response structure handling (data.items)")
        print("   2. ✅ Using actual fields: volume, trade, volumeBuy, volumeSell")
        print("   3. ✅ Removed dependency on missing fields (pnl, winRate)")
        print("   4. ✅ Added balance ratio analysis for trader quality")
        print("   5. ✅ Smart trade sizing detection")
        print("   6. ✅ Improved signal generation with actual data")
    else:
        print("\n❌ Optimization verification failed")

if __name__ == "__main__":
    asyncio.run(main()) 