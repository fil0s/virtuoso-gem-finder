#!/usr/bin/env python3
"""
Enhanced Caching System Test Script

Demonstrates the cost optimization benefits of the enhanced caching system
for position tracking and cross-platform token analysis.

This script shows how the caching system reduces Birdeye API calls and
provides estimated cost savings.
"""

import asyncio
import time
import json
import logging
from typing import List, Dict, Any
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_cache_manager import EnhancedPositionCacheManager
from core.cache_manager import CacheManager
from api.birdeye_connector import BirdeyeAPI
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup
from core.config_manager import ConfigManager

class CachingTestSuite:
    """Test suite to demonstrate enhanced caching benefits"""
    
    def __init__(self):
        # Initialize logging
        self.logger_setup = LoggerSetup('CachingTest')
        self.logger = self.logger_setup.logger
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize cache system
        self.base_cache = CacheManager()
        self.enhanced_cache = EnhancedPositionCacheManager(self.base_cache, self.logger)
        
        # Initialize Birdeye API
        self.rate_limiter = RateLimiterService()
        birdeye_config = self.config.get('BIRDEYE_API', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.base_cache,
            rate_limiter=self.rate_limiter
        )
        
        # Test token addresses (popular Solana tokens)
        self.test_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
            "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",  # ETHER
        ]
        
        self.logger.info("🧪 Enhanced Caching Test Suite initialized")
    
    async def run_all_tests(self):
        """Run comprehensive caching tests"""
        print("\n" + "="*60)
        print("🧪 ENHANCED CACHING SYSTEM TEST SUITE")
        print("="*60)
        
        # Test 1: Cache warming performance
        await self.test_cache_warming()
        
        # Test 2: Position tracking simulation
        await self.test_position_tracking_caching()
        
        # Test 3: Cross-platform analysis caching
        await self.test_cross_platform_caching()
        
        # Test 4: Cache hit rate analysis
        await self.test_cache_performance()
        
        # Test 5: Cost savings estimation
        self.analyze_cost_savings()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
    
    async def test_cache_warming(self):
        """Test cache warming functionality"""
        print("\n🔥 Test 1: Cache Warming Performance")
        print("-" * 40)
        
        # Register test tokens as position tokens
        for token in self.test_tokens:
            self.enhanced_cache.register_tracked_token(token, is_position=True)
        
        # Test cache warming
        start_time = time.time()
        tokens_needing_data = self.enhanced_cache.warm_cache_for_positions(self.test_tokens)
        
        print(f"📊 Tokens needing cache warming: {len(tokens_needing_data)}")
        print(f"⏱️  Cache warming check time: {time.time() - start_time:.3f}s")
        
        if tokens_needing_data:
            # Simulate batch warming
            start_time = time.time()
            try:
                # Batch get token overviews
                overviews = await self.birdeye_api.get_token_overviews_batch(tokens_needing_data[:3])  # Limit for demo
                for address, overview in overviews.items():
                    if overview:
                        self.enhanced_cache.set_enhanced("position_token_overview", address, overview)
                
                warm_time = time.time() - start_time
                print(f"🔥 Cache warming completed in {warm_time:.3f}s for {len(overviews)} tokens")
                
            except Exception as e:
                print(f"⚠️  Cache warming error: {e}")
        else:
            print("✅ All tokens already cached - no warming needed")
    
    async def test_position_tracking_caching(self):
        """Test position tracking with caching"""
        print("\n📍 Test 2: Position Tracking Caching")
        print("-" * 40)
        
        test_token = self.test_tokens[0]  # Use SOL for testing
        
        # Simulate position tracking data access patterns
        data_types = [
            "position_token_overview",
            "position_price", 
            "position_volume",
            "position_whale_activity"
        ]
        
        # First access (cache miss expected)
        print("🔍 First access (cache miss expected):")
        start_time = time.time()
        
        for data_type in data_types:
            cached_data = self.enhanced_cache.get_enhanced(data_type, test_token)
            status = "HIT" if cached_data else "MISS"
            print(f"  • {data_type}: {status}")
        
        first_access_time = time.time() - start_time
        
        # Simulate API data and cache it
        print("\n💾 Caching simulated data...")
        for data_type in data_types:
            fake_data = {
                "timestamp": int(time.time()),
                "data_type": data_type,
                "token": test_token,
                "value": f"cached_{data_type}_data"
            }
            self.enhanced_cache.set_enhanced(data_type, test_token, fake_data)
        
        # Second access (cache hit expected)
        print("\n🎯 Second access (cache hit expected):")
        start_time = time.time()
        
        for data_type in data_types:
            cached_data = self.enhanced_cache.get_enhanced(data_type, test_token)
            status = "HIT" if cached_data else "MISS"
            print(f"  • {data_type}: {status}")
        
        second_access_time = time.time() - start_time
        
        print(f"\n⚡ Performance improvement: {(first_access_time - second_access_time) * 1000:.1f}ms faster")
    
    async def test_cross_platform_caching(self):
        """Test cross-platform analysis caching"""
        print("\n🌐 Test 3: Cross-Platform Analysis Caching")
        print("-" * 40)
        
        # Test cross-platform data caching
        cross_platform_data = {
            "dexscreener_trending": ["token1", "token2", "token3"],
            "rugcheck_trending": ["token2", "token3", "token4"],
            "birdeye_trending": ["token1", "token3", "token5"],
            "correlation_score": 0.75
        }
        
        # Cache cross-platform data
        self.enhanced_cache.set_enhanced("cross_platform_trending", "analysis_batch_1", cross_platform_data)
        
        # Test retrieval
        start_time = time.time()
        cached_data = self.enhanced_cache.get_enhanced("cross_platform_trending", "analysis_batch_1")
        retrieval_time = (time.time() - start_time) * 1000
        
        if cached_data:
            print(f"✅ Cross-platform data cached and retrieved in {retrieval_time:.3f}ms")
            print(f"📊 Cached data includes {len(cached_data)} fields")
        else:
            print("❌ Cross-platform data caching failed")
    
    async def test_cache_performance(self):
        """Test cache performance metrics"""
        print("\n📈 Test 4: Cache Performance Analysis")
        print("-" * 40)
        
        # Generate some cache activity
        test_operations = 50
        
        print(f"🔄 Performing {test_operations} cache operations...")
        
        for i in range(test_operations):
            token = self.test_tokens[i % len(self.test_tokens)]
            data_type = f"test_data_type_{i % 3}"
            
            # Mix of cache hits and misses
            if i % 3 == 0:
                # Set data (cache miss)
                test_data = {"test_value": f"data_{i}", "timestamp": time.time()}
                self.enhanced_cache.set_enhanced(data_type, token, test_data)
            else:
                # Get data (potential cache hit)
                self.enhanced_cache.get_enhanced(data_type, token)
        
        # Get performance statistics
        stats = self.enhanced_cache.get_cache_statistics()
        
        print(f"📊 Cache Performance Statistics:")
        print(f"  • Cache hits: {stats['cache_hits']}")
        print(f"  • Cache misses: {stats['cache_misses']}")
        print(f"  • Hit rate: {stats['hit_rate_percent']:.1f}%")
        print(f"  • API calls saved: {stats['api_calls_saved']}")
        print(f"  • Estimated cost savings: ${stats['estimated_cost_savings_usd']:.4f}")
        print(f"  • Tracked tokens: {stats['tracked_tokens']}")
        print(f"  • Position tokens: {stats['position_tokens']}")
    
    def analyze_cost_savings(self):
        """Analyze potential cost savings"""
        print("\n💰 Test 5: Cost Savings Analysis")
        print("-" * 40)
        
        # Get final statistics
        stats = self.enhanced_cache.get_cache_statistics()
        
        # Calculate projections
        daily_api_calls_saved = stats['api_calls_saved'] * 24  # Assuming hourly runs
        monthly_api_calls_saved = daily_api_calls_saved * 30
        
        # Birdeye pricing estimates (approximate)
        cost_per_api_call = 0.00001  # ~$0.00001 per compute unit
        daily_savings = daily_api_calls_saved * cost_per_api_call
        monthly_savings = monthly_api_calls_saved * cost_per_api_call
        
        print(f"📊 Cost Savings Projections:")
        print(f"  • Current session API calls saved: {stats['api_calls_saved']}")
        print(f"  • Projected daily API calls saved: {daily_api_calls_saved}")
        print(f"  • Projected monthly API calls saved: {monthly_api_calls_saved}")
        print(f"  • Estimated daily cost savings: ${daily_savings:.4f}")
        print(f"  • Estimated monthly cost savings: ${monthly_savings:.4f}")
        print(f"  • Cache hit rate: {stats['hit_rate_percent']:.1f}%")
        
        # Additional benefits
        print(f"\n🎯 Additional Benefits:")
        print(f"  • Reduced API rate limiting issues")
        print(f"  • Faster response times for position tracking")
        print(f"  • More reliable service during high-load periods")
        print(f"  • Better user experience with instant data access")
        
        # Recommendations
        print(f"\n💡 Optimization Recommendations:")
        if stats['hit_rate_percent'] < 70:
            print(f"  • Consider increasing cache TTL for stable data")
            print(f"  • Enable more aggressive cache warming")
        else:
            print(f"  • Cache performance is excellent!")
        
        if stats['position_tokens'] > 0:
            print(f"  • Position token caching is active - optimal for trading")
        
        print(f"  • Consider enabling daemon mode for cross-platform analysis")
        print(f"  • Monitor cache statistics regularly for optimization")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.birdeye_api.close()
            self.logger.info("🧹 Test cleanup completed")
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")

async def main():
    """Run the caching test suite"""
    test_suite = CachingTestSuite()
    
    try:
        await test_suite.run_all_tests()
    except Exception as e:
        print(f"❌ Test suite error: {e}")
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main()) 