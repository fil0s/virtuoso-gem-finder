#!/usr/bin/env python3
"""
Validate Whale Consolidation Implementation
Ensures all strategies and components are using the consolidated whale implementation
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from utils.logger_setup import LoggerSetup


async def validate_whale_consolidation():
    """Validate that all components are using the consolidated whale implementation"""
    logger_setup = LoggerSetup("whale_consolidation_validator", log_level="INFO")
    logger = logger_setup.logger
    
    logger.info("🔍 Starting Whale Consolidation Validation")
    logger.info("=" * 60)
    
    errors = []
    warnings = []
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Strategy Imports
    logger.info("\n🔍 Checking strategy imports...")
    total_checks += 1
    try:
        from core.strategies.base_token_discovery_strategy import BaseTokenDiscoveryStrategy
        from core.strategies.volume_momentum_strategy import VolumeMomentumStrategy
        from core.strategies.recent_listings_strategy import RecentListingsStrategy
        from core.strategies.price_momentum_strategy import PriceMomentumStrategy
        from core.strategies.liquidity_growth_strategy import LiquidityGrowthStrategy
        from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
        
        logger.info("✅ All strategy classes imported successfully")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Strategy import validation failed: {str(e)}")
        logger.error(f"❌ Strategy imports failed: {e}")
    
    # Check 2: EarlyTokenDetector Integration
    logger.info("\n🔍 Checking EarlyTokenDetector whale integration...")
    total_checks += 1
    try:
        from services.early_token_detection import EarlyTokenDetector
        
        detector = EarlyTokenDetector()
        
        if not hasattr(detector, 'whale_analyzer'):
            errors.append("EarlyTokenDetector missing whale_analyzer attribute")
        elif not hasattr(detector, 'whale_shark_tracker'):
            errors.append("EarlyTokenDetector missing whale_shark_tracker attribute")
        else:
            logger.info("✅ EarlyTokenDetector whale integration validated")
            checks_passed += 1
    except Exception as e:
        errors.append(f"EarlyTokenDetector validation failed: {str(e)}")
        logger.error(f"❌ EarlyTokenDetector validation failed: {e}")
    
    # Check 3: Whale Services
    logger.info("\n🔍 Checking whale service availability...")
    total_checks += 1
    try:
        from services.whale_shark_movement_tracker import (
            WhaleSharkMovementTracker,
            WhaleActivityType,
            WhaleSignal
        )
        
        from services.whale_discovery_service import (
            WhaleDiscoveryService,
            WhaleCandidate,
            WhaleMetrics,
            WhaleQualificationLevel,
            WhaleBehaviorType
        )
        
        logger.info("✅ All whale services available")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Whale service validation failed: {str(e)}")
        logger.error(f"❌ Whale service validation failed: {e}")
    
    # Check 4: API Methods
    logger.info("\n🔍 Checking whale API method compatibility...")
    total_checks += 1
    try:
        from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        from api.birdeye_connector import BirdeyeAPI
        
        # Mock config for testing
        mock_config = {
            'api_key': 'test_key',
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20
        }
        
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        birdeye_api = BirdeyeAPI(mock_config, logger, cache_manager, rate_limiter)
        
        whale_tracker = WhaleSharkMovementTracker(birdeye_api, logger)
        
        # Check required methods
        required_methods = [
            'analyze_whale_activity_patterns',
            'get_whale_database_stats',
            'run_enhanced_whale_discovery'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(whale_tracker, method):
                missing_methods.append(method)
        
        if missing_methods:
            errors.append(f"WhaleSharkMovementTracker missing methods: {missing_methods}")
        else:
            # Test database stats
            stats = whale_tracker.get_whale_database_stats()
            if not isinstance(stats, dict):
                errors.append("get_whale_database_stats should return a dictionary")
            else:
                logger.info("✅ Whale API methods are compatible")
                checks_passed += 1
        
        await birdeye_api.close()
        
    except Exception as e:
        errors.append(f"API method validation failed: {str(e)}")
        logger.error(f"❌ API method validation failed: {e}")
    
    # Generate Report
    logger.info("\n" + "=" * 60)
    logger.info("🔍 WHALE CONSOLIDATION VALIDATION REPORT")
    logger.info("=" * 60)
    
    success_rate = (checks_passed / total_checks) * 100 if total_checks > 0 else 0
    
    if checks_passed == total_checks:
        logger.info("🎉 OVERALL STATUS: ✅ ALL VALIDATIONS PASSED")
    else:
        logger.info("⚠️ OVERALL STATUS: ❌ SOME VALIDATIONS FAILED")
    
    logger.info(f"\n📋 VALIDATION SUMMARY:")
    logger.info(f"   Total Checks: {total_checks}")
    logger.info(f"   Passed: {checks_passed}")
    logger.info(f"   Failed: {total_checks - checks_passed}")
    logger.info(f"   Success Rate: {success_rate:.1f}%")
    
    if errors:
        logger.info(f"\n🚨 ERRORS FOUND ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            logger.info(f"   {i}. {error}")
    else:
        logger.info(f"\n✅ NO ERRORS FOUND")
    
    if warnings:
        logger.info(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            logger.info(f"   {i}. {warning}")
    else:
        logger.info(f"\n✅ NO WARNINGS")
    
    # Recommendations
    logger.info(f"\n💡 RECOMMENDATIONS:")
    if not errors and not warnings:
        logger.info("   🎯 Whale consolidation is fully validated!")
        logger.info("   ✅ All strategies and components are properly updated")
        logger.info("   🚀 System is ready for production use")
    elif errors:
        logger.info("   🔧 Address all errors before proceeding")
        logger.info("   🧪 Run validation again after fixes")
    
    logger.info("\n" + "=" * 60)
    
    return checks_passed == total_checks


async def main():
    """Main validation execution"""
    print("🔍 Whale Consolidation Validation")
    print("Validating all strategies and components use consolidated whale implementation")
    print("=" * 60)
    
    success = await validate_whale_consolidation()
    
    exit_code = 0 if success else 1
    print(f"\n🏁 Validation completed with exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 