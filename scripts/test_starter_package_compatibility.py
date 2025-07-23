#!/usr/bin/env python3
"""
Test Starter Package Compatibility

This script tests the new Starter package compatible methods for trade data
that replace the Premium-only /defi/v3/token/trade-data/multiple endpoint.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup

async def test_starter_compatibility():
    """Test Starter package compatible trade data methods."""
    
    print("🧪 Testing Starter Package Compatibility")
    print("=" * 50)
    
    # Initialize components
    logger_setup = LoggerSetup("StarterTest")
    logger = logger_setup.logger
    
    # Check API key
    api_key = os.getenv('BIRDEYE_API_KEY')
    if not api_key:
        print("❌ BIRDEYE_API_KEY environment variable not set")
        return
    
    # Initialize services
    cache_manager = CacheManager(ttl_default=300)
    rate_limiter = RateLimiterService()
    
    # Create config
    config = {
        'api_key': api_key,
        'base_url': 'https://public-api.birdeye.so',
        'rate_limit': 15,  # Starter package limit
        'request_timeout_seconds': 20,
        'cache_ttl_default_seconds': 300,
        'cache_ttl_error_seconds': 60,
        'max_retries': 3,
        'backoff_factor': 2
    }
    
    birdeye_api = BirdeyeAPI(config, logger_setup, cache_manager, rate_limiter)
    
    # Test tokens (popular Solana tokens)
    test_addresses = [
        "So11111111111111111111111111111111111111112",  # SOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
        "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"   # ETHER
    ]
    
    print(f"🎯 Testing with {len(test_addresses)} tokens")
    
    # Test 1: Starter package trade data method
    print("\n📡 Test 1: Starter Package Trade Data Method")
    print("-" * 40)
    
    start_time = time.time()
    try:
        trade_data = await birdeye_api.get_token_trade_data_multiple(
            test_addresses[:3], "24h", "starter_test"
        )
        
        execution_time = time.time() - start_time
        
        if trade_data:
            print(f"✅ Success: {len(trade_data)} tokens in {execution_time:.2f}s")
            for addr, data in trade_data.items():
                if data:
                    volume = data.get('volume_24h_usd', 0)
                    price_change = data.get('price_change_24h_percent', 0)
                    activity_score = data.get('trading_activity_score', 0)
                    symbol = data.get('symbol', 'Unknown')
                    print(f"   📈 {symbol} ({addr[:8]}...): ${volume:,.0f} volume, {price_change:+.2f}% change, {activity_score:.0f} activity score")
                else:
                    print(f"   ⚠️  Token {addr[:8]}...: No data")
        else:
            print(f"❌ Failed: No data returned in {execution_time:.2f}s")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Market data method
    print("\n📊 Test 2: Starter Package Market Data Method")
    print("-" * 40)
    
    start_time = time.time()
    try:
        market_data = await birdeye_api.get_token_market_data_multiple(
            test_addresses[:3], "24h", "market_test"
        )
        
        execution_time = time.time() - start_time
        
        if market_data:
            print(f"✅ Success: {len(market_data)} tokens in {execution_time:.2f}s")
            for addr, data in market_data.items():
                if data:
                    print(f"   📊 Token {addr[:8]}...: {len(data) if isinstance(data, dict) else 'Data received'}")
                else:
                    print(f"   ⚠️  Token {addr[:8]}...: No data")
        else:
            print(f"❌ Failed: No data returned in {execution_time:.2f}s")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: API statistics
    print("\n📊 API Usage Statistics")
    print("-" * 25)
    
    api_stats = birdeye_api.get_api_call_statistics()
    performance_stats = birdeye_api.get_performance_stats()
    
    print(f"   📞 Total API calls: {api_stats.get('total_api_calls', 0)}")
    print(f"   ✅ Successful calls: {api_stats.get('successful_api_calls', 0)}")
    print(f"   ❌ Failed calls: {api_stats.get('failed_api_calls', 0)}")
    print(f"   🎯 Cache hits: {api_stats.get('cache_hits', 0)}")
    print(f"   💨 Cache misses: {api_stats.get('cache_misses', 0)}")
    
    if api_stats.get('total_api_calls', 0) > 0:
        success_rate = (api_stats.get('successful_api_calls', 0) / api_stats.get('total_api_calls', 1)) * 100
        print(f"   📈 Success rate: {success_rate:.1f}%")
    
    # Test 4: Rate limiting compliance
    print("\n⏱️  Rate Limiting Analysis")
    print("-" * 25)
    
    total_time = sum([
        api_stats.get('total_response_time_ms', 0)
    ]) / 1000  # Convert to seconds
    
    if total_time > 0:
        calls_per_second = api_stats.get('total_api_calls', 0) / total_time
        print(f"   🚀 Average rate: {calls_per_second:.2f} calls/second")
        
        if calls_per_second <= 15:
            print(f"   ✅ Within Starter package limit (15 RPS)")
        else:
            print(f"   ⚠️  Exceeds Starter package limit (15 RPS)")
    
    print("\n🏁 Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_starter_compatibility()) 