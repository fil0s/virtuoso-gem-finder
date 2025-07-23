#!/usr/bin/env python3
"""
Test Enhanced Scoring Integration

This script tests the integration of enhanced pump/dump detection
into the final scoring system to verify:
- Early pump tokens get score boosts
- Extreme pump tokens get rejected
- Dump tokens get rejected
- Normal tokens maintain baseline scores
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.early_token_detection import EarlyTokenDetector
from services.logger_setup import LoggerSetup


def create_mock_token_data(symbol, phase_type):
    """Create mock token data for different pump/dump phases"""
    
    base_token = {
        'address': f'mock_address_{symbol}',
        'symbol': symbol,
        'name': f'{symbol} Token',
        'creation_time': 1735171200 - 3600,  # 1 hour ago
        'logoURI': 'https://example.com/logo.png'
    }
    
    base_overview = {
        'price': 0.001,
        'liquidity': 500000,
        'volume': {'h24': 300000, 'h1': 15000, 'h4': 60000},
        'marketCap': 1000000,
        'holders': 50
    }
    
    base_full_data = {
        'overview': base_overview,
        'holders': {'total': 50, 'items': []},
        'top_traders': [{} for _ in range(20)],
        'trading_data': {
            'trade_metrics': {
                'trend_dynamics_score': 0.6,
                'total_trades_24h': 1000
            }
        }
    }
    
    base_security = {
        'is_scam': False,
        'is_risky': False
    }
    
    # Modify based on phase type
    if phase_type == 'early_pump':
        base_overview.update({
            'priceChange1h': 75.0,   # 75% gain in 1h
            'priceChange4h': 120.0,  # 120% gain in 4h  
            'priceChange24h': 180.0, # 180% gain in 24h
            'volume': {'h24': 15000000, 'h1': 2000000, 'h4': 6000000}
        })
        
    elif phase_type == 'momentum_pump':
        base_overview.update({
            'priceChange1h': 180.0,  # 180% gain in 1h
            'priceChange4h': 400.0,  # 400% gain in 4h
            'priceChange24h': 600.0, # 600% gain in 24h
            'volume': {'h24': 25000000, 'h1': 8000000, 'h4': 15000000}
        })
        
    elif phase_type == 'extreme_pump':
        base_overview.update({
            'priceChange1h': 400.0,   # 400% gain in 1h
            'priceChange4h': 800.0,   # 800% gain in 4h
            'priceChange24h': 1500.0, # 1500% gain in 24h
            'volume': {'h24': 100000000, 'h1': 60000000, 'h4': 90000000}
        })
        
    elif phase_type == 'dump_start':
        base_overview.update({
            'priceChange1h': -45.0,  # 45% drop in 1h
            'priceChange4h': 200.0,  # Was pumping 4h ago
            'priceChange24h': 300.0, # Still positive over 24h
            'volume': {'h24': 20000000, 'h1': 8000000, 'h4': 15000000}
        })
        
    elif phase_type == 'normal':
        base_overview.update({
            'priceChange1h': 5.0,    # 5% gain in 1h
            'priceChange4h': 12.0,   # 12% gain in 4h
            'priceChange24h': 25.0,  # 25% gain in 24h
            'volume': {'h24': 2000000, 'h1': 100000, 'h4': 500000}
        })
    
    return base_token, base_full_data, base_security


async def test_early_pump_score_boost():
    """Test that early pump tokens receive score boosts"""
    
    logger_setup = LoggerSetup('scoring_test')
    logger = logger_setup.logger
    detector = EarlyTokenDetector()
    
    print("="*80)
    print("TESTING EARLY PUMP SCORE BOOST")
    print("="*80)
    
    # Create mock early pump token
    token, full_data, security = create_mock_token_data('EARLY', 'early_pump')
    basic_metrics = {'mock_address_EARLY': {'overview': full_data['overview'], 'price_data': {}}}
    security_data = {'mock_address_EARLY': security}
    
    # Calculate score
    score = await detector._calculate_comprehensive_score(token, full_data, basic_metrics, security_data)
    
    print(f"\n📊 EARLY PUMP TOKEN SCORING:")
    print(f"   Token: {token['symbol']}")
    print(f"   Price changes: 1h=75%, 4h=120%, 24h=180%")
    print(f"   Final Score: {score:.1f}")
    
    # Test criteria
    success = True
    if score < 85:  # Should get significant boost
        print(f"❌ FAILED: Early pump should score >85, got {score:.1f}")
        success = False
    
    if success:
        print("✅ SUCCESS: Early pump token received appropriate score boost!")
    
    return success, score


async def test_extreme_pump_rejection():
    """Test that extreme pump tokens get very low scores but aren't completely rejected"""
    
    logger_setup = LoggerSetup('scoring_test')
    logger = logger_setup.logger
    detector = EarlyTokenDetector()
    
    print("\n" + "="*80)
    print("TESTING EXTREME PUMP HIGH-RISK OPPORTUNITY")
    print("="*80)
    
    # Create mock extreme pump token
    token, full_data, security = create_mock_token_data('EXTREME', 'extreme_pump')
    basic_metrics = {'mock_address_EXTREME': {'overview': full_data['overview'], 'price_data': {}}}
    security_data = {'mock_address_EXTREME': security}
    
    # Calculate score
    score = await detector._calculate_comprehensive_score(token, full_data, basic_metrics, security_data)
    
    print(f"\n📊 EXTREME PUMP TOKEN SCORING:")
    print(f"   Token: {token['symbol']}")
    print(f"   Price changes: 1h=400%, 4h=800%, 24h=1500%")
    print(f"   Final Score: {score:.1f}")
    
    # Test criteria - should be low but not zero (high-risk opportunity)
    success = True
    if score == 0:  # Should not be completely rejected anymore
        print(f"❌ FAILED: Extreme pump should be high-risk opportunity (low score), not completely rejected")
        success = False
    elif score > 50:  # Should still be quite low due to high risk
        print(f"❌ FAILED: Extreme pump should have low score (<50), got {score:.1f}")
        success = False
    
    if success:
        print("✅ SUCCESS: Extreme pump token correctly scored as high-risk opportunity!")
    
    return success, score


