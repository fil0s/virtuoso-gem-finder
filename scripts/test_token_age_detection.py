#!/usr/bin/env python
"""
Test script for token age detection and timeframe selection.
This script verifies that the token-age aware timeframe selection works correctly.
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Improve path handling to avoid import errors
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer
from api.birdeye_connector import BirdeyeAPI
from api.cache_manager import CacheManager
from api.rate_limiter_service import RateLimiterService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('token_age_test')

# Test tokens at different age levels
TEST_TOKENS = [
    # Format: (token_address, token_symbol, expected_age_category)
    # Add tokens with different age categories:
    # 'new' (< 24h), 'recent' (1-3 days), 'developing' (3-7 days), 'established' (> 7 days)
    # Note: These expectations may change as tokens age, so this is just for initial testing
    ("LGvhMduuqQC4ygDXMYvKsEx56Qw8MGxu1W1XMY8P9o3", "BUBBLE", "established"),  # Example established token
    ("RAYC1hmQiXvw2YYW6EsYGFm5KQ1YMbwcJ8WC4CJBpnVm", "RAYC", "established"),   # Example established token
    # Add more tokens as needed for testing
]

async def init_api():
    """Initialize the API connector with proper configuration"""
    
    # Check for API key
    birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
    if not birdeye_api_key:
        logger.error("BIRDEYE_API_KEY environment variable is required")
        sys.exit(1)
    
    # Initialize cache manager
    cache_manager = CacheManager(logger=logger)
    
    # Initialize rate limiter
    rate_limiter = RateLimiterService(logger=logger)
    
    # Configure API
    config = {
        'api_key': birdeye_api_key,
        'base_url': 'https://public-api.birdeye.so',
        'rate_limit': 100,  # requests per minute
        'request_timeout_seconds': 30,
        'cache_ttl_default_seconds': 300,
        'cache_ttl_error_seconds': 60,
        'max_retries': 3,
        'backoff_factor': 2
    }
    
    # Initialize Birdeye API connector
    api = BirdeyeAPI(
        config=config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    return api

async def test_token_age_detection():
    """Test token age detection and timeframe selection"""
    
    api = await init_api()
    
    # Initialize the trend confirmation analyzer
    birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
    analyzer = TrendConfirmationAnalyzer(birdeye_api_key, birdeye_api=api)
    
    results = []
    
    logger.info("Starting token age detection test")
    logger.info("=" * 80)
    
    for token_address, token_symbol, expected_age in TEST_TOKENS:
        logger.info(f"Testing token: {token_symbol} ({token_address})")
        
        try:
            # Get token age and category
            age_days, age_category = await analyzer.get_token_age(token_address)
            
            # Get security data for verification
            security_data = await api.get_token_security(token_address)
            creation_info = await api.get_token_creation_info(token_address)
            
            # Extract creation timestamp if available
            creation_time = None
            if security_data and 'createdTime' in security_data:
                creation_time = int(security_data['createdTime'])
            elif creation_info and 'createdTime' in creation_info:
                creation_time = int(creation_info['createdTime'])
                
            # Format creation time for display
            creation_time_str = "Unknown"
            if creation_time:
                creation_time_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get selected timeframes based on age
            selected_timeframes = analyzer.age_timeframe_map.get(age_category, analyzer.standard_timeframes)
            
            # Print results
            logger.info(f"  Token age: {age_days:.1f} days")
            logger.info(f"  Age category: {age_category}")
            logger.info(f"  Expected category: {expected_age}")
            logger.info(f"  Creation time: {creation_time_str}")
            logger.info(f"  Selected timeframes: {selected_timeframes}")
            
            # Record results
            results.append({
                "token_address": token_address,
                "token_symbol": token_symbol,
                "age_days": age_days,
                "age_category": age_category,
                "expected_category": expected_age,
                "creation_time": creation_time_str,
                "selected_timeframes": selected_timeframes,
                "match": age_category == expected_age
            })
            
            logger.info(f"  Test result: {'✅ PASS' if age_category == expected_age else '❌ FAIL'}")
            
        except Exception as e:
            logger.error(f"Error testing {token_symbol}: {e}")
            results.append({
                "token_address": token_address,
                "token_symbol": token_symbol,
                "error": str(e)
            })
        
        logger.info("-" * 80)
    
    # Output summary
    logger.info("Test Summary:")
    passed = sum(1 for r in results if r.get('match', False))
    total = len(TEST_TOKENS)
    logger.info(f"  Passed: {passed}/{total} tests")
    
    # Write results to file
    output_dir = project_root / "data" / "token_age_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"token_age_test_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_file}")
    
    return results

async def main():
    """Run the test script"""
    await test_token_age_detection()
    
if __name__ == "__main__":
    asyncio.run(main()) 