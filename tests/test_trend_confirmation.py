import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer

async def test_trend_confirmation():
    """Test trend confirmation system"""
    
    # Mock Birdeye API key for testing
    analyzer = TrendConfirmationAnalyzer("test_api_key")
    
    # Test EMA calculation
    test_prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109]
    ema = analyzer._calculate_ema(test_prices, 5)
    assert len(ema) > 0, "EMA calculation failed"
    print("✅ EMA calculation working")
    
    # Test higher highs/lows detection
    # Create longer sequence for higher highs/lows
    highs = [100, 102, 105, 103, 108, 110, 107, 112, 115, 113, 
             116, 114, 117, 120, 118, 121, 119, 124, 125, 123]
    lows = [95, 97, 100, 98, 103, 105, 102, 107, 110, 108,
            109, 107, 112, 114, 111, 115, 114, 118, 120, 117]
    higher_structure = analyzer._check_higher_highs_lows(highs, lows)
    print(f"✅ Higher structure detection: {higher_structure}")
    
    # Test momentum calculation
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    momentum = analyzer._calculate_momentum(closes)
    assert momentum > 0, "Momentum should be positive for uptrending prices"
    print(f"✅ Momentum calculation: {momentum:.2f}")
    
    # Test timeframe score calculation
    score = analyzer._calculate_timeframe_score(
        price_above_ema20=True,
        price_above_ema50=True,
        ema_alignment=True,
        higher_structure=True,
        momentum=5.0,
        volume_trend='increasing'
    )
    assert score > 80, f"Strong trend should score >80, got {score}"
    print(f"✅ Timeframe scoring: {score}")
    
    print("🎉 All trend confirmation tests passed!")

if __name__ == "__main__":
    asyncio.run(test_trend_confirmation()) 