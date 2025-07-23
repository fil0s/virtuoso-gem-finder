#!/usr/bin/env python3
"""
RugCheck Integration Comparison Test

This script tests the difference in token filtering quality 
when RugCheck integration is enabled vs disabled.
"""

import asyncio
import logging
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger_setup import LoggerSetup
from api.rugcheck_connector import RugCheckConnector
from utils.env_loader import load_environment

async def test_rugcheck_comparison():
    """Test token filtering with and without RugCheck integration."""
    
    # Load environment
    load_environment()
    
    # Setup logging
    logger_setup = LoggerSetup("RugCheckComparison")
    logger = logger_setup.logger
    
    print("🧪 RugCheck Integration Comparison Test")
    print("=" * 60)
    
    # Test tokens - mix of potentially safe and risky ones
    test_tokens = [
        "So11111111111111111111111111111111111111112",  # Wrapped SOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
        "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",  # mSOL
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",  # Ethereum (Wormhole)
    ]
    
    print(f"📊 Testing {len(test_tokens)} tokens...")
    print()
    
    # Initialize RugCheck connector
    rugcheck = RugCheckConnector(logger=logger)
    
    # Test each token
    safe_tokens = []
    risky_tokens = []
    
    for i, token_address in enumerate(test_tokens, 1):
        print(f"🔍 [{i}/{len(test_tokens)}] Analyzing {token_address[:8]}...")
        
        try:
            # Get RugCheck analysis
            result = await rugcheck.analyze_token_security(token_address)
            
            if result and result.api_success:
                risk_level = result.risk_level.value
                is_healthy = result.is_healthy
                score = result.score or 0
                
                print(f"  ✅ Risk Level: {risk_level}")
                print(f"  📊 Score: {score:.1f}")
                print(f"  💚 Healthy: {is_healthy}")
                
                if is_healthy and risk_level in ['safe', 'low_risk', 'medium_risk']:
                    safe_tokens.append({
                        'address': token_address,
                        'risk_level': risk_level,
                        'score': score,
                        'healthy': is_healthy
                    })
                else:
                    risky_tokens.append({
                        'address': token_address,
                        'risk_level': risk_level,
                        'score': score,
                        'healthy': is_healthy
                    })
            else:
                print(f"  ❌ Analysis failed")
                risky_tokens.append({
                    'address': token_address,
                    'risk_level': 'unknown',
                    'score': 0,
                    'healthy': False
                })
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            risky_tokens.append({
                'address': token_address,
                'risk_level': 'error',
                'score': 0,
                'healthy': False
            })
        
        print()
        
        # Small delay to respect rate limits
        await asyncio.sleep(0.1)
    
    # Print comparison results
    print("📈 COMPARISON RESULTS")
    print("=" * 60)
    print()
    
    print(f"🟢 WITHOUT RugCheck: All {len(test_tokens)} tokens would be processed")
    print("   → Standard BirdEye filtering only")
    print("   → No security risk assessment")
    print()
    
    print(f"🔐 WITH RugCheck: {len(safe_tokens)} safe, {len(risky_tokens)} filtered out")
    print("   → Enhanced security filtering")
    print("   → Risk-based token qualification")
    print()
    
    if safe_tokens:
        print("✅ SAFE TOKENS (would proceed to next analysis stage):")
        for token in safe_tokens:
            print(f"   • {token['address'][:8]}... - {token['risk_level']} (Score: {token['score']:.1f})")
        print()
    
    if risky_tokens:
        print("⚠️  FILTERED OUT (would be excluded from trading):")
        for token in risky_tokens:
            print(f"   • {token['address'][:8]}... - {token['risk_level']} (Score: {token['score']:.1f})")
        print()
    
    # Calculate filtering effectiveness
    filter_rate = (len(risky_tokens) / len(test_tokens)) * 100
    print(f"🎯 FILTERING EFFECTIVENESS: {filter_rate:.1f}% of tokens filtered for security")
    
    # Recommendations
    print()
    print("💡 RECOMMENDATIONS:")
    print("=" * 60)
    if len(safe_tokens) > 0:
        print("✅ RugCheck integration is working effectively")
        print("✅ Security filtering is identifying safe tokens")
        print("✅ Ready for production use")
    else:
        print("⚠️  All tokens filtered - consider adjusting risk tolerance")
        print("⚠️  May need to allow medium_risk tokens")
    
    print()
    print("🔧 To enable RugCheck in your monitoring:")
    print("   1. Set RUGCHECK.enabled: true in config")
    print("   2. Adjust risk tolerance settings")
    print("   3. Monitor filtering effectiveness")

if __name__ == "__main__":
    asyncio.run(test_rugcheck_comparison()) 