async def test_dump_token_rejection():
    """Test that dump tokens are rejected"""
    
    logger_setup = LoggerSetup('scoring_test')
    logger = logger_setup.logger
    detector = EarlyTokenDetector()
    
    print("\n" + "="*80)
    print("TESTING DUMP TOKEN REJECTION")
    print("="*80)
    
    # Create mock dump token
    token, full_data, security = create_mock_token_data('DUMP', 'dump_start')
    basic_metrics = {'mock_address_DUMP': {'overview': full_data['overview'], 'price_data': {}}}
    security_data = {'mock_address_DUMP': security}
    
    # Calculate score
    score = await detector._calculate_comprehensive_score(token, full_data, basic_metrics, security_data)
    
    print(f"\n📊 DUMP TOKEN SCORING:")
    print(f"   Token: {token['symbol']}")
    print(f"   Price changes: 1h=-45%, 4h=200%, 24h=300%")
    print(f"   Final Score: {score:.1f}")
    
    # Test criteria
    success = True
    if score > 0:  # Should be rejected completely
        print(f"❌ FAILED: Dump token should be rejected (score=0), got {score:.1f}")
        success = False
    
    if success:
        print("✅ SUCCESS: Dump token correctly rejected!")
    
    return success, score


async def test_normal_token_baseline():
    """Test that normal tokens maintain baseline scores"""
    
    logger_setup = LoggerSetup('scoring_test')
    logger = logger_setup.logger
    detector = EarlyTokenDetector()
    
    print("\n" + "="*80)
    print("TESTING NORMAL TOKEN BASELINE")
    print("="*80)
    
    # Create mock normal token
    token, full_data, security = create_mock_token_data('NORMAL', 'normal')
    basic_metrics = {'mock_address_NORMAL': {'overview': full_data['overview'], 'price_data': {}}}
    security_data = {'mock_address_NORMAL': security}
    
    # Calculate score
    score = await detector._calculate_comprehensive_score(token, full_data, basic_metrics, security_data)
    
    print(f"\n📊 NORMAL TOKEN SCORING:")
    print(f"   Token: {token['symbol']}")
    print(f"   Price changes: 1h=5%, 4h=12%, 24h=25%")
    print(f"   Final Score: {score:.1f}")
    
    # Test criteria
    success = True
    if score < 40 or score > 80:  # Should be in normal range
        print(f"❌ FAILED: Normal token should score 40-80, got {score:.1f}")
        success = False
    
    if success:
        print("✅ SUCCESS: Normal token maintained baseline score!")
    
    return success, score


async def test_momentum_pump_moderate_boost():
    """Test that momentum pump tokens get moderate boost"""
    
    logger_setup = LoggerSetup('scoring_test')
    logger = logger_setup.logger
    detector = EarlyTokenDetector()
    
    print("\n" + "="*80)
    print("TESTING MOMENTUM PUMP MODERATE BOOST")
    print("="*80)
    
    # Create mock momentum pump token
    token, full_data, security = create_mock_token_data('MOMENTUM', 'momentum_pump')
    basic_metrics = {'mock_address_MOMENTUM': {'overview': full_data['overview'], 'price_data': {}}}
    security_data = {'mock_address_MOMENTUM': security}
    
    # Calculate score
    score = await detector._calculate_comprehensive_score(token, full_data, basic_metrics, security_data)
    
    print(f"\n📊 MOMENTUM PUMP TOKEN SCORING:")
    print(f"   Token: {token['symbol']}")
    print(f"   Price changes: 1h=180%, 4h=400%, 24h=600%")
    print(f"   Final Score: {score:.1f}")
    
    # Test criteria
    success = True
    if score < 70:  # Should get moderate boost but less than early pump
        print(f"❌ FAILED: Momentum pump should score >70, got {score:.1f}")
        success = False
    
    if success:
        print("✅ SUCCESS: Momentum pump token received moderate boost!")
    
    return success, score


