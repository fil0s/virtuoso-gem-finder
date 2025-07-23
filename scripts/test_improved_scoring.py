#!/usr/bin/env python3
"""
Test script to validate the improved scoring approach.

This script tests the new philosophy: "Catch rockets, avoid manipulation"
- TDCCP should still be flagged due to manipulation indicators
- Legitimate moonshots should score high
- Price movements alone should not cause penalties
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
from services.early_token_detection import EarlyTokenDetector
from services.logger_setup import LoggerSetup

def setup_logging():
    """Setup logging for testing."""
    logger_setup = LoggerSetup('TestImprovedScoring', log_level='DEBUG')
    return logger_setup.logger

async def test_tdccp_with_new_approach():
    """Test TDCCP with the new manipulation-focused approach."""
    print("=" * 60)
    print("TESTING TDCCP WITH NEW APPROACH")
    print("=" * 60)
    
    # Mock TDCCP data during pump phase
    token_data = {
        'address': 'tdccp_test_address',
        'symbol': 'TDCCP'
    }
    
    # Full data with TDCCP's characteristics
    full_data = {
        'overview': {
            'symbol': 'TDCCP',
            'priceChange1h': 1500.0,      # 1500% in 1h
            'priceChange4h': 5000.0,      # 5000% in 4h  
            'priceChange24h': 750000.0,   # 750,000% in 24h
            'volume': {
                'h1': 10000000,    # $10M in 1h
                'h4': 25000000,    # $25M in 4h
                'h24': 50000000    # $50M in 24h
            },
            'marketCap': 1000000,  # $1M market cap (50x volume ratio!)
            'liquidity': 2000000,  # $2M liquidity
            'price': 3.0
        },
        'top_traders': [f'trader_{i}' for i in range(8)]  # Only 8 traders for $50M!
    }
    
    # Basic metrics
    basic_metrics = {
        'tdccp_test_address': {
            'creation_time': time.time() - (12 * 3600)  # 12 hours old
        }
    }
    
    # Security data (clean)
    security_data = {
        'tdccp_test_address': {
            'is_scam': False,
            'is_risky': False
        }
    }
    
    detector = EarlyTokenDetector()
    score = await detector._calculate_comprehensive_score(
        token_data, full_data, basic_metrics, security_data
    )
    
    print(f"\nTDCCP NEW APPROACH RESULTS:")
    print(f"  🎯 Final Score: {score:.1f}/100")
    print(f"  📊 Expected: Should still be low due to manipulation indicators")
    print(f"  🔍 Key factors:")
    print(f"    - Volume/Market Cap: 50x (extreme manipulation)")
    print(f"    - Trader concentration: 8 traders for $50M")
    print(f"    - Price gains: Should be REWARDED, not penalized")
    
    return score

async def test_legitimate_moonshot():
    """Test a legitimate token with extreme gains but organic patterns."""
    print("\n" + "=" * 60)
    print("TESTING LEGITIMATE MOONSHOT")
    print("=" * 60)
    
    # Mock legitimate moonshot data
    token_data = {
        'address': 'moonshot_test_address',
        'symbol': 'MOON'
    }
    
    # Full data with legitimate moonshot characteristics
    full_data = {
        'overview': {
            'symbol': 'MOON',
            'priceChange1h': 50.0,        # 50% in 1h (good momentum)
            'priceChange4h': 150.0,       # 150% in 4h  
            'priceChange24h': 800.0,      # 800% in 24h (still extreme!)
            'volume': {
                'h1': 500000,      # $500K in 1h
                'h4': 1500000,     # $1.5M in 4h
                'h24': 5000000     # $5M in 24h
            },
            'marketCap': 10000000,  # $10M market cap (0.5x volume ratio - healthy!)
            'liquidity': 3000000,   # $3M liquidity
            'price': 2.5
        },
        'top_traders': [f'trader_{i}' for i in range(200)]  # 200 diverse traders
    }
    
    # Basic metrics
    basic_metrics = {
        'moonshot_test_address': {
            'creation_time': time.time() - (7 * 24 * 3600)  # 1 week old
        }
    }
    
    # Security data (clean)
    security_data = {
        'moonshot_test_address': {
            'is_scam': False,
            'is_risky': False
        }
    }
    
    detector = EarlyTokenDetector()
    score = await detector._calculate_comprehensive_score(
        token_data, full_data, basic_metrics, security_data
    )
    
    print(f"\nLEGITIMATE MOONSHOT RESULTS:")
    print(f"  🚀 Final Score: {score:.1f}/100")
    print(f"  📊 Expected: Should be HIGH due to organic growth patterns")
    print(f"  🔍 Key factors:")
    print(f"    - Volume/Market Cap: 0.5x (healthy ratio)")
    print(f"    - Trader diversity: 200 traders")
    print(f"    - Price gains: 800% should be REWARDED")
    print(f"    - Age: 1 week (established but still early)")
    
    return score

async def test_moderate_performer():
    """Test a token with moderate gains (what old system preferred)."""
    print("\n" + "=" * 60)
    print("TESTING MODERATE PERFORMER")
    print("=" * 60)
    
    # Mock moderate performer data
    token_data = {
        'address': 'moderate_test_address',
        'symbol': 'MOD'
    }
    
    # Full data with moderate characteristics
    full_data = {
        'overview': {
            'symbol': 'MOD',
            'priceChange1h': 5.0,         # 5% in 1h
            'priceChange4h': 12.0,        # 12% in 4h  
            'priceChange24h': 25.0,       # 25% in 24h (moderate)
            'volume': {
                'h1': 100000,      # $100K in 1h
                'h4': 300000,      # $300K in 4h
                'h24': 800000      # $800K in 24h
            },
            'marketCap': 8000000,   # $8M market cap (0.1x volume ratio - very healthy)
            'liquidity': 1500000,   # $1.5M liquidity
            'price': 1.2
        },
        'top_traders': [f'trader_{i}' for i in range(100)]  # 100 traders
    }
    
    # Basic metrics
    basic_metrics = {
        'moderate_test_address': {
            'creation_time': time.time() - (3 * 24 * 3600)  # 3 days old
        }
    }
    
    # Security data (clean)
    security_data = {
        'moderate_test_address': {
            'is_scam': False,
            'is_risky': False
        }
    }
    
    detector = EarlyTokenDetector()
    score = await detector._calculate_comprehensive_score(
        token_data, full_data, basic_metrics, security_data
    )
    
    print(f"\nMODERATE PERFORMER RESULTS:")
    print(f"  📈 Final Score: {score:.1f}/100")
    print(f"  📊 Expected: Should be LOWER than moonshot despite being 'safer'")
    print(f"  🔍 Key factors:")
    print(f"    - Volume/Market Cap: 0.1x (very healthy)")
    print(f"    - Trader diversity: 100 traders")
    print(f"    - Price gains: Only 25% (less exciting for early detection)")
    
    return score

async def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("🚀 Testing Improved Scoring Approach")
    logger.info("PHILOSOPHY: Catch rockets, avoid manipulation")
    logger.info("=" * 80)
    
    # Run tests
    tdccp_score = await test_tdccp_with_new_approach()
    moonshot_score = await test_legitimate_moonshot()
    moderate_score = await test_moderate_performer()
    
    # Analysis
    logger.info("\n" + "=" * 80)
    logger.info("COMPARATIVE ANALYSIS")
    logger.info("=" * 80)
    
    logger.info(f"TDCCP (Manipulation):     {tdccp_score:.1f}/100")
    logger.info(f"Legitimate Moonshot:      {moonshot_score:.1f}/100")
    logger.info(f"Moderate Performer:       {moderate_score:.1f}/100")
    
    logger.info("\nEXPECTED RANKING (new philosophy):")
    logger.info("1. 🥇 Legitimate Moonshot (high gains + organic)")
    logger.info("2. 🥈 Moderate Performer (healthy but less exciting)")
    logger.info("3. 🥉 TDCCP (manipulation detected)")
    
    # Validate results
    success = True
    if moonshot_score <= moderate_score:
        logger.warning("⚠️  ISSUE: Moonshot should score higher than moderate performer!")
        success = False
    
    if tdccp_score >= 70:
        logger.warning("⚠️  ISSUE: TDCCP should still be below alert threshold!")
        success = False
    
    if moonshot_score >= 70:
        logger.info("✅ SUCCESS: Legitimate moonshot scores above alert threshold!")
    else:
        logger.warning("⚠️  ISSUE: Legitimate moonshot should trigger alerts!")
        success = False
    
    logger.info(f"\n🎯 OVERALL RESULT: {'SUCCESS' if success else 'NEEDS ADJUSTMENT'}")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 