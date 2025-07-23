#!/usr/bin/env python3
"""
🔍 Debug Scoring Normalization Issue
Trace why we're getting 178-218 scores instead of 100-point maximum
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_focused_scoring import EarlyGemFocusedScoring

def debug_scoring_issue():
    """Debug the scoring normalization issue"""
    
    print("🔍 DEBUGGING SCORING NORMALIZATION ISSUE")
    print("=" * 60)
    
    # Initialize scorer
    scorer = EarlyGemFocusedScoring(debug_mode=True)
    
    # Create a test candidate that would get high scores
    test_candidate = {
        'source': 'moralis_graduated',
        'address': 'test123',
        'symbol': 'TEST',
        'name': 'Test Token',
        'estimated_age_minutes': 15,  # Very fresh
        'graduation_progress_pct': 60,  # Sweet spot
        'velocity': 3000,  # High velocity
        'bonding_curve_stage': 'STAGE_0_ULTRA_EARLY',
        'platforms': ['birdeye', 'dexscreener', 'jupiter'],
        
        # Multi-timeframe data for velocity analysis
        'volume_5m': 50000,
        'volume_15m': 45000,
        'volume_30m': 40000,
        'volume_1h': 75000,
        'volume_6h': 200000,
        'volume_24h': 500000,
        
        'price_change_5m': 15.5,
        'price_change_15m': 12.3,
        'price_change_30m': 8.7,
        'price_change_1h': 25.2,
        'price_change_6h': 45.8,
        'price_change_24h': 120.5,
        
        'trades_5m': 150,
        'trades_15m': 140,
        'trades_30m': 130,
        'trades_1h': 300,
        'trades_6h': 800,
        'trades_24h': 2000,
        'unique_traders': 250
    }
    
    overview_data = {
        'holders': 500,
        'market_cap': 150000
    }
    
    volume_price_analysis = {
        'volume_trend': 'increasing',
        'price_momentum': 'strong_bullish'
    }
    
    trading_activity = {
        'recent_activity_score': 85,
        'buy_sell_ratio': 2.5
    }
    
    security_analysis = {
        'security_score': 90,
        'risk_factors': []
    }
    
    dex_analysis = {
        'dex_presence_score': 8,
        'liquidity_quality_score': 85
    }
    
    print("🧪 TEST CANDIDATE PROFILE:")
    print(f"   Source: {test_candidate['source']}")
    print(f"   Age: {test_candidate['estimated_age_minutes']} minutes")
    print(f"   Graduation: {test_candidate['graduation_progress_pct']}%")
    print(f"   Velocity: ${test_candidate['velocity']}/hour")
    print(f"   Volume 1h: ${test_candidate['volume_1h']:,}")
    print(f"   Price Change 1h: {test_candidate['price_change_1h']}%")
    print()
    
    # Calculate score with detailed breakdown
    final_score, breakdown = scorer.calculate_final_score(
        candidate=test_candidate,
        overview_data=overview_data,
        whale_analysis={},
        volume_price_analysis=volume_price_analysis,
        community_boost_analysis={},
        security_analysis=security_analysis,
        trading_activity=trading_activity,
        dex_analysis=dex_analysis
    )
    
    print("📊 DETAILED SCORING BREAKDOWN:")
    print("-" * 40)
    
    # Extract component scores
    components = breakdown['final_score_summary']['component_scores']
    totals = breakdown['final_score_summary']['scoring_totals']
    
    print("🔥 COMPONENT SCORES:")
    total_raw = 0
    for component, data in components.items():
        raw_score = data['raw']
        max_score = data['max']
        weight = data['weight']
        total_raw += raw_score
        
        print(f"   {component.replace('_', ' ').title()}: {raw_score:.1f}/{max_score} ({weight})")
        
        # Check if component exceeds its maximum
        if raw_score > max_score:
            print(f"   ⚠️  WARNING: {component} exceeds maximum by {raw_score - max_score:.1f} points!")
    
    print()
    print("🎯 FINAL CALCULATION:")
    print(f"   Raw Total: {totals['raw_total_score']:.1f}")
    print(f"   Calculated Total: {total_raw:.1f}")
    print(f"   Normalization Factor: {totals['normalization_factor']}")
    print(f"   Final Score: {totals['final_score']:.1f}")
    print(f"   Expected Max: {totals['max_possible_score']}")
    
    # Check for issues
    print()
    print("🚨 ISSUE ANALYSIS:")
    
    if totals['raw_total_score'] > 125:
        print(f"   ❌ RAW SCORE EXCEEDS 125: {totals['raw_total_score']:.1f}/125")
        print(f"   📊 This means component caps are not working!")
        
        # Check each component
        for component, data in components.items():
            if data['raw'] > data['max']:
                print(f"   🔍 {component}: {data['raw']:.1f} > {data['max']} (excess: {data['raw'] - data['max']:.1f})")
    
    if totals['final_score'] > 100:
        print(f"   ❌ FINAL SCORE EXCEEDS 100: {totals['final_score']:.1f}/100")
        print(f"   📊 This means normalization is not working!")
    
    # Check individual component breakdowns
    print()
    print("🔍 COMPONENT BREAKDOWN ANALYSIS:")
    
    # Early platform analysis
    early_platform = breakdown.get('early_platform_analysis', {})
    if 'score_components' in early_platform:
        print("🔥 Early Platform Components:")
        ep_components = early_platform['score_components']
        ep_total = 0
        for comp, score in ep_components.items():
            if comp not in ['total_before_cap', 'final_score']:
                ep_total += score
                print(f"   {comp}: {score:.1f}")
        print(f"   Calculated Total: {ep_total:.1f}")
        print(f"   Reported Total: {ep_components.get('total_before_cap', 0):.1f}")
        print(f"   Final Score: {ep_components.get('final_score', 0):.1f}")
        
        if ep_components.get('final_score', 0) > 50:
            print(f"   ⚠️  Early Platform exceeds 50-point cap!")
    
    # Momentum analysis
    momentum = breakdown.get('momentum_analysis', {})
    if 'score_components' in momentum:
        print()
        print("📈 Momentum Components:")
        m_components = momentum['score_components']
        m_total = 0
        for comp, score in m_components.items():
            if comp not in ['total_before_cap', 'final_score', 'velocity_confidence']:
                m_total += score
                print(f"   {comp}: {score:.1f}")
        print(f"   Calculated Total: {m_total:.1f}")
        print(f"   Reported Total: {m_components.get('total_before_cap', 0):.1f}")
        print(f"   Final Score: {m_components.get('final_score', 0):.1f}")
        
        if m_components.get('final_score', 0) > 38:
            print(f"   ⚠️  Momentum exceeds 38-point cap!")
    
    print()
    print("🎯 SUMMARY:")
    print(f"   Expected Range: 0-100 points")
    print(f"   Actual Score: {final_score:.1f} points")
    print(f"   Issue Severity: {'🔴 CRITICAL' if final_score > 100 else '🟡 MODERATE' if final_score > 80 else '🟢 NORMAL'}")
    
    return final_score, breakdown

if __name__ == "__main__":
    debug_scoring_issue() 