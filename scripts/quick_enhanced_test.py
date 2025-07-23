#!/usr/bin/env python3
"""
Quick test of enhanced High Trading Activity Strategy
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from utils.env_loader import load_environment
import yaml

async def quick_test():
    load_environment()
    
    # Try enhanced config first, fallback to regular config
    config_file = 'config/config.enhanced.yaml'
    if not os.path.exists(config_file):
        config_file = 'config/config.yaml'
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    from services.logger_setup import LoggerSetup
    
    logger_setup = LoggerSetup('QuickTest')
    logger = logger_setup.logger
    
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_config['api_key'] = os.environ.get('BIRDEYE_API_KEY')
    
    birdeye_api = BirdeyeAPI(
        config=birdeye_config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    strategy = HighTradingActivityStrategy(logger=logger)
    
    print('🧪 Testing enhanced High Trading Activity Strategy...')
    try:
        tokens = await strategy.execute(birdeye_api)
        print(f'✅ Found {len(tokens)} tokens')
        
        if tokens:
            sample_token = tokens[0]
            print(f'📊 Sample token analysis:')
            print(f'   Address: {sample_token.get("address", "N/A")}')
            print(f'   Symbol: {sample_token.get("symbol", "N/A")}')
            print(f'   Is Trending: {sample_token.get("is_trending", False)}')
            print(f'   Smart Money Detected: {sample_token.get("smart_money_detected", False)}')
            print(f'   Holder Risk Level: {sample_token.get("holder_risk_level", "unknown")}')
            print(f'   Enhanced Score: {sample_token.get("enhanced_score", "N/A")}')
            
            # Check enhancement factors
            enhancement_factors = sample_token.get("enhancement_factors", [])
            if enhancement_factors:
                print(f'   Enhancement Factors: {", ".join(enhancement_factors)}')
            
            # Check enhancement summary
            enhancement_summary = sample_token.get("enhancement_summary", {})
            if enhancement_summary:
                print(f'   Enhancement Summary:')
                print(f'     - Trending: {enhancement_summary.get("is_trending", False)}')
                print(f'     - Smart Money: {enhancement_summary.get("smart_money_detected", False)}')
                print(f'     - Holder Risk: {enhancement_summary.get("holder_risk_level", "unknown")}')
                print(f'     - Total Boost: {enhancement_summary.get("total_boost_factor", 1.0):.2f}x')
        else:
            print('⚠️ No tokens found - this could be due to market conditions or filtering')
            
    except Exception as e:
        print(f'❌ Error during strategy execution: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test()) 