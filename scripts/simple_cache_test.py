#!/usr/bin/env python3
"""
Simple Cache Test Script

Test basic cache functionality to identify why hit rates are 0%.
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cache_manager import CacheManager

def test_cache_system():
    """Test the cache system directly"""
    print("🔍 SIMPLE CACHE INVESTIGATION")
    print("=" * 40)
    
    # Initialize cache manager
    cache = CacheManager(ttl_default=300)
    
    print("\n🧪 Test 1: Basic Set/Get")
    test_key = "test_key_1"
    test_value = {"data": "test_value", "timestamp": time.time()}
    
    print(f"   Setting: {test_key} = {test_value}")
    cache.set(test_key, test_value)
    
    print(f"   Getting: {test_key}")
    retrieved = cache.get(test_key)
    
    if retrieved is not None:
        print(f"   ✅ SUCCESS: {retrieved}")
    else:
        print(f"   ❌ FAILED: Got None")
    
    print(f"   Cache stats: {cache.stats}")
    
    print("\n🧪 Test 2: TTL Expiration")
    ttl_key = "ttl_test"
    ttl_value = {"short": "lived"}
    
    print(f"   Setting with 2s TTL: {ttl_key}")
    cache.set(ttl_key, ttl_value, ttl=2)
    
    immediate = cache.get(ttl_key)
    print(f"   Immediate get: {immediate}")
    
    print("   Waiting 3 seconds...")
    time.sleep(3)
    
    expired = cache.get(ttl_key)
    print(f"   After expiration: {expired}")
    
    print(f"   Cache stats: {cache.stats}")
    
    print("\n🧪 Test 3: Complex Key Generation")
    # Simulate BirdEye-style cache keys
    keys = [
        "birdeye_multi_price_token1,token2,token3",
        "birdeye_token_overview_9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        "birdeye_top_traders_opt_27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4_24h_volume_desc_10_0"
    ]
    
    for i, key in enumerate(keys):
        value = {"test": i, "key": key}
        print(f"   Setting complex key {i+1}: {key[:50]}...")
        cache.set(key, value)
        
        retrieved = cache.get(key)
        if retrieved is not None:
            print(f"   ✅ Complex key {i+1} working")
        else:
            print(f"   ❌ Complex key {i+1} FAILED")
    
    print(f"\n📊 Final stats: {cache.stats}")
    
    print("\n🔍 Test 4: Cache Internal State")
    print(f"   Total cache entries: {len(cache.cache)}")
    print(f"   Cache keys: {list(cache.cache.keys())}")
    
    # Check if any entries exist
    for key, entry in cache.cache.items():
        age = time.time() - entry['timestamp']
        expired = age > entry['ttl']
        print(f"   Key: {key[:50]}...")
        print(f"      Age: {age:.1f}s, TTL: {entry['ttl']}s, Expired: {expired}")
    
    print("\n✅ Investigation Complete!")

if __name__ == "__main__":
    test_cache_system() 