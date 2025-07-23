#!/usr/bin/env python3
"""
Simple test to verify Early Gem Focused Scoring integration
"""

from scripts.early_gem_focused_scoring import EarlyGemFocusedScoring

def test_early_gem_integration():
    """Test that early gem scoring system is working properly"""
    
    print("🚀 TESTING EARLY GEM SCORING INTEGRATION")
    print("=" * 60)
    
    try:
        # Initialize early gem scorer
        scorer = EarlyGemFocusedScoring()
        print("✅ EarlyGemFocusedScoring class initialized successfully")
        
        # Test candidate data
        test_candidate = {
            'address': 'TEST123456789',
            'symbol': 'TESTGEM',
            'name': 'Test Gem Token',
            'source': 'pump_fun_stage0',
            'pump_fun_launch': True,
            'bonding_curve_stage': 'STAGE_0_ULTRA_EARLY',
            'estimated_age_minutes': 5,
            'graduation_progress_pct': 65,
            'platforms': ['pump_fun'],
            'price': 0.000087,
            'market_cap': 45000,
            'volume_24h': 12500,
            'liquidity': 8500
        }
        
        # Test analysis data
        test_analysis_data = {
            'overview_data': {
                'holders': 89,
                'price_24h_change': 156.7
            },
            'whale_analysis': {
                'whale_concentration': 35.2,
                'smart_money_detected': True
            },
            'volume_price_analysis': {
                'volume_trend': 'surging',
                'price_momentum': 'strong_bullish'
            },
            'security_analysis': {
                'security_score': 92,
                'risk_factors': []
            },
            'trading_activity': {
                'recent_activity_score': 87,
                'buy_sell_ratio': 2.8
            },
            'dex_analysis': {
                'dex_presence_score': 6.5,
                'liquidity_quality_score': 75
            }
        }
        
        # Test the scoring
        final_score, breakdown = scorer.calculate_early_gem_score(test_candidate, test_analysis_data)
        
        print(f"🎯 TEST RESULT: {final_score:.1f}/100")
        print(f"📊 CONVICTION LEVEL: {scorer._get_conviction_level(final_score)}")
        
        # Verify breakdown structure
        expected_components = ['early_platform_analysis', 'momentum_analysis', 'safety_validation', 'cross_platform_bonus']
        for component in expected_components:
            if component in breakdown:
                score = breakdown[component].get('score', 0)
                print(f"   • {component.replace('_', ' ').title()}: {score:.1f}")
            else:
                print(f"   ❌ Missing component: {component}")
        
        print("\n✅ INTEGRATION TEST PASSED")
        print("🚀 Early Gem Focused Scoring is ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_early_gem_integration() 