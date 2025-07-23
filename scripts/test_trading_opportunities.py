#!/usr/bin/env python3
"""
Test Enhanced Pump/Dump Trading Opportunities

This script tests the new trading opportunity detection system to verify
it can identify profitable pump phases and warn about dump phases.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.pump_dump_detector import EnhancedPumpDumpDetector
from services.logger_setup import LoggerSetup


def test_early_pump_opportunity():
    """Test early pump detection for entry opportunities"""
    
    logger_setup = LoggerSetup('trading_test')
    logger = logger_setup.logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    
    print("="*80)
    print("TESTING EARLY PUMP TRADING OPPORTUNITY")
    print("="*80)
    
    # Simulate early pump phase (good entry opportunity)
    early_pump_data = {
        'token_symbol': 'EARLYP',
        'price_change_1h_percent': 75.0,      # 75% gain in 1h (early pump)
        'price_change_4h_percent': 120.0,     # 120% gain in 4h (building momentum)
        'price_change_24h_percent': 180.0,    # 180% gain in 24h (early in cycle)
        'volume_24h': 15000000,               # $15M volume
        'volume_1h': 2000000,                 # $2M in 1h (reasonable)
        'volume_4h': 6000000,                 # $6M in 4h (sustained)
        'market_cap': 1000000,                # $1M market cap
        'unique_trader_count': 150,           # Good diversity
        'trade_count_24h': 2000,              # Healthy trade count
        'creation_time': 1735171200 - 7200    # 2 hours old
    }
    
    print("\n📊 EARLY PUMP DATA:")
    print(f"   Price changes: 1h={early_pump_data['price_change_1h_percent']}%, 4h={early_pump_data['price_change_4h_percent']}%, 24h={early_pump_data['price_change_24h_percent']}%")
    print(f"   Volume/Market Cap: {early_pump_data['volume_24h']/early_pump_data['market_cap']:.1f}x")
    print(f"   Trader diversity: {early_pump_data['unique_trader_count']} traders")
    
    result = detector.analyze_token(early_pump_data)
    
    print(f"\n🔍 ANALYSIS RESULTS:")
    print(f"   Current Phase: {result['current_phase']}")
    print(f"   Phase Confidence: {result['phase_confidence']:.2f}")
    print(f"   Overall Risk: {result['overall_risk']}")
    print(f"   Recommendation: {result['recommendation']}")
    print(f"   Profit Potential: {result['profit_potential']:.1f}%")
    
    if result['trading_opportunities']:
        print(f"\n💰 TRADING OPPORTUNITIES ({len(result['trading_opportunities'])}):")
        for i, opp in enumerate(result['trading_opportunities'], 1):
            print(f"   {i}. {opp['opportunity_type']} - {opp['action']}")
            print(f"      Profit Target: {opp['estimated_profit_potential']:.1f}%")
            print(f"      Max Hold Time: {opp['max_hold_time_minutes']} minutes")
            print(f"      Stop Loss: {opp['stop_loss_percentage']:.1f}%")
            print(f"      Take Profit: {opp['take_profit_percentage']:.1f}%")
            print(f"      Reasoning: {opp['reasoning']}")
            print()
    
    # Test success criteria
    success = True
    if result['current_phase'] != 'EARLY_PUMP':
        print("❌ FAILED: Should detect EARLY_PUMP phase")
        success = False
    
    if not result['trading_opportunities']:
        print("❌ FAILED: Should identify trading opportunity")
        success = False
    
    if result['trading_opportunities'] and result['trading_opportunities'][0]['action'] != 'ENTER':
        print("❌ FAILED: Should recommend ENTER action")
        success = False
    
    if success:
        print("✅ SUCCESS: Early pump opportunity correctly identified!")
    
    return success


def test_extreme_pump_exit():
    """Test extreme pump detection for scalping opportunities and exit signals"""
    
    logger_setup = LoggerSetup('trading_test')
    logger = logger_setup.logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    
    print("\n" + "="*80)
    print("TESTING EXTREME PUMP SCALPING OPPORTUNITY")
    print("="*80)
    
    # Simulate extreme pump phase (exit immediately)
    extreme_pump_data = {
        'token_symbol': 'EXTREMEP',
        'price_change_1h_percent': 400.0,     # 400% gain in 1h (EXTREME)
        'price_change_4h_percent': 800.0,     # 800% gain in 4h (EXTREME)
        'price_change_24h_percent': 1500.0,   # 1500% gain in 24h (EXTREME)
        'volume_24h': 100000000,              # $100M volume
        'volume_1h': 60000000,                # $60M in 1h (concentrated)
        'volume_4h': 90000000,                # $90M in 4h (very concentrated)
        'market_cap': 5000000,                # $5M market cap
        'unique_trader_count': 30,            # Low diversity (warning sign)
        'trade_count_24h': 8000,              # High frequency
        'creation_time': 1735171200 - 3600    # 1 hour old
    }
    
    print("\n📊 EXTREME PUMP DATA:")
    print(f"   Price changes: 1h={extreme_pump_data['price_change_1h_percent']}%, 4h={extreme_pump_data['price_change_4h_percent']}%, 24h={extreme_pump_data['price_change_24h_percent']}%")
    print(f"   Volume/Market Cap: {extreme_pump_data['volume_24h']/extreme_pump_data['market_cap']:.1f}x")
    
    result = detector.analyze_token(extreme_pump_data)
    
    print(f"\n🔍 ANALYSIS RESULTS:")
    print(f"   Current Phase: {result['current_phase']}")
    print(f"   Overall Risk: {result['overall_risk']}")
    print(f"   Recommendation: {result['recommendation']}")
    
    if result['trading_opportunities']:
        print(f"\n🔥 SCALPING & EXIT SIGNALS:")
        for i, opp in enumerate(result['trading_opportunities'], 1):
            print(f"   {i}. Action: {opp['action']}")
            print(f"      Risk Level: {opp['risk_level']}")
            if opp['action'] == 'ENTER_HIGH_RISK':
                print(f"      Scalp Target: {opp['estimated_profit_potential']:.1f}%")
                print(f"      Max Hold: {opp['max_hold_time_minutes']} minutes")
                print(f"      Stop Loss: {opp['stop_loss_percentage']:.1f}%")
                print(f"      Take Profit: {opp['take_profit_percentage']:.1f}%")
            elif opp['action'] == 'EXIT':
                print(f"      Expected Loss if Staying: {opp['estimated_profit_potential']:.1f}%")
                print(f"      Exit Within: {opp['max_hold_time_minutes']} minutes")
            print(f"      Reasoning: {opp['reasoning']}")
            print()
    
    # Test success criteria
    success = True
    if result['current_phase'] != 'EXTREME_PUMP':
        print("❌ FAILED: Should detect EXTREME_PUMP phase")
        success = False
    
    if not result['trading_opportunities']:
        print("❌ FAILED: Should identify trading opportunities")
        success = False
    
    # Check for high-risk scalping opportunity
    has_scalp_opportunity = False
    has_exit_signal = False
    
    for opp in result['trading_opportunities']:
        if opp['action'] == 'ENTER_HIGH_RISK':
            has_scalp_opportunity = True
        elif opp['action'] == 'EXIT':
            has_exit_signal = True
    
    if not has_scalp_opportunity:
        print("❌ FAILED: Should provide high-risk scalping opportunity")
        success = False
    
    if not has_exit_signal:
        print("❌ FAILED: Should also provide exit signal for existing positions")
        success = False
    
    if result['overall_risk'] != 'CRITICAL':
        print("❌ FAILED: Should be CRITICAL risk level")
        success = False
    
    if success:
        print("✅ SUCCESS: Extreme pump scalping opportunity and exit signal correctly identified!")
    
    return success


def test_dump_warning():
    """Test dump detection for avoid signals"""
    
    logger_setup = LoggerSetup('trading_test')
    logger = logger_setup.logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    
    print("\n" + "="*80)
    print("TESTING DUMP WARNING DETECTION")
    print("="*80)
    
    # Simulate dump start phase (was pumping, now dumping)
    dump_start_data = {
        'token_symbol': 'DUMPER',
        'price_change_1h_percent': -45.0,     # 45% drop in 1h (severe dump)
        'price_change_4h_percent': 200.0,     # Was pumping 4h ago
        'price_change_24h_percent': 300.0,    # Still positive over 24h
        'volume_24h': 20000000,               # $20M volume
        'volume_1h': 8000000,                 # $8M in 1h (panic selling)
        'volume_4h': 15000000,               # $15M in 4h
        'market_cap': 2000000,                # $2M market cap
        'unique_trader_count': 80,            # Moderate diversity
        'trade_count_24h': 3000,              # Normal trade count
        'creation_time': 1735171200 - 14400   # 4 hours old
    }
    
    print("\n📊 DUMP START DATA:")
    print(f"   Price changes: 1h={dump_start_data['price_change_1h_percent']}%, 4h={dump_start_data['price_change_4h_percent']}%, 24h={dump_start_data['price_change_24h_percent']}%")
    print(f"   Volume spike during dump: {dump_start_data['volume_1h']/1000000:.1f}M in 1h")
    
    result = detector.analyze_token(dump_start_data)
    
    print(f"\n🔍 ANALYSIS RESULTS:")
    print(f"   Current Phase: {result['current_phase']}")
    print(f"   Overall Risk: {result['overall_risk']}")
    print(f"   Recommendation: {result['recommendation']}")
    
    if result['signals']:
        print(f"\n🚨 WARNING SIGNALS:")
        for signal in result['signals']:
            if signal['trading_action'] in ['SELL_WARNING', 'AVOID']:
                print(f"   {signal['severity']} - {signal['description']}")
                print(f"   Action: {signal['trading_action']}")
    
    # Test success criteria
    success = True
    if result['current_phase'] not in ['DUMP_START', 'DUMP_CONTINUATION']:
        print("❌ FAILED: Should detect dump phase")
        success = False
    
    sell_warnings = [s for s in result['signals'] if s['trading_action'] == 'SELL_WARNING']
    if not sell_warnings:
        print("❌ FAILED: Should generate sell warning")
        success = False
    
    if success:
        print("✅ SUCCESS: Dump warning correctly identified!")
    
    return success


def test_trading_strategy_simulation():
    """Simulate a complete pump/dump cycle for strategy validation"""
    
    logger_setup = LoggerSetup('trading_test')
    logger = logger_setup.logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    
    print("\n" + "="*80)
    print("SIMULATING COMPLETE PUMP/DUMP CYCLE")
    print("="*80)
    
    # Simulate different phases of a pump and dump
    phases = [
        {
            'name': 'Early Pump Phase',
            'data': {
                'token_symbol': 'CYCLE',
                'price_change_1h_percent': 60.0,
                'price_change_4h_percent': 80.0,
                'price_change_24h_percent': 150.0,
                'volume_24h': 8000000,
                'volume_1h': 1000000,
                'market_cap': 500000,
                'unique_trader_count': 120,
                'trade_count_24h': 1500,
                'creation_time': 1735171200 - 7200
            },
            'expected_action': 'ENTER'
        },
        {
            'name': 'Momentum Pump Phase',
            'data': {
                'token_symbol': 'CYCLE',
                'price_change_1h_percent': 180.0,
                'price_change_4h_percent': 400.0,
                'price_change_24h_percent': 600.0,
                'volume_24h': 25000000,
                'volume_1h': 8000000,
                'market_cap': 2000000,
                'unique_trader_count': 200,
                'trade_count_24h': 5000,
                'creation_time': 1735171200 - 7200
            },
            'expected_action': 'MONITOR'
        },
        {
            'name': 'Extreme Pump Phase',
            'data': {
                'token_symbol': 'CYCLE',
                'price_change_1h_percent': 350.0,
                'price_change_4h_percent': 800.0,
                'price_change_24h_percent': 1200.0,
                'volume_24h': 80000000,
                'volume_1h': 40000000,
                'market_cap': 5000000,
                'unique_trader_count': 100,
                'trade_count_24h': 8000,
                'creation_time': 1735171200 - 7200
            },
            'expected_action': 'ENTER_HIGH_RISK'
        },
        {
            'name': 'Dump Start Phase',
            'data': {
                'token_symbol': 'CYCLE',
                'price_change_1h_percent': -60.0,
                'price_change_4h_percent': 200.0,
                'price_change_24h_percent': 400.0,
                'volume_24h': 50000000,
                'volume_1h': 20000000,
                'market_cap': 2000000,
                'unique_trader_count': 80,
                'trade_count_24h': 6000,
                'creation_time': 1735171200 - 7200
            },
            'expected_action': 'AVOID'
        }
    ]
    
    strategy_results = []
    
    for phase in phases:
        print(f"\n📍 {phase['name']}:")
        result = detector.analyze_token(phase['data'])
        
        print(f"   Phase: {result['current_phase']}")
        print(f"   Risk: {result['overall_risk']}")
        
        actual_action = 'NONE'
        if result['trading_opportunities']:
            # For extreme pumps, prioritize ENTER_HIGH_RISK over EXIT
            high_risk_entry = next((opp for opp in result['trading_opportunities'] if opp['action'] == 'ENTER_HIGH_RISK'), None)
            if high_risk_entry:
                actual_action = 'ENTER_HIGH_RISK'
            else:
                actual_action = result['trading_opportunities'][0]['action']
        elif any(s['trading_action'] == 'AVOID' for s in result['signals']):
            actual_action = 'AVOID'
        
        print(f"   Expected Action: {phase['expected_action']}")
        print(f"   Actual Action: {actual_action}")
        
        success = (actual_action == phase['expected_action'] or 
                  (phase['expected_action'] in ['MONITOR', 'ENTER'] and actual_action in ['MONITOR', 'ENTER']))
        
        strategy_results.append(success)
        print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    overall_success = all(strategy_results)
    success_rate = sum(strategy_results) / len(strategy_results) * 100
    
    print(f"\n📊 STRATEGY SIMULATION RESULTS:")
    print(f"   Phases Tested: {len(phases)}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Overall Result: {'✅ STRATEGY VALIDATED' if overall_success else '❌ STRATEGY NEEDS IMPROVEMENT'}")
    
    return overall_success


def main():
    """Main test function"""
    
    print("🚀 STARTING ENHANCED PUMP/DUMP TRADING TESTS")
    print("Testing the new trading opportunity detection system")
    
    # Run all tests
    test_results = []
    
    try:
        test_results.append(("Early Pump Opportunity", test_early_pump_opportunity()))
        test_results.append(("Extreme Pump Scalping", test_extreme_pump_exit()))
        test_results.append(("Dump Warning", test_dump_warning()))
        test_results.append(("Trading Strategy", test_trading_strategy_simulation()))
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED WITH ERROR: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("TRADING OPPORTUNITY TEST RESULTS")
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
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("📈 The system can now identify profitable pump opportunities")
        print("🔥 And provide high-risk scalping for extreme pumps")
        print("⚠️  With timely exit signals for dumps")
        print("💰 Ready for trading implementation!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. System needs refinement.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 