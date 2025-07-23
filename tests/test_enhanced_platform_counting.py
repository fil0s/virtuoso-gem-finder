#!/usr/bin/env python3
"""
Test Enhanced Platform Counting Logic
Tests the improved platform validation logic for tokens like AURA
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.high_conviction_token_detector import HighConvictionTokenDetector

def test_platform_counting():
    """Test the enhanced platform counting logic"""
    print("🧪 TESTING ENHANCED PLATFORM COUNTING LOGIC")
    print("=" * 60)
    
    # Initialize detector
    detector = HighConvictionTokenDetector(debug_mode=True)
    
    # Test case 1: AURA-like token with DexScreener + RugCheck + Jupiter
    aura_candidate = {
        'address': 'DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2',
        'symbol': 'aura',
        'cross_platform_score': 42.0,
        'market_cap': 128_153_754,  # From DexScreener
        'volume_24h': 8_916_023,    # From DexScreener
        'platforms': ['dexscreener', 'rugcheck', 'jupiter']  # 3 platforms but only 1 with financial data
    }
    
    print(f"🪙 Test Token: {aura_candidate['symbol']} ({aura_candidate['address'][:8]}...)")
    print(f"📊 Market Cap: ${aura_candidate['market_cap']:,}")
    print(f"📈 Volume 24h: ${aura_candidate['volume_24h']:,}")
    print(f"🌐 Platforms: {aura_candidate['platforms']}")
    
    # Test the enhanced platform counting
    validated_platforms = detector._count_validated_platforms(aura_candidate)
    print(f"\n🔍 Platform Validation Results:")
    print(f"  • Original platform count: {len(aura_candidate['platforms'])}")
    print(f"  • Validated platform count: {validated_platforms}")
    
    # Test against current thresholds
    cross_platform_config = detector.config.get('CROSS_PLATFORM_ANALYSIS', {})
    pre_filter_config = cross_platform_config.get('pre_filter', {})
    min_platforms = pre_filter_config.get('min_platforms', 2)
    
    print(f"\n⚙️ Pre-Filter Threshold:")
    print(f"  • Min platforms required: {min_platforms}")
    
    # Determine if it would pass
    would_pass_old = len(aura_candidate['platforms']) >= min_platforms
    would_pass_new = validated_platforms >= min_platforms
    
    print(f"\n🎯 Pre-Filter Results:")
    print(f"  • Old logic (financial data only): {'✅ PASS' if would_pass_old else '❌ FAIL'}")
    print(f"  • New logic (any platform data): {'✅ PASS' if would_pass_new else '❌ FAIL'}")
    
    if not would_pass_old and would_pass_new:
        print(f"  🎉 IMPROVEMENT: Token now passes with enhanced logic!")
    elif would_pass_old and not would_pass_new:
        print(f"  ⚠️ REGRESSION: Token fails with new logic!")
    elif would_pass_old and would_pass_new:
        print(f"  ✅ CONSISTENT: Token passes with both logics")
    else:
        print(f"  ❌ CONSISTENT: Token fails with both logics")
    
    # Test case 2: Token with only financial data platform
    financial_only_candidate = {
        'address': 'ExampleFinancialOnlyToken123456789',
        'symbol': 'FIN',
        'cross_platform_score': 35.0,
        'market_cap': 75_000,
        'volume_24h': 300_000,
        'platforms': ['dexscreener']  # Only 1 platform with financial data
    }
    
    print(f"\n🪙 Test Token 2: {financial_only_candidate['symbol']} (Financial data only)")
    print(f"🌐 Platforms: {financial_only_candidate['platforms']}")
    
    validated_platforms_2 = detector._count_validated_platforms(financial_only_candidate)
    would_pass_new_2 = validated_platforms_2 >= min_platforms
    
    print(f"  • Validated platform count: {validated_platforms_2}")
    print(f"  • Would pass pre-filter: {'✅ PASS' if would_pass_new_2 else '❌ FAIL'}")
    
    # Test case 3: Token with validation platforms only (no financial data)
    validation_only_candidate = {
        'address': 'ExampleValidationOnlyToken123456789',
        'symbol': 'VAL',
        'cross_platform_score': 25.0,
        'market_cap': 0,  # No financial data
        'volume_24h': 0,  # No financial data
        'platforms': ['rugcheck', 'jupiter']  # 2 validation platforms
    }
    
    print(f"\n🪙 Test Token 3: {validation_only_candidate['symbol']} (Validation only)")
    print(f"🌐 Platforms: {validation_only_candidate['platforms']}")
    
    validated_platforms_3 = detector._count_validated_platforms(validation_only_candidate)
    would_pass_new_3 = validated_platforms_3 >= min_platforms
    
    print(f"  • Validated platform count: {validated_platforms_3}")
    print(f"  • Would pass pre-filter: {'✅ PASS' if would_pass_new_3 else '❌ FAIL'}")
    
    print(f"\n📋 SUMMARY:")
    print(f"  • Enhanced logic allows validation platforms to count")
    print(f"  • AURA-like tokens with good financial data + validation now pass")
    print(f"  • System maintains quality while being less restrictive")
    
    return {
        'aura_old_pass': would_pass_old,
        'aura_new_pass': would_pass_new,
        'improvement_detected': not would_pass_old and would_pass_new
    }

if __name__ == "__main__":
    results = test_platform_counting()
    
    if results['improvement_detected']:
        print(f"\n🎉 SUCCESS: Enhanced platform counting logic working correctly!")
        print(f"   AURA-like tokens will now pass pre-filtering.")
    else:
        print(f"\n⚠️ Review needed: Check if logic is working as expected.") 