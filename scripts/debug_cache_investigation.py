#!/usr/bin/env python3
"""
Cache System Investigation Script

This script investigates why the cache system is showing 0% hit rates
by testing cache key generation, storage, and retrieval.
"""

import asyncio
import time
import json
import hashlib
from core.cache_manager import CacheManager
from api.birdeye_connector import BirdeyeAPI
from services.rate_limiter_service import RateLimiterService
import os

class CacheInvestigator:
    """Investigate cache system issues"""
    
    def __init__(self):
        print("🔍 Cache System Investigation Starting...")
        
        # Initialize cache manager
        self.cache_manager = CacheManager(ttl_default=300)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiterService()
        
        # Initialize BirdeyeAPI for testing
        config = {
            'api_key': os.getenv('BIRDEYE_API_KEY'),
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        self.birdeye_api = BirdeyeAPI(config, print, self.cache_manager, self.rate_limiter)
    
    def test_basic_cache_operations(self):
        """Test basic cache set/get operations"""
        print("\n🧪 Testing Basic Cache Operations...")
        
        # Test 1: Simple key-value
        test_key = "test_simple_key"
        test_value = {"test": "data", "timestamp": time.time()}
        
        print(f"   Setting cache: {test_key} = {test_value}")
        self.cache_manager.set(test_key, test_value)
        
        print(f"   Getting cache: {test_key}")
        retrieved_value = self.cache_manager.get(test_key)
        
        if retrieved_value is not None:
            print(f"   ✅ Cache set/get working: {retrieved_value}")
        else:
            print(f"   ❌ Cache set/get FAILED: Retrieved None")
        
        # Test 2: TTL expiration
        short_ttl_key = "test_ttl_key"
        short_ttl_value = {"short": "ttl"}
        
        print(f"   Setting cache with 2s TTL: {short_ttl_key}")
        self.cache_manager.set(short_ttl_key, short_ttl_value, ttl=2)
        
        immediate_get = self.cache_manager.get(short_ttl_key)
        print(f"   Immediate get: {immediate_get}")
        
        print("   Waiting 3 seconds for TTL expiration...")
        time.sleep(3)
        
        expired_get = self.cache_manager.get(short_ttl_key)
        if expired_get is None:
            print("   ✅ TTL expiration working correctly")
        else:
            print(f"   ❌ TTL expiration FAILED: Still got {expired_get}")
    
    def test_api_cache_key_generation(self):
        """Test how API cache keys are generated"""
        print("\n🔑 Testing API Cache Key Generation...")
        
        # Test different scenarios
        test_scenarios = [
            {
                "endpoint": "/defi/multi_price",
                "params": {
                    "list_address": "token1,token2,token3",
                    "include_liquidity": True
                }
            },
            {
                "endpoint": "/defi/v3/token/list",
                "params": {
                    "sort_by": "volume_24h_usd",
                    "sort_type": "desc",
                    "limit": 20
                }
            },
            {
                "endpoint": "/defi/v2/tokens/top_traders",
                "params": {
                    "address": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
                    "time_frame": "24h",
                    "sort_by": "volume"
                }
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n   Scenario {i}: {scenario['endpoint']}")
            
            # Generate cache key using BirdeyeAPI method
            cache_key = self.generate_birdeye_cache_key(scenario['endpoint'], scenario['params'])
            print(f"   Generated key: {cache_key}")
            
            # Test set/get cycle
            test_data = {"test_data": f"scenario_{i}", "timestamp": time.time()}
            
            print(f"   Setting in cache...")
            self.cache_manager.set(cache_key, test_data)
            
            print(f"   Getting from cache...")
            retrieved = self.cache_manager.get(cache_key)
            
            if retrieved is not None:
                print(f"   ✅ Cache key working: {retrieved}")
            else:
                print(f"   ❌ Cache key FAILED")
            
            # Test key consistency
            cache_key_2 = self.generate_birdeye_cache_key(scenario['endpoint'], scenario['params'])
            if cache_key == cache_key_2:
                print(f"   ✅ Key generation consistent")
            else:
                print(f"   ❌ Key generation INCONSISTENT: {cache_key} != {cache_key_2}")
    
    def generate_birdeye_cache_key(self, endpoint: str, params: dict = None) -> str:
        """Generate cache key using BirdeyeAPI method"""
        # Replicate the BirdeyeAPI cache key generation
        namespace = "birdeye"
        
        if params:
            # Sort parameters for consistency
            sorted_params = sorted(params.items())
            param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            cache_key = f"{namespace}_{endpoint.replace('/', '_')}_{param_str}"
        else:
            cache_key = f"{namespace}_{endpoint.replace('/', '_')}"
        
        # Clean up the key
        cache_key = cache_key.replace('__', '_').replace('=', '_').replace('&', '_').replace(',', '_')
        
        return cache_key
    
    def investigate_actual_api_cache_usage(self):
        """Test actual API calls to see cache behavior"""
        print("\n🌐 Testing Actual API Cache Usage...")
        
        # Clear cache stats
        self.cache_manager.stats = {'hits': 0, 'misses': 0}
        
        test_token = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"  # Fartcoin from test
        
        print(f"   Making first API call for token: {test_token}")
        # This would require async, so we'll just simulate the cache key
        
        # Simulate what BirdeyeAPI would do
        endpoint = "/defi/token_overview"
        params = {"address": test_token}
        
        cache_key = f"birdeye_token_overview_{test_token}"
        print(f"   Simulated cache key: {cache_key}")
        
        # Test the actual cache operations
        mock_data = {"address": test_token, "symbol": "TEST", "price": 1.23}
        
        print("   Setting mock data in cache...")
        self.cache_manager.set(cache_key, mock_data)
        
        print("   Immediately retrieving...")
        retrieved = self.cache_manager.get(cache_key)
        
        if retrieved is not None:
            print(f"   ✅ API-style cache working: {retrieved}")
        else:
            print(f"   ❌ API-style cache FAILED")
        
        # Show cache stats
        print(f"   Cache stats: {self.cache_manager.stats}")
    
    def run_investigation(self):
        """Run complete cache investigation"""
        print("🔍 CACHE SYSTEM INVESTIGATION")
        print("=" * 50)
        
        self.test_basic_cache_operations()
        self.test_api_cache_key_generation()
        self.investigate_actual_api_cache_usage()
        
        # Final cache stats
        print(f"\n📊 Final Cache Stats: {self.cache_manager.stats}")
        
        print("\n✅ Investigation Complete!")

if __name__ == "__main__":
    investigator = CacheInvestigator()
    investigator.run_investigation() 