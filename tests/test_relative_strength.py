import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relative_strength_analyzer import RelativeStrengthAnalyzer

async def test_relative_strength():
    """Test relative strength analysis"""
    
    analyzer = RelativeStrengthAnalyzer()
    # Temporarily override the min_universe_size for testing
    analyzer.min_universe_size = 5
    
    # Create test universe
    universe_data = [
        {'symbol': 'TOKEN1', 'price_change_1h': 1.0, 'price_change_4h': 2.0, 'price_change_24h': 5.0, 'volume_24h': 100000},
        {'symbol': 'TOKEN2', 'price_change_1h': -1.0, 'price_change_4h': 0.5, 'price_change_24h': 2.0, 'volume_24h': 50000},
        {'symbol': 'TOKEN3', 'price_change_1h': 3.0, 'price_change_4h': 5.0, 'price_change_24h': 10.0, 'volume_24h': 200000},
        {'symbol': 'TOKEN4', 'price_change_1h': -2.0, 'price_change_4h': -3.0, 'price_change_24h': -5.0, 'volume_24h': 75000},
        {'symbol': 'TOKEN5', 'price_change_1h': 0.5, 'price_change_4h': 1.5, 'price_change_24h': 3.0, 'volume_24h': 125000}
    ]
    
    # Test case 1: Strong performing token
    strong_token = {'symbol': 'STRONG', 'price_change_1h': 4.0, 'price_change_4h': 8.0, 'price_change_24h': 15.0, 'volume_24h': 250000}
    
    # Calculate relative strength
    rs_analysis = await analyzer.calculate_relative_performance(strong_token, universe_data)
    
    # Validate results
    print(f"RS Score: {rs_analysis['rs_score']:.1f}")
    print(f"Percentile Rank: {rs_analysis['percentile_rank']:.1f}")
    print(f"Consistency Score: {rs_analysis['consistency_score']:.1f}")
    
    # Check expectations
    assert rs_analysis['rs_score'] > 60, "Strong token should have high RS score"
    assert rs_analysis['percentile_rank'] > 80, "Strong token should be in top percentile"
    assert rs_analysis['consistency_score'] > 60, "Strong token should have good consistency"
    assert rs_analysis['is_market_leader'] == True, "Strong token should be market leader"
    
    # Test case 2: Weak performing token
    weak_token = {'symbol': 'WEAK', 'price_change_1h': -3.0, 'price_change_4h': -4.0, 'price_change_24h': -8.0, 'volume_24h': 30000}
    
    # Calculate relative strength
    rs_analysis = await analyzer.calculate_relative_performance(weak_token, universe_data)
    
    # Validate results
    print(f"Weak Token RS Score: {rs_analysis['rs_score']:.1f}")
    print(f"Weak Token Percentile Rank: {rs_analysis['percentile_rank']:.1f}")
    
    # Check expectations
    assert rs_analysis['rs_score'] < 50, "Weak token should have low RS score"
    assert rs_analysis['percentile_rank'] < 30, "Weak token should be in bottom percentile"
    assert rs_analysis['is_market_leader'] == False, "Weak token should not be market leader"
    
    print("✅ RS calculation working")
    print("✅ Percentile rank calculation working")
    print("✅ Market leadership identification working")
    
    # Test filtering
    tokens = universe_data + [strong_token, weak_token]
    filtered_tokens = []
    
    # Add tokens to dict format expected by filter
    for i, token in enumerate(tokens):
        token_dict = token.copy()
        filtered_tokens.append(token_dict)
    
    # Apply filter
    rs_passed = await analyzer.filter_by_relative_strength(filtered_tokens)
    
    print(f"Tokens passed RS filter: {len(rs_passed)}/{len(tokens)}")
    
    # Test passes
    print("🎉 All relative strength tests passed!")

if __name__ == "__main__":
    asyncio.run(test_relative_strength()) 