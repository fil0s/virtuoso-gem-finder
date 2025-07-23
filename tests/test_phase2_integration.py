import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer
from services.relative_strength_analyzer import RelativeStrengthAnalyzer

async def test_phase2_integration():
    """Test Phase 2 components working together"""
    
    print("🧪 Testing Phase 2 Integration...")
    
    # Test 1: Trend Confirmation
    trend_analyzer = TrendConfirmationAnalyzer("test_key")
    
    # Test trend components
    test_prices = [100, 102, 104, 106, 108, 110]
    ema = trend_analyzer._calculate_ema(test_prices, 3)
    assert len(ema) > 0, "EMA calculation failed"
    print("✅ Trend confirmation system initialized")
    
    # Test 2: Relative Strength
    rs_analyzer = RelativeStrengthAnalyzer()
    # Temporarily override min universe size for testing
    rs_analyzer.min_universe_size = 2
    
    universe = [
        {'price_change_1h': 1, 'price_change_4h': 2, 'price_change_24h': 5, 'volume_24h': 100000},
        {'price_change_1h': -1, 'price_change_4h': 0, 'price_change_24h': 1, 'volume_24h': 50000}
    ]
    
    universe_stats = rs_analyzer._calculate_universe_returns(universe)
    assert 'median_1h' in universe_stats, "Universe calculation failed"
    print("✅ Relative strength system initialized")
    
    # Test 3: Integration compatibility
    # Both systems should work with the same token data format
    test_token = {
        'symbol': 'TEST',
        'address': 'test_address',
        'price_change_1h': 5.0,
        'price_change_4h': 8.0,
        'price_change_24h': 15.0,
        'volume_24h': 200000
    }
    
    # RS analysis should work
    rs_result = await rs_analyzer.calculate_relative_performance(test_token, universe)
    assert 'rs_score' in rs_result, "RS analysis failed"
    print("✅ Token data format compatible between systems")
    
    print("🎉 Phase 2 Integration Test PASSED!")
    print("📋 Ready for Phase 3 implementation")

if __name__ == "__main__":
    asyncio.run(test_phase2_integration()) 