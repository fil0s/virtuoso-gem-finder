import asyncio
import sys
import os
from pathlib import Path

# Improve path handling to avoid import errors
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from api.batch_api_manager import BatchAPIManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Try running from project root with: python -m tests.test_cache_fix")
    sys.exit(1)

class DummyBirdeyeAPI:
    pass

class DummyLogger:
    def info(self, msg):
        pass
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

async def test_cache_functionality():
    """Test that cache system is working"""
    print("🧪 Testing Cache System Functionality...")
    try:
        api_manager = BatchAPIManager(DummyBirdeyeAPI(), DummyLogger())
        
        # Test cache key generation
        endpoint = "https://api.example.com/test"
        params = {"symbol": "SOL", "timeframe": "1h"}
        
        key1 = api_manager.cache_manager._generate_cache_key(endpoint, params)
        key2 = api_manager.cache_manager._generate_cache_key(endpoint, params)
        assert key1 == key2, "Cache keys should be consistent"
        print("✅ Cache key generation working")
        
        # Test cache storage and retrieval
        test_data = {"price": 100, "volume": 1000}
        await api_manager.cache_manager.set_cached_data(endpoint, params, test_data)
        
        cached_result = await api_manager.cache_manager.get_cached_data(endpoint, params)
        assert cached_result == test_data, "Cache storage/retrieval failed"
        print("✅ Cache storage/retrieval working")
        
        # Test cache hit rate calculation
        hit_rate = api_manager.cache_manager.get_cache_hit_rate()
        assert hit_rate >= 0, "Cache hit rate should be calculable"
        print(f"✅ Cache hit rate: {hit_rate:.2f}%")
        
        print("🎉 All cache tests passed!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_cache_functionality())
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 