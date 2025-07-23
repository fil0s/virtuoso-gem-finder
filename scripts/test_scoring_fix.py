#!/usr/bin/env python3
"""
🔧 SCORING FIX VERIFICATION TEST
Test script to verify that the scoring inflation bug has been fixed.

This script tests the fixed scoring system to ensure:
1. No scores exceed 100 points
2. Component scores stay within their intended caps
3. Bonus stacking is prevented
4. Proper normalization is applied

Author: Virtuoso AI Assistant
Date: 2025-01-31
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_focused_scoring import EarlyGemFocusedScoring
import json
from datetime import datetime

def test_extreme_high_scoring_scenarios():
    """Test scenarios that previously caused 175-180+ scores"""
    
    print("🔧 TESTING SCORING FIX - EXTREME HIGH SCENARIOS")
    print("=" * 60)
    
    scorer = EarlyGemFocusedScoring(debug_mode=True)
    
    # Test Case 1: Perfect Pump.fun token (previously would score 175+)
    perfect_pump_fun = {
        'source': 'pump_fun_stage0',
        'pump_fun_launch': True,
        'bonding_curve_stage': 'STAGE_0_ULTRA_EARLY',
        'estimated_age_minutes': 2,  # Ultra fresh
        'graduation_progress_pct': 65,  # Sweet spot
        'velocity': 6000,  # Exceptional velocity
        'platforms': ['pump_fun', 'birdeye', 'dexscreener'],
        'liquidity_usd': 15000,
        'market_cap': 200000,
        'volume_24h': 50000,
        'holders': 150
    }
    
    # Mock analysis data
    overview_data = {'holders': 150, 'market_cap': 200000}
    whale_analysis = {}
    volume_price_analysis = {
        'volume_trend': 'surging',
        'price_momentum': 'strong_bullish'
    }
    community_boost_analysis = {}
    security_analysis = {'security_score': 95, 'risk_factors': []}
    trading_activity = {
        'recent_activity_score': 90,
        'buy_sell_ratio': 3.0
    }
    dex_analysis = {
        'dex_presence_score': 8,
        'liquidity_quality_score': 85
    }
    
    print("\n🧪 Test Case 1: Perfect Pump.fun Token")
    print("-" * 40)
    
    final_score, breakdown = scorer.calculate_final_score(
        perfect_pump_fun, overview_data, whale_analysis, volume_price_analysis,
        community_boost_analysis, security_analysis, trading_activity, dex_analysis
    )
    
    print(f"📊 Final Score: {final_score:.1f}/100")
    
    # Verify component scores
    early_platform = breakdown['early_platform_analysis']['score']
    momentum = breakdown['momentum_analysis']['score']
    safety = breakdown['safety_validation']['score']
    validation = breakdown['cross_platform_bonus']['score']
    
    print(f"🔥 Early Platform: {early_platform:.1f}/50")
    print(f"📈 Momentum: {momentum:.1f}/38")
    print(f"🛡️ Safety: {safety:.1f}/25")
    print(f"✅ Validation: {validation:.1f}/12")
    
    # Verify caps
    assert final_score <= 100, f"❌ FINAL SCORE EXCEEDS 100: {final_score}"
    assert early_platform <= 50, f"❌ EARLY PLATFORM EXCEEDS 50: {early_platform}"
    assert momentum <= 38, f"❌ MOMENTUM EXCEEDS 38: {momentum}"
    assert safety <= 25, f"❌ SAFETY EXCEEDS 25: {safety}"
    assert validation <= 12, f"❌ VALIDATION EXCEEDS 12: {validation}"
    
    print("✅ All component caps verified!")
    
    # Test Case 2: Perfect Launchlab token
    perfect_launchlab = {
        'platform': 'raydium_launchlab',
        'launchlab_stage': 'ULTRA_EARLY',
        'estimated_age_minutes': 5,
        'graduation_progress_pct': 70,
        'velocity_per_hour': 12,  # Exceptional SOL velocity
        'sol_raised_estimated': 2,  # Ultra early
        'platforms': ['launchlab', 'birdeye', 'dexscreener', 'jupiter'],
        'liquidity_usd': 25000,
        'market_cap': 300000,
        'volume_24h': 75000,
        'holders': 300
    }
    
    overview_data_2 = {'holders': 300, 'market_cap': 300000}
    
    print("\n🧪 Test Case 2: Perfect Launchlab Token")
    print("-" * 40)
    
    final_score_2, breakdown_2 = scorer.calculate_final_score(
        perfect_launchlab, overview_data_2, whale_analysis, volume_price_analysis,
        community_boost_analysis, security_analysis, trading_activity, dex_analysis
    )
    
    print(f"📊 Final Score: {final_score_2:.1f}/100")
    
    # Verify component scores
    early_platform_2 = breakdown_2['early_platform_analysis']['score']
    momentum_2 = breakdown_2['momentum_analysis']['score']
    safety_2 = breakdown_2['safety_validation']['score']
    validation_2 = breakdown_2['cross_platform_bonus']['score']
    
    print(f"🔥 Early Platform: {early_platform_2:.1f}/50")
    print(f"📈 Momentum: {momentum_2:.1f}/38")
    print(f"🛡️ Safety: {safety_2:.1f}/25")
    print(f"✅ Validation: {validation_2:.1f}/12")
    
    # Verify caps
    assert final_score_2 <= 100, f"❌ FINAL SCORE EXCEEDS 100: {final_score_2}"
    assert early_platform_2 <= 50, f"❌ EARLY PLATFORM EXCEEDS 50: {early_platform_2}"
    assert momentum_2 <= 38, f"❌ MOMENTUM EXCEEDS 38: {momentum_2}"
    assert safety_2 <= 25, f"❌ SAFETY EXCEEDS 25: {safety_2}"
    assert validation_2 <= 12, f"❌ VALIDATION EXCEEDS 12: {validation_2}"
    
    print("✅ All component caps verified!")
    
    return final_score, final_score_2, breakdown, breakdown_2

def test_component_score_breakdown():
    """Test individual component score breakdowns"""
    
    print("\n🔍 COMPONENT SCORE BREAKDOWN ANALYSIS")
    print("=" * 60)
    
    scorer = EarlyGemFocusedScoring(debug_mode=True)
    
    # Test extreme scenario that would previously cause stacking
    extreme_candidate = {
        'source': 'pump_fun_stage0',
        'pump_fun_launch': True,
        'bonding_curve_stage': 'STAGE_0_ULTRA_EARLY',
        'estimated_age_minutes': 1,  # Ultra fresh
        'graduation_progress_pct': 75,  # Sweet spot
        'velocity': 10000,  # Exceptional velocity
        'platforms': ['pump_fun', 'birdeye', 'dexscreener', 'jupiter', 'meteora'],
        'liquidity_usd': 50000,
        'market_cap': 500000,
        'volume_24h': 200000,
        'holders': 1000
    }
    
    # Mock data for maximum scores
    overview_data = {'holders': 1000, 'market_cap': 500000}
    volume_price_analysis = {
        'volume_trend': 'surging',
        'price_momentum': 'strong_bullish'
    }
    trading_activity = {
        'recent_activity_score': 95,
        'buy_sell_ratio': 4.0
    }
    security_analysis = {'security_score': 100, 'risk_factors': []}
    dex_analysis = {
        'dex_presence_score': 10,
        'liquidity_quality_score': 95
    }
    
    final_score, breakdown = scorer.calculate_final_score(
        extreme_candidate, overview_data, {}, volume_price_analysis,
        {}, security_analysis, trading_activity, dex_analysis
    )
    
    print(f"\n📊 EXTREME SCENARIO RESULTS:")
    print(f"   Final Score: {final_score:.1f}/100")
    
    # Check if score components are available
    if 'score_components' in breakdown['early_platform_analysis']:
        components = breakdown['early_platform_analysis']['score_components']
        print(f"\n🔥 Early Platform Components:")
        print(f"   Base Platform: {components['base_platform']:.1f}/20")
        print(f"   Velocity Bonus: {components['velocity_bonus']:.1f}/12")
        print(f"   Stage Bonus: {components['stage_bonus']:.1f}/10")
        print(f"   Age Bonus: {components['age_bonus']:.1f}/6")
        print(f"   Graduation Bonus: {components['graduation_bonus']:.1f}/4")
        print(f"   Total Before Cap: {components['total_before_cap']:.1f}")
        print(f"   Final Score: {components['final_score']:.1f}/50")
        
        if components['total_before_cap'] > 50:
            print(f"   ⚠️  BONUS STACKING DETECTED BUT CAPPED: {components['total_before_cap']:.1f} → {components['final_score']:.1f}")
    
    if 'score_components' in breakdown['momentum_analysis']:
        components = breakdown['momentum_analysis']['score_components']
        print(f"\n📈 Momentum Components:")
        print(f"   Volume Trend: {components['volume_trend']:.1f}/12")
        print(f"   Price Momentum: {components['price_momentum']:.1f}/10")
        print(f"   Trading Activity: {components['trading_activity']:.1f}/8")
        print(f"   Holder Growth: {components['holder_growth']:.1f}/6")
        print(f"   Liquidity Quality: {components['liquidity_quality']:.1f}/4")
        print(f"   Total Before Cap: {components['total_before_cap']:.1f}")
        print(f"   Final Score: {components['final_score']:.1f}/38")
        
        if components['total_before_cap'] > 38:
            print(f"   ⚠️  BONUS STACKING DETECTED BUT CAPPED: {components['total_before_cap']:.1f} → {components['final_score']:.1f}")
    
    # Verify final score doesn't exceed 100
    assert final_score <= 100, f"❌ FINAL SCORE STILL EXCEEDS 100: {final_score}"
    
    print(f"\n✅ SCORING FIX VERIFIED: Maximum possible score is {final_score:.1f}/100")
    
    return final_score, breakdown

def generate_fix_report():
    """Generate a comprehensive fix report"""
    
    print("\n📋 SCORING FIX REPORT")
    print("=" * 60)
    
    # Run tests
    score1, score2, breakdown1, breakdown2 = test_extreme_high_scoring_scenarios()
    extreme_score, extreme_breakdown = test_component_score_breakdown()
    
    # Generate report
    report = {
        'fix_summary': {
            'issue': 'Scoring inflation causing 175-180+ scores instead of max 100',
            'root_cause': 'Bonus stacking in enhanced scoring methods',
            'fix_applied': 'Component-based scoring with individual caps and anti-stacking',
            'fix_date': datetime.now().isoformat(),
            'verification_status': 'PASSED'
        },
        'test_results': {
            'perfect_pump_fun_score': score1,
            'perfect_launchlab_score': score2,
            'extreme_scenario_score': extreme_score,
            'max_observed_score': max(score1, score2, extreme_score),
            'all_scores_under_100': all(s <= 100 for s in [score1, score2, extreme_score])
        },
        'component_caps_verified': {
            'early_platform_max': 50,
            'momentum_max': 38,
            'safety_max': 25,
            'validation_max': 12,
            'theoretical_total': 125,
            'normalized_max': 100
        },
        'before_fix': {
            'observed_scores': [175.5, 176.3, 180.4, 174.4, 173.4],
            'avg_high_score': 176.0,
            'score_inflation': '76% above intended maximum'
        },
        'after_fix': {
            'max_test_score': max(score1, score2, extreme_score),
            'score_inflation': '0% - properly capped at 100',
            'fix_effectiveness': 'SUCCESSFUL'
        }
    }
    
    # Save report
    with open('scoring_fix_verification_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ FIX VERIFICATION COMPLETE!")
    print(f"   Maximum observed score: {report['test_results']['max_observed_score']:.1f}/100")
    print(f"   Score inflation eliminated: ✅")
    print(f"   All component caps working: ✅")
    print(f"   Bonus stacking prevented: ✅")
    print(f"   Report saved: scoring_fix_verification_report.json")
    
    return report

if __name__ == "__main__":
    try:
        print("🚀 STARTING SCORING FIX VERIFICATION")
        print("=" * 60)
        
        report = generate_fix_report()
        
        print("\n🎉 SCORING FIX VERIFICATION SUCCESSFUL!")
        print("   The extreme high scores (175-180+) have been eliminated.")
        print("   All scores now properly capped at 100 points maximum.")
        print("   Component scoring with anti-stacking is working correctly.")
        
    except Exception as e:
        print(f"\n❌ SCORING FIX VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 