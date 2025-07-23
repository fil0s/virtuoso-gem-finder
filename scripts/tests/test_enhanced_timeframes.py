#!/usr/bin/env python
"""
Test script for enhanced timeframe selection with expanded token age categories
This script validates that the token-age aware timeframe selection logic
works correctly with the expanded timeframes and age categories.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime, timedelta

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer
from utils.structured_logger import get_structured_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TimeframeTest")
logger.setLevel(logging.INFO)

class TimeframeTestHelper:
    """Helper class to test enhanced timeframe selection logic"""
    
    def __init__(self):
        # Initialize cache manager
        self.cache_manager = CacheManager(ttl_default=300)
        
        # Initialize rate limiter with reasonable config
        self.rate_limiter = RateLimiterService(config={
            "enabled": True,
            "default_retry_interval": 1,
            "domains": {
                "default": {"calls": 5, "period": 1},
                "birdeye": {"calls": 10, "period": 1}
            }
        })
        
        # Load API key from environment variable
        self.api_key = os.environ.get('BIRDEYE_API_KEY')
        if not self.api_key:
            logger.warning("No BIRDEYE_API_KEY found in environment variables")
            
        # Initialize Birdeye API connector
        self.birdeye_api = BirdeyeAPI(
            config={
                'api_key': self.api_key,
                'base_url': 'https://public-api.birdeye.so',
                'request_timeout_seconds': 30,
                'cache_ttl_default_seconds': 300,
                'cache_ttl_error_seconds': 60,
                'max_retries': 3,
                'backoff_factor': 2,
                'rate_limit': 60
            },
            logger=logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Test tokens with various age ranges
        self.test_tokens = {
            # New tokens (modify these with real tokens in your tests)
            'ultra_new': '9TVjnzpF5JhdQkKBL9XrPLcSMWgem1FfbRKeCTiRhGZj',  # < 15 min
            'very_new': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',  # 15 min - 1 hour
            'new': 'LZsGxfkJKjt7ZQGQyNX8uvgBUUYs6SAMVByA4r3UKnY',  # 1-6 hours
            'very_recent': 'EBAeM3CLBg9ybbNcCXC5XyYADEZCRsx6RMgZpJQXMXwV',  # 6-24 hours
            
            # Older tokens (these can be real established tokens)
            'recent': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # 1-3 days (USDC)
            'developing': '7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj',  # 3-7 days
            'emerging': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # 7-14 days (USDT)
            'established': 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',  # 14-30 days
            'mature_3mo': 'So11111111111111111111111111111111111111112',  # 1-3 months (SOL)
            'mature_6mo': 'DUSTawucrTsGU8hcqRdHDCbuYhCPADMLM2VcCb8VnFnQ',  # 3-6 months
            'veteran': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263'  # > 6 months
        }
        
    async def get_token_age_info(self, token_address: str) -> Dict[str, Any]:
        """Get token age and appropriate timeframes for a given token"""
        
        logger.info(f"Testing token: {token_address}")
        
        # Get token age
        age_days, age_category = await self.birdeye_api.get_token_age(token_address)
        
        # Get auto-selected timeframe
        ohlcv_result = await self.birdeye_api.get_ohlcv_data(token_address, time_frame='auto', limit=30)
        
        # Try standard timeframes to check data availability
        timeframe_results = {}
        for timeframe in ['1s', '15s', '30s', '1m', '5m', '15m', '30m', '1h', '4h', '1d']:
            try:
                data = await self.birdeye_api.get_ohlcv_data(token_address, time_frame=timeframe, limit=10)
                timeframe_results[timeframe] = {
                    'available': bool(data and len(data) > 0),
                    'candle_count': len(data) if data else 0
                }
            except Exception as e:
                timeframe_results[timeframe] = {
                    'available': False,
                    'error': str(e)
                }
        
        # Return comprehensive info
        return {
            'token_address': token_address,
            'age_days': age_days,
            'age_category': age_category,
            'auto_timeframe_result': {
                'candle_count': len(ohlcv_result) if ohlcv_result else 0,
                'has_data': bool(ohlcv_result and len(ohlcv_result) > 0)
            },
            'timeframe_availability': timeframe_results,
            'timestamp': int(time.time()),
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run tests for all token age categories"""
        
        results = {}
        
        for category, token_address in self.test_tokens.items():
            try:
                logger.info(f"Testing {category} category with token {token_address}")
                token_results = await self.get_token_age_info(token_address)
                results[category] = token_results
            except Exception as e:
                logger.error(f"Error testing {category} category: {e}")
                results[category] = {
                    'token_address': token_address,
                    'error': str(e)
                }
        
        # Save results to file
        output_file = 'debug/token_analysis/enhanced_timeframe_test_results.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Test results saved to {output_file}")
        
        return results

async def main():
    """Main function to run the tests"""
    
    logger.info("Starting enhanced timeframe selection tests")
    
    test_helper = TimeframeTestHelper()
    results = await test_helper.run_tests()
    
    # Print summary
    logger.info("\n===== TIMEFRAME SELECTION TEST SUMMARY =====")
    
    for category, data in results.items():
        if 'error' in data:
            logger.error(f"{category}: ERROR - {data['error']}")
            continue
            
        logger.info(f"{category} ({data['age_days']:.2f} days): {data['age_category']}")
        
        if data['auto_timeframe_result']['has_data']:
            logger.info(f"  ✅ Auto timeframe returned {data['auto_timeframe_result']['candle_count']} candles")
        else:
            logger.warning(f"  ❌ Auto timeframe returned no data")
            
        # Show availability of different timeframes
        available = [tf for tf, info in data['timeframe_availability'].items() if info['available']]
        unavailable = [tf for tf, info in data['timeframe_availability'].items() if not info['available']]
        
        if available:
            logger.info(f"  📊 Available timeframes: {', '.join(available)}")
        if unavailable:
            logger.info(f"  🚫 Unavailable timeframes: {', '.join(unavailable)}")
            
        logger.info("-" * 40)
    
    logger.info("Enhanced timeframe selection tests completed")

if __name__ == "__main__":
    # Create directories if they don't exist
    os.makedirs("temp/app_cache", exist_ok=True)
    os.makedirs("debug/token_analysis", exist_ok=True)
    
    # Run test
    asyncio.run(main()) 