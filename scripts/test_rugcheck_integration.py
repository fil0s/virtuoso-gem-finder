#!/usr/bin/env python3
"""
Test RugCheck Integration

This script tests the integration of RugCheck API with the token discovery strategies
to ensure security filtering works correctly in the discovery phase.
"""

import asyncio
import logging
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.rugcheck_connector import RugCheckConnector, RugRiskLevel
from api.birdeye_connector import BirdeyeAPI
from core.token_discovery_strategies import VolumeMomentumStrategy
from utils.env_loader import load_environment
from services.logger_setup import LoggerSetup


async def test_rugcheck_connector():
    """Test basic RugCheck connector functionality"""
    print("🧪 Testing RugCheck Connector...")
    
    # Initialize logger
    logger_setup = LoggerSetup("RugCheckTest")
    logger = logger_setup.logger
    
    # Initialize RugCheck connector
    rugcheck = RugCheckConnector(logger=logger)
    
    # Test tokens (mix of good and potentially risky tokens)
    test_tokens = [
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC (should be safe)
        "So11111111111111111111111111111111111111112",   # SOL wrapped (should be safe)
        # Add more test tokens as needed
    ]
    
    print(f"Testing {len(test_tokens)} tokens...")
    
    # Test individual analysis
    for token_address in test_tokens[:2]:  # Test first 2 tokens
        print(f"\n🔍 Analyzing {token_address}...")
        result = await rugcheck.analyze_token_security(token_address)
        
        print(f"  Risk Level: {result.risk_level.value}")
        print(f"  Score: {result.score}")
        print(f"  Healthy: {result.is_healthy}")
        print(f"  Issues: {len(result.issues)}")
        print(f"  Warnings: {len(result.warnings)}")
        print(f"  API Success: {result.api_success}")
        
        if result.issues:
            print(f"  Issues: {result.issues}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
    
    # Test batch analysis
    print(f"\n🔍 Testing batch analysis...")
    batch_results = await rugcheck.batch_analyze_tokens(test_tokens)
    
    print(f"Batch analysis complete: {len(batch_results)} results")
    for token_address, result in batch_results.items():
        print(f"  {token_address}: {result.risk_level.value} (Healthy: {result.is_healthy})")
    
    return batch_results


async def test_strategy_integration():
    """Test RugCheck integration with token discovery strategies"""
    print("\n🧪 Testing Strategy Integration...")
    
    # Load environment variables
    load_environment()
    import os
    api_key = os.getenv("BIRDEYE_API_KEY")
    if not api_key:
        print("❌ BIRDEYE_API_KEY not found in environment")
        return
    
    # Initialize APIs
    logger_setup = LoggerSetup("StrategyTest")
    logger = logger_setup.logger
    
    # Create a config dict for BirdeyeAPI
    config = {
        'api_key': api_key,
        'base_url': 'https://public-api.birdeye.so',
        'rate_limit': 100,
        'request_timeout_seconds': 20,
        'cache_ttl_default_seconds': 300,
        'cache_ttl_error_seconds': 60,
        'max_retries': 3,
        'backoff_factor': 2
    }
    
    # Import cache manager and rate limiter
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_api = BirdeyeAPI(
        config=config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    # Test strategy with RugCheck enabled
    print("\n🛡️ Testing strategy with RugCheck enabled...")
    strategy_with_rugcheck = VolumeMomentumStrategy(logger=logger)
    
    # Execute strategy (this will include RugCheck filtering)
    tokens_with_rugcheck = await strategy_with_rugcheck.execute(birdeye_api, scan_id="rugcheck_test")
    
    print(f"Strategy with RugCheck found {len(tokens_with_rugcheck)} tokens")
    
    # Display results
    for token in tokens_with_rugcheck[:5]:  # Show first 5 tokens
        token_address = token.get("address", "Unknown")
        security_analysis = token.get("security_analysis", {})
        
        print(f"  Token: {token_address}")
        print(f"    Risk Level: {security_analysis.get('risk_level', 'Unknown')}")
        print(f"    Score: {security_analysis.get('rugcheck_score', 'N/A')}")
        print(f"    Issues: {security_analysis.get('issues_count', 0)}")
        print(f"    Warnings: {security_analysis.get('warnings_count', 0)}")
    
    # Test strategy with RugCheck disabled for comparison
    print("\n⚠️ Testing strategy with RugCheck disabled...")
    
    # Create a new strategy instance with RugCheck disabled
    class VolumeMomentumStrategyNoRugCheck(VolumeMomentumStrategy):
        def __init__(self, logger=None):
            super().__init__(logger=logger)
            self.enable_rugcheck_filtering = False
            self.rugcheck_connector = None
    
    strategy_without_rugcheck = VolumeMomentumStrategyNoRugCheck(logger=logger)
    tokens_without_rugcheck = await strategy_without_rugcheck.execute(birdeye_api, scan_id="no_rugcheck_test")
    
    print(f"Strategy without RugCheck found {len(tokens_without_rugcheck)} tokens")
    
    # Compare results
    print(f"\n📊 Comparison:")
    print(f"  With RugCheck: {len(tokens_with_rugcheck)} tokens")
    print(f"  Without RugCheck: {len(tokens_without_rugcheck)} tokens")
    print(f"  Filtered out: {len(tokens_without_rugcheck) - len(tokens_with_rugcheck)} tokens")
    
    return {
        "with_rugcheck": tokens_with_rugcheck,
        "without_rugcheck": tokens_without_rugcheck
    }


async def test_risk_level_classification():
    """Test risk level classification logic"""
    print("\n🧪 Testing Risk Level Classification...")
    
    logger_setup = LoggerSetup("RiskClassificationTest")
    logger = logger_setup.logger
    
    rugcheck = RugCheckConnector(logger=logger)
    
    # Test different risk scenarios
    test_scenarios = [
        {
            "name": "High Score Safe Token",
            "score": 95.0,
            "issues": [],
            "warnings": [],
            "expected": RugRiskLevel.SAFE
        },
        {
            "name": "Medium Score Token",
            "score": 65.0,
            "issues": [],
            "warnings": ["minor warning"],
            "expected": RugRiskLevel.LOW_RISK
        },
        {
            "name": "Low Score Token",
            "score": 45.0,
            "issues": [],
            "warnings": ["warning1", "warning2"],
            "expected": RugRiskLevel.MEDIUM_RISK
        },
        {
            "name": "Very Low Score Token",
            "score": 20.0,
            "issues": [],
            "warnings": [],
            "expected": RugRiskLevel.HIGH_RISK
        },
        {
            "name": "Token with Honeypot",
            "score": 80.0,
            "issues": ["honeypot detected"],
            "warnings": [],
            "expected": RugRiskLevel.CRITICAL_RISK
        }
    ]
    
    for scenario in test_scenarios:
        risk_level = rugcheck._calculate_risk_level(
            scenario["score"],
            scenario["issues"],
            scenario["warnings"]
        )
        
        is_healthy = rugcheck._is_token_healthy(
            risk_level,
            scenario["issues"],
            scenario["score"]
        )
        
        print(f"  {scenario['name']}:")
        print(f"    Score: {scenario['score']}")
        print(f"    Issues: {len(scenario['issues'])}")
        print(f"    Warnings: {len(scenario['warnings'])}")
        print(f"    Expected Risk: {scenario['expected'].value}")
        print(f"    Actual Risk: {risk_level.value}")
        print(f"    Healthy: {is_healthy}")
        print(f"    Test: {'✅ PASS' if risk_level == scenario['expected'] else '❌ FAIL'}")
        print()


async def main():
    """Run all RugCheck integration tests"""
    print("🚀 Starting RugCheck Integration Tests...")
    print("=" * 60)
    
    try:
        # Test 1: Basic RugCheck connector
        await test_rugcheck_connector()
        
        # Test 2: Risk level classification
        await test_risk_level_classification()
        
        # Test 3: Strategy integration
        await test_strategy_integration()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 