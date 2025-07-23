#!/usr/bin/env python3
"""
Quick test for the 3 previously failing Birdeye endpoints
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup

async def test_fixed_endpoints():
    """Test the 3 endpoints that were failing before our fixes"""
    
    # Setup
    logger_setup = LoggerSetup('EndpointFixer', log_level='INFO')
    logger = logger_setup.logger
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_api = BirdeyeAPI(
        config=birdeye_config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    test_token = 'So11111111111111111111111111111111111111112'  # SOL
    
    logger.info("🔧 Testing fixed endpoints...")
    
    # Clear relevant caches to test fresh
    cache_manager.delete("birdeye_gainers_losers_24h")
    cache_manager.delete("birdeye_new_listings")
    cache_manager.delete(f"birdeye_top_traders_{test_token}")
    logger.info("Cleared caches for fresh testing")
    
    # Test 1: get_gainers_losers
    logger.info("1. Testing get_gainers_losers...")
    try:
        gainers_losers = await birdeye_api.get_gainers_losers(timeframe="24h")
        if isinstance(gainers_losers, list):
            logger.info(f"✅ get_gainers_losers: SUCCESS - Got {len(gainers_losers)} items")
        else:
            logger.error(f"❌ get_gainers_losers: FAIL - Got {type(gainers_losers)}")
    except Exception as e:
        logger.error(f"❌ get_gainers_losers: FAIL - {e}")
    
    await asyncio.sleep(1)
    
    # Test 2: get_new_listings
    logger.info("2. Testing get_new_listings...")
    try:
        new_listings = await birdeye_api.get_new_listings()
        if isinstance(new_listings, list):
            logger.info(f"✅ get_new_listings: SUCCESS - Got {len(new_listings)} items")
        else:
            logger.error(f"❌ get_new_listings: FAIL - Got {type(new_listings)}")
    except Exception as e:
        logger.error(f"❌ get_new_listings: FAIL - {e}")
    
    await asyncio.sleep(1)
    
    # Test 3: get_top_traders
    logger.info("3. Testing get_top_traders...")
    try:
        top_traders = await birdeye_api.get_top_traders(test_token)
        if isinstance(top_traders, list):
            logger.info(f"✅ get_top_traders: SUCCESS - Got {len(top_traders)} items")
        else:
            logger.error(f"❌ get_top_traders: FAIL - Got {type(top_traders)}")
    except Exception as e:
        logger.error(f"❌ get_top_traders: FAIL - {e}")
    
    logger.info("🏁 Fixed endpoints test completed!")

if __name__ == "__main__":
    asyncio.run(test_fixed_endpoints()) 