#!/usr/bin/env python3
"""
🔍 Debug Scoring Issue - Trace Bonus Stacking
Find exactly where the 218-273 raw scores are coming from
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_focused_scoring import EarlyGemFocusedScoring

def debug_high_scoring_token():
    """Debug a token that would score 218+ raw points"""
    
    print("🔍 DEBUGGING HIGH SCORING TOKEN")
    print("=" * 60)
    
    # Initialize scorer with debug mode
    scorer = EarlyGemFocusedScoring(debug_mode=True)
    
    # Create a token similar to the ones scoring 174-218 final
    # This should represent a typical high-scoring token from the scan
    high_scoring_token = {
        'source': 'moralis_graduated',  # Graduated token
        'symbol': 'ELON',
        'address': '7bkszgvSDqsQgmSV852MR7TBzrn3kJAm76md5FXQpump',
        'estimated_age_minutes': 120,  # 2 hours old
        'platforms': ['birdeye', 'dexscreener', 'moralis'],
        'market_cap': 1700000,
        'liquidity': 137000,
        
        # Volume data (multi-timeframe)
        'volume_5m': 15000,
        'volume_15m': 45000,
        'volume_30m': 80000,
        'volume_1h': 120000,
        'volume_6h': 350000,
        'volume_24h': 800000,
        
        # Price changes
        'price_change_5m': 5.2,
        'price_change_15m': 12.5,
        'price_change_30m': 18.7,
        'price_change_1h': 25.3,
        'price_change_6h': 45.8,
        'price_change_24h': 89.4,
        
        # Trading activity
        'trades_5m': 25,
        'trades_15m': 78,
        'trades_30m': 145,
        'trades_1h': 234,
        'trades_6h': 567,
        'trades_24h': 1200,
        'unique_traders_24h': 345,
        
        # Platform-specific data
        'velocity': 2500,  # USD per hour
        'graduation_progress_pct': 75,
        'bonding_curve_stage': 'STAGE_1_CONFIRMED',
        'holders': 456
    }
    
    # Mock analysis data
    overview_data = {
        'holders': 456,
        'market_cap': 1700000
    }
    
    volume_price_analysis = {
        'volume_trend': 'strong_upward',
        'price_momentum': 'bullish'
    }
    
    trading_activity = {
        'recent_activity_score': 85,
        'buy_sell_ratio': 2.1
    }
    
    security_analysis = {
        'security_score': 92,
        'risk_factors': []
    }
    
    dex_analysis = {
        'dex_presence_score': 8,
        'liquidity_quality_score': 85
    }
    
    print(f"🎯 Testing token: {high_scoring_token['symbol']}")
    print(f"📊 Source: {high_scoring_token['source']}")
    print(f"⏰ Age: {high_scoring_token['estimated_age_minutes']} minutes")
    print(f"💰 Market Cap: ${high_scoring_token['market_cap']:,}")
    print()
    
    # Calculate score with detailed breakdown
    try:
        final_score, breakdown = scorer.calculate_final_score(
            candidate=high_scoring_token,
            overview_data=overview_data,
            whale_analysis={},
            volume_price_analysis=volume_price_analysis,
            community_boost_analysis={},
            security_analysis=security_analysis,
            trading_activity=trading_activity,
            dex_analysis=dex_analysis
        )
        
        print("🚨 SCORING RESULTS:")
        print("-" * 40)
        print(f"🎯 FINAL SCORE: {final_score:.1f}/100")
        
        # Extract raw component scores
        components = breakdown['final_score_summary']['component_scores']
        raw_total = breakdown['final_score_summary']['scoring_totals']['raw_total_score']
        
        print(f"📊 RAW TOTAL: {raw_total:.1f}/125 (SHOULD BE ≤125)")
        print()
        print("🔍 COMPONENT BREAKDOWN:")
        
        total_check = 0
        for component, data in components.items():
            raw_score = data['raw']
            max_score = data['max']
            weight = data['weight']
            
            # Check for over-limit scoring
            status = "✅" if raw_score <= max_score else f"❌ OVER LIMIT BY {raw_score - max_score:.1f}"
            
            print(f"  • {component.replace('_', ' ').title()}: {raw_score:.1f}/{max_score} ({weight}) {status}")
            total_check += raw_score
        
        print()
        print(f"🧮 COMPONENT SUM CHECK: {total_check:.1f} (should equal raw total: {raw_total:.1f})")
        
        if raw_total > 125:
            print(f"🚨 PROBLEM IDENTIFIED: Raw score {raw_total:.1f} exceeds 125-point limit by {raw_total - 125:.1f} points!")
            print(f"🔧 This causes final score inflation: ({raw_total:.1f}/125)*100 = {final_score:.1f}")
        
        # Check individual component details
        print("\n🔍 DETAILED COMPONENT ANALYSIS:")
        print("-" * 40)
        
        # Early platform analysis
        early_platform = breakdown.get('early_platform_analysis', {})
        if early_platform:
            print(f"🏗️  EARLY PLATFORM ANALYSIS:")
            score_components = early_platform.get('score_components', {})
            if score_components:
                for comp, value in score_components.items():
                    if isinstance(value, (int, float)):
                        print(f"    {comp}: {value:.1f}")
            print(f"    TOTAL: {early_platform.get('score', 0):.1f}/50")
        
        # Momentum analysis  
        momentum = breakdown.get('momentum_analysis', {})
        if momentum:
            print(f"📈 MOMENTUM ANALYSIS:")
            score_components = momentum.get('score_components', {})
            if score_components:
                for comp, value in score_components.items():
                    if isinstance(value, (int, float)) and comp != 'velocity_confidence':
                        print(f"    {comp}: {value:.1f}")
            print(f"    TOTAL: {momentum.get('score', 0):.1f}/38")
        
        # Safety validation
        safety = breakdown.get('safety_validation', {})
        if safety:
            print(f"🛡️  SAFETY VALIDATION:")
            print(f"    TOTAL: {safety.get('score', 0):.1f}/25")
        
        # Cross-platform bonus
        cross_platform = breakdown.get('cross_platform_bonus', {})
        if cross_platform:
            print(f"✅ CROSS-PLATFORM BONUS:")
            print(f"    TOTAL: {cross_platform.get('score', 0):.1f}/12")
        
    except Exception as e:
        print(f"❌ ERROR during scoring: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_high_scoring_token() 