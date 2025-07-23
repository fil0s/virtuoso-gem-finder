#!/usr/bin/env python3
"""
Test script to validate enhanced pump and dump detection.

This script tests the improved scoring system against various scenarios
including the TDCCP case to ensure proper detection and scoring.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from services.pump_dump_detector import EnhancedPumpDumpDetector
from services.early_token_detection import EarlyTokenDetector
from services.logger_setup import LoggerSetup

def setup_logging():
    """Setup logging for testing."""
    logger_setup = LoggerSetup('TestPumpDumpDetection', log_level='DEBUG')
    return logger_setup.logger

def test_tdccp_scenario():
    """
    Test the TDCCP pump and dump scenario.
    TDCCP spiked from $0.0004 to over $3.00 (750,000%+ gain) before crashing.
    """
    print("=" * 60)
    print("TESTING TDCCP SCENARIO")
    print("=" * 60)
    
    # Simulate TDCCP's peak pump data
    tdccp_pump_data = {
        'token_symbol': 'TDCCP',
        'price_change_1h_percent': 1500.0,   # 1500% in 1 hour during peak
        'price_change_4h_percent': 5000.0,   # 5000% in 4 hours 
        'price_change_24h_percent': 750000.0, # 750,000% in 24 hours (actual)
        'volume_24h': 50000000,              # $50M volume
        'volume_1h': 10000000,               # $10M in last hour
        'volume_4h': 25000000,               # $25M in 4 hours
        'market_cap': 1000000,               # $1M market cap (volume 50x market cap!)
        'unique_trader_count': 8,            # Very few traders for massive volume
        'trade_count_24h': 1200,
        'creation_time': time.time() - (12 * 3600)  # 12 hours old
    }
    
    print(f"Testing TDCCP pump phase scenario:")
    print(f"  - 24h price change: {tdccp_pump_data['price_change_24h_percent']:+,.0f}%")
    print(f"  - Volume: ${tdccp_pump_data['volume_24h']:,.0f}")
    print(f"  - Market cap: ${tdccp_pump_data['market_cap']:,.0f}")
    print(f"  - Volume/Market cap ratio: {tdccp_pump_data['volume_24h']/tdccp_pump_data['market_cap']:.1f}x")
    print(f"  - Unique traders: {tdccp_pump_data['unique_trader_count']}")
    
    # Test pump/dump detection
    logger = LoggerSetup('TestPumpDumpDetection', log_level='DEBUG').logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    pump_dump_analysis = detector.analyze_token(tdccp_pump_data)
    
    print("\nPUMP/DUMP ANALYSIS RESULTS:")
    print(f"  - Risk Level: {pump_dump_analysis.get('overall_risk_level', 'UNKNOWN')}")
    print(f"  - Risk Score: {pump_dump_analysis.get('risk_score', 0):.3f}")
    print(f"  - Total Score: {pump_dump_analysis.get('total_score', 0)}")
    print(f"  - Recommendation: {pump_dump_analysis.get('recommendation', 'UNKNOWN')}")
    print(f"  - Warning Flags: {pump_dump_analysis.get('warning_flags', [])}")
    
    # Check if it properly detected as high risk
    risk_level = pump_dump_analysis.get('overall_risk_level', 'UNKNOWN')
    risk_score = pump_dump_analysis.get('risk_score', 0)
    
    if risk_level in ['CRITICAL', 'HIGH'] and risk_score >= 0.6:
        print("✅ SUCCESS: TDCCP pump properly detected as HIGH/CRITICAL risk")
        return True
    else:
        print("❌ FAILURE: TDCCP pump not properly detected as high risk")
        return False

def test_tdccp_crash_scenario():
    """
    Test TDCCP crash scenario (after the pump).
    """
    print("=" * 60)
    print("TESTING TDCCP CRASH SCENARIO")
    print("=" * 60)
    
    # Simulate TDCCP's crash data (from $3.00 to $0.27)
    tdccp_crash_data = {
        'token_symbol': 'TDCCP_CRASH',
        'price_change_1h_percent': -85.0,    # 85% crash in 1 hour
        'price_change_4h_percent': -60.0,    # 60% crash in 4 hours
        'price_change_24h_percent': 200000.0, # Still up massively from 24h ago
        'volume_24h': 30000000,              # $30M volume during crash
        'volume_1h': 15000000,               # $15M panic selling
        'volume_4h': 20000000,               # $20M selling pressure
        'market_cap': 500000,                # Crashed market cap
        'unique_trader_count': 15,           # More traders during panic
        'trade_count_24h': 2000,
        'creation_time': time.time() - (18 * 3600)  # 18 hours old
    }
    
    print(f"Testing TDCCP crash phase scenario:")
    print(f"  - 1h price change: {tdccp_crash_data['price_change_1h_percent']:+.1f}%")
    print(f"  - 24h price change: {tdccp_crash_data['price_change_24h_percent']:+,.0f}%")
    print(f"  - Volume: ${tdccp_crash_data['volume_24h']:,.0f}")
    
    # Test pump/dump detection
    logger = LoggerSetup('TestPumpDumpDetection', log_level='DEBUG').logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    pump_dump_analysis = detector.analyze_token(tdccp_crash_data)
    
    print("\nCRASH ANALYSIS RESULTS:")
    print(f"  - Risk Level: {pump_dump_analysis.get('overall_risk_level', 'UNKNOWN')}")
    print(f"  - Risk Score: {pump_dump_analysis.get('risk_score', 0):.3f}")
    print(f"  - Warning Flags: {pump_dump_analysis.get('warning_flags', [])}")
    
    # Check for pump/dump pattern detection
    warning_flags = pump_dump_analysis.get('warning_flags', [])
    if 'PUMP_DUMP_PATTERN' in warning_flags or 'EXTREME_PRICE_MOVEMENT' in warning_flags:
        print("✅ SUCCESS: TDCCP crash properly detected pump/dump pattern")
        return True
    else:
        print("⚠️  WARNING: TDCCP crash pattern not fully detected")
        return False

def test_legitimate_token_scenario():
    """
    Test a legitimate high-performing token to ensure it doesn't get penalized.
    """
    print("=" * 60)
    print("TESTING LEGITIMATE TOKEN SCENARIO")
    print("=" * 60)
    
    # Simulate a legitimate token with good growth
    legitimate_data = {
        'token_symbol': 'LEGIT',
        'price_change_1h_percent': 8.0,      # 8% in 1 hour
        'price_change_4h_percent': 15.0,     # 15% in 4 hours
        'price_change_24h_percent': 25.0,    # 25% in 24 hours (healthy growth)
        'volume_24h': 500000,                # $500k volume
        'volume_1h': 50000,                  # $50k in last hour
        'volume_4h': 200000,                 # $200k in 4 hours
        'market_cap': 5000000,               # $5M market cap (healthy ratio)
        'unique_trader_count': 150,          # Good trader diversity
        'trade_count_24h': 800,
        'creation_time': time.time() - (7 * 24 * 3600)  # 1 week old
    }
    
    print(f"Testing legitimate token scenario:")
    print(f"  - 24h price change: {legitimate_data['price_change_24h_percent']:+.1f}%")
    print(f"  - Volume/Market cap ratio: {legitimate_data['volume_24h']/legitimate_data['market_cap']:.2f}x")
    print(f"  - Unique traders: {legitimate_data['unique_trader_count']}")
    
    # Test pump/dump detection
    logger = LoggerSetup('TestPumpDumpDetection', log_level='DEBUG').logger
    detector = EnhancedPumpDumpDetector(logger=logger)
    pump_dump_analysis = detector.analyze_token(legitimate_data)
    
    print("\nLEGITIMATE TOKEN ANALYSIS:")
    print(f"  - Risk Level: {pump_dump_analysis.get('overall_risk_level', 'UNKNOWN')}")
    print(f"  - Risk Score: {pump_dump_analysis.get('risk_score', 0):.3f}")
    print(f"  - Warning Flags: {pump_dump_analysis.get('warning_flags', [])}")
    
    # Should be low risk
    risk_level = pump_dump_analysis.get('overall_risk_level', 'UNKNOWN')
    if risk_level in ['LOW', 'MINIMAL']:
        print("✅ SUCCESS: Legitimate token properly classified as low risk")
        return True
    else:
        print(f"⚠️  WARNING: Legitimate token classified as {risk_level} risk")
        return False

async def test_scoring_integration():
    """
    Test that the enhanced scoring system properly integrates pump/dump detection.
    """
    print("=" * 60)
    print("TESTING SCORING INTEGRATION")
    print("=" * 60)
    
    # Mock token data for TDCCP scenario
    token_data = {'address': 'mock_tdccp_address', 'symbol': 'TDCCP'}
    
    # Mock full data with TDCCP characteristics
    full_data = {
        'liquidity': 200000,  # High liquidity during pump
        'overview': {
            'symbol': 'TDCCP',
            'priceChange1h': 1500.0,    # 1500% in 1h
            'priceChange4h': 5000.0,    # 5000% in 4h  
            'priceChange24h': 750000.0, # 750,000% in 24h
            'volume': {
                'h1': 10000000,   # $10M in 1h
                'h4': 25000000,   # $25M in 4h
                'h24': 50000000   # $50M in 24h
            },
            'marketCap': 1000000,  # $1M market cap
            'price': 3.0
        },
        'top_traders': [f'trader_{i}' for i in range(8)]  # Only 8 traders
    }
    
    # Mock basic metrics
    basic_metrics = {
        'mock_tdccp_address': {
            'creation_time': time.time() - (12 * 3600)  # 12 hours old
        }
    }
    
    # Mock security data (clean)
    security_data = {
        'mock_tdccp_address': {
            'is_scam': False,
            'is_risky': False
        }
    }
    
    # Test the integrated scoring
    try:
        # Assuming EarlyTokenDetector constructor requires at least a logger instance.
        # The logger is passed as an argument to the test_scoring_integration function.
        detector = EarlyTokenDetector()
        score = await detector._calculate_comprehensive_score(
            token_data, full_data, basic_metrics, security_data
        )
        
        print(f"\nINTEGRATED SCORING RESULTS:")
        print(f"  - Final Score: {score:.1f}/100")
        
        if score < 70:  # Should be below alert threshold
            print("✅ SUCCESS: TDCCP scenario properly penalized in scoring")
            print(f"  - Score {score:.1f} is below alert threshold of 70")
            return True
        else:
            print("❌ FAILURE: TDCCP scenario not properly penalized")
            print(f"  - Score {score:.1f} is above alert threshold of 70")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in scoring integration test: {e}")
        return False

async def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("🚀 Starting Enhanced Pump & Dump Detection Tests")
    logger.info("=" * 80)
    
    # Initialize detector
    detector = EnhancedPumpDumpDetector(logger=logger)
    
    # Run tests
    test_results = []
    
    # Test 1: TDCCP pump scenario
    test_results.append(test_tdccp_scenario())
    
    # Test 2: TDCCP crash scenario
    test_results.append(test_tdccp_crash_scenario())
    
    # Test 3: Legitimate token scenario
    test_results.append(test_legitimate_token_scenario())
    
    # Test 4: Scoring integration
    test_results.append(await test_scoring_integration())
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(test_results)
    total = len(test_results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Enhanced detection working correctly!")
    else:
        logger.error(f"❌ {total - passed} tests failed - Review implementation")
    
    return passed == total

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 