async def test_scoring_comparison():
    """Test relative scoring between different phases"""
    
    print("\n" + "="*80)
    print("TESTING RELATIVE SCORING COMPARISON")
    print("="*80)
    
    logger_setup = LoggerSetup('scoring_test')
    detector = EarlyTokenDetector()
    
    # Test all phases
    phases = ['normal', 'early_pump', 'momentum_pump', 'extreme_pump', 'dump_start']
    scores = {}
    
    for phase in phases:
        token, full_data, security = create_mock_token_data(f'TEST_{phase.upper()}', phase)
        basic_metrics = {f'mock_address_TEST_{phase.upper()}': {'overview': full_data['overview'], 'price_data': {}}}
        security_data = {f'mock_address_TEST_{phase.upper()}': security}
        
        score = await detector._calculate_comprehensive_score(token, full_data, basic_metrics, security_data)
        scores[phase] = score
        print(f"   {phase:15} Score: {score:6.1f}")
    
    # Validate relative ordering
    success = True
    
    # Early pump should score highest among viable tokens
    viable_scores = {k: v for k, v in scores.items() if v > 0}
    if viable_scores and scores['early_pump'] != max(viable_scores.values()):
        print("❌ FAILED: Early pump should have highest score among viable tokens")
        success = False
    
    # Extreme pump and dump should be rejected (score = 0)
    if scores['extreme_pump'] == 0:
        print("❌ FAILED: Extreme pump should be high-risk opportunity (low score), not completely rejected")
        success = False
    elif scores['extreme_pump'] > 50:
        print("❌ FAILED: Extreme pump should have low score due to high risk")
        success = False
    
    if scores['dump_start'] > 0:
        print("❌ FAILED: Dump should be rejected")
        success = False
    
    # Early pump should score higher than momentum pump
    if scores['early_pump'] > 0 and scores['momentum_pump'] > 0:
        if scores['early_pump'] <= scores['momentum_pump']:
            print("❌ FAILED: Early pump should score higher than momentum pump")
            success = False
    
    if success:
        print("\n✅ SUCCESS: Relative scoring order is correct!")
        print("   Early Pump > Momentum Pump > Normal > Extreme Pump (high-risk) > (Dump = 0)")
    
    return success, scores


async def main():
    """Main test function"""
    
    print("🚀 TESTING ENHANCED SCORING INTEGRATION")
    print("Validating trading opportunity integration in final scores")
    
    # Run all tests
    test_results = []
    detailed_results = {}
    
    try:
        result, score = await test_early_pump_score_boost()
        test_results.append(("Early Pump Boost", result))
        detailed_results['early_pump_score'] = score
        
        result, score = await test_momentum_pump_moderate_boost()
        test_results.append(("Momentum Pump Boost", result))
        detailed_results['momentum_pump_score'] = score
        
        result, score = await test_extreme_pump_rejection()
        test_results.append(("Extreme Pump High-Risk", result))
        detailed_results['extreme_pump_score'] = score
        
        result, score = await test_dump_token_rejection()
        test_results.append(("Dump Token Rejection", result))
        detailed_results['dump_score'] = score
        
        result, score = await test_normal_token_baseline()
        test_results.append(("Normal Token Baseline", result))
        detailed_results['normal_score'] = score
        
        result, scores = await test_scoring_comparison()
        test_results.append(("Relative Scoring", result))
        detailed_results['all_scores'] = scores
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED WITH ERROR: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("ENHANCED SCORING INTEGRATION RESULTS")
    print("="*80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\nSuccess Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    # Score summary
    if 'all_scores' in detailed_results:
        print(f"\n📊 FINAL SCORE COMPARISON:")
        for phase, score in detailed_results['all_scores'].items():
            print(f"   {phase:15} {score:6.1f}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("📈 Enhanced scoring successfully integrates trading opportunities")
        print("🟢 Early pumps get score boosts")
        print("🔥 Extreme pumps become high-risk scalping opportunities")
        print("🔴 Dumps get rejected")
        print("💰 Ready for production trading!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Scoring integration needs refinement.")
    
    return passed == total


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 