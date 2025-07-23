#!/usr/bin/env python3
"""
Debug Price Momentum Strategy

Specific test to understand why Price Momentum Strategy is finding 0 tokens.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from core.strategies.price_momentum_strategy import PriceMomentumStrategy
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService


async def debug_price_momentum():
    """Debug Price Momentum Strategy step by step."""
    print("🔧 Debugging Price Momentum Strategy")
    print("=" * 50)
    
    # Initialize logger
    logger_setup = LoggerSetup("DebugTest")
    logger = logger_setup.logger
    
    try:
        # Initialize Birdeye API (same pattern as test_strategy_fixes.py)
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            print("❌ BIRDEYE_API_KEY not set")
            return
        
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
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
        
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
        
        # Initialize strategy
        strategy = PriceMomentumStrategy(logger=logger)
        
        print(f"📊 API Parameters: {strategy.api_parameters}")
        print(f"📊 Confluence Threshold: {strategy.confluence_threshold}")
        print()
        
        # Step 1: Test API call
        print("🔍 Step 1: Testing API call...")
        scan_id = f"debug_price_momentum_{int(datetime.now().timestamp())}"
        
        # Check if API parameters are too restrictive
        print("🔍 Current API parameters:")
        for key, value in strategy.api_parameters.items():
            if isinstance(value, (int, float)):
                print(f"   {key}: {value:,}")
            else:
                print(f"   {key}: {value}")
        
        # Get initial tokens from API
        tokens = await strategy.execute(birdeye_api, scan_id=scan_id)
        print(f"✅ API returned {len(tokens)} tokens")
        
        if len(tokens) == 0:
            print("❌ No tokens returned from strategy - checking if API parameters are too restrictive...")
            
            # Test with the strategy's current API parameters directly
            print("🔄 Testing direct API call with strategy's parameters...")
            api_tokens = await birdeye_api.get_token_list(**strategy.api_parameters)
            print(f"✅ Direct API call returned {len(api_tokens)} tokens")
            
            if len(api_tokens) == 0:
                print("❌ Even direct API call returns 0 tokens - API parameters are too restrictive!")
                
                # Try with more relaxed API parameters
                relaxed_params = {
                    "sort_by": "price_change_24h_percent",
                    "sort_type": "desc", 
                    "min_volume_24h_usd": 10000,  # Much lower than 100,000
                    "min_liquidity": 50000,       # Much lower than 300,000
                    "min_trade_24h_count": 100,   # Much lower than 700
                    "limit": 25
                }
                
                print(f"🔄 Trying with relaxed params:")
                for key, value in relaxed_params.items():
                    print(f"   {key}: {value:,}")
                
                # Test with relaxed parameters directly
                api_tokens = await birdeye_api.get_token_list(**relaxed_params)
                print(f"✅ Relaxed API returned {len(api_tokens)} tokens")
                
                if len(api_tokens) > 0:
                    print("🎯 Found tokens with relaxed parameters!")
                    print(f"📊 Sample token: {api_tokens[0].get('symbol', 'Unknown')} - Price change: {api_tokens[0].get('price_change_24h_percent', 0):.2f}%")
                    
                    # Test momentum analysis on first token
                    print("\n🔍 Step 2: Testing momentum analysis...")
                    test_token = api_tokens[0]
                    
                    # Simulate momentum analysis
                    momentum_analysis = await strategy._analyze_price_momentum(test_token, birdeye_api)
                    print(f"📈 Momentum analysis result: {momentum_analysis}")
                    
                    confluence_score = momentum_analysis.get("confluence_score", 0.0)
                    print(f"📊 Confluence score: {confluence_score:.3f} (threshold: {strategy.confluence_threshold:.3f})")
                    
                    if confluence_score >= strategy.confluence_threshold:
                        print("✅ Token would pass confluence check!")
                    else:
                        print(f"❌ Token would fail confluence check: {confluence_score:.3f} < {strategy.confluence_threshold:.3f}")
                else:
                    print("❌ Even relaxed parameters return no tokens - market conditions issue")
            else:
                print(f"✅ Direct API call found tokens - issue is in strategy processing")
                print(f"📊 Sample tokens from direct API call:")
                # Fix the slice error by ensuring we have a proper list
                sample_tokens = api_tokens[:3] if isinstance(api_tokens, list) else list(api_tokens)[:3]
                for i, token in enumerate(sample_tokens):
                    if isinstance(token, dict):
                        symbol = token.get('symbol', 'Unknown')
                        price_change = token.get('price_change_24h_percent', 0)
                        volume = token.get('volume_24h_usd', 0)
                        print(f"   {i+1}. {symbol}: {price_change:.1f}% change, ${volume:,.0f} volume")
        else:
            print("✅ Strategy found tokens - processing them...")
            for i, token in enumerate(tokens[:3]):  # Show first 3
                print(f"🎯 Token {i+1}: {token.get('symbol', 'Unknown')} - Score: {token.get('strategy_score', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await birdeye_api.close()
    
    print("\n" + "=" * 50)
    print("🔧 Debug complete!")


if __name__ == "__main__":
    asyncio.run(debug_price_momentum()) 