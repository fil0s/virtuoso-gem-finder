#!/usr/bin/env python
"""
Test script for token age detection and timeframe selection
This script validates the token-age aware timeframe selection logic
in the BirdeyeAPI connector.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, List, Any, Optional
import dotenv

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from utils.structured_logger import get_structured_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("token_age_test")
structured_logger = get_structured_logger("token_age_test")

# Token addresses for testing different age categories
TEST_TOKENS = {
    # Likely new tokens (adjust with actual new tokens)
    "new": [
        "EXvh36xGnRRw1D4z9eBdNU5YKbYxTCqCgFSbYNTEh83P",  # Recent token
        "AsvDeZZmKsjn5TUjLPEjrMQGUAYn8qAgbBnASU1EMNg5"   # Another recent token
    ],
    # Tokens that are a few days old
    "recent": [
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"   # USDT
    ],
    # Established tokens (weeks/months old)
    "established": [
        "So11111111111111111111111111111111111111112",  # SOL
        "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj"   # Established token
    ]
}

async def test_token_age_detection(birdeye_api: BirdeyeAPI):
    """Test token age detection logic"""
    logger.info("Testing token age detection...")
    
    for category, tokens in TEST_TOKENS.items():
        logger.info(f"Testing {category} tokens...")
        
        for token_address in tokens:
            try:
                # Get token age
                age_days, age_category = await birdeye_api.get_token_age(token_address)
                
                # Get token name for better logging
                token_overview = await birdeye_api.get_token_overview(token_address)
                token_name = token_overview.get('symbol', 'Unknown') if token_overview else 'Unknown'
                
                logger.info(f"Token: {token_name} ({token_address})")
                logger.info(f"  Age: {age_days:.2f} days")
                logger.info(f"  Category: {age_category}")
                
                # Validate auto timeframe selection
                ohlcv_data = await birdeye_api.get_ohlcv_data(token_address, time_frame='auto')
                logger.info(f"  OHLCV data points: {len(ohlcv_data)}")
                
                # Check if we have synthetic data for very new tokens
                has_synthetic = any(candle.get('synthetic', False) for candle in ohlcv_data) if ohlcv_data else False
                if has_synthetic:
                    logger.info(f"  Using synthetic OHLCV data")
                
                # Add a separator line for readability
                logger.info("-" * 50)
                
            except Exception as e:
                logger.error(f"Error testing token {token_address}: {e}")
    
    logger.info("Token age detection test completed.")

async def main():
    """Main test function"""
    logger.info("Starting token age detection test")
    
    # Load environment variables from .env file
    dotenv.load_dotenv()
    
    # Set up basic configuration manually
    config = {
        'cache': {
            'ttl_seconds': int(os.environ.get('CACHE_TTL', 300)),
            'enabled': os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
        },
        'rate_limiting': {
            'birdeye': {
                'requests_per_minute': int(os.environ.get('BIRDEYE_RATE_LIMIT', 100))
            }
        },
        'api': {
            'birdeye': {
                'api_key': os.environ.get('BIRDEYE_API_KEY', ''),
                'base_url': 'https://public-api.birdeye.so',
                'request_timeout_seconds': 20,
                'max_retries': 3
            }
        }
    }
    
    if not config['api']['birdeye']['api_key']:
        logger.error("BIRDEYE_API_KEY environment variable is not set")
        return
    
    # Setup services
    cache_manager = CacheManager(config.get('cache', {}))
    rate_limiter = RateLimiterService(config.get('rate_limiting', {}))
    
    # Initialize API
    birdeye_config = config.get('api', {}).get('birdeye', {})
    birdeye_api = BirdeyeAPI(birdeye_config, logger, cache_manager, rate_limiter)
    
    try:
        # Run test
        await test_token_age_detection(birdeye_api)
    finally:
        # Cleanup
        await birdeye_api.close_session()
        logger.info("Test completed, resources cleaned up")

if __name__ == "__main__":
    asyncio.run(main()) 