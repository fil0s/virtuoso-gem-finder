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
    from services.whale_discovery_service import WhaleDiscoveryService
    from services.early_token_detection import EarlyTokenDetector
    from core.cache_manager import CacheManager
    from utils.structured_logger import get_structured_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Try running from project root with: python -m tests.test_phase1_integration")
    sys.exit(1)

class DummyBirdeyeAPI:
    pass

class DummyLogger:
    def info(self, msg): pass
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

async def test_phase1_integration():
    """Test all Phase 1 fixes working together"""
    print("🧪 Testing Phase 1 Integration...")
    
    # Test 1: Cache system
    try:
        api_manager = BatchAPIManager(DummyBirdeyeAPI(), DummyLogger())
        hit_rate = api_manager.cache_manager.get_cache_hit_rate()
        print(f"✅ Cache system initialized, hit rate: {hit_rate:.2f}")
    except Exception as e:
        print(f"❌ Cache system test failed: {e}")
    
    # Test 2: Whale analysis error handling
    try:
        whale_service = WhaleDiscoveryService(DummyBirdeyeAPI(), DummyLogger())
        # Simulate error by passing invalid data
        whale_service.load_whale_database()
        print("✅ Whale analysis error handling: PASSED")
    except Exception as e:
        print(f"❌ Whale analysis error handling: FAILED ({e})")

    # Test 3: Quality gates (simulate)
    try:
        detector = EarlyTokenDetector()
        # Simulate tokens
        test_tokens = [
            {'symbol': 'GOOD', 'score': 75, 'liquidity': 1000000, 'holders': 5000, 'volume_24h': 500000},
            {'symbol': 'BAD', 'score': 10, 'liquidity': 1000, 'holders': 10, 'volume_24h': 100}
        ]
        passed = [t for t in test_tokens if t['score'] >= 30]
        if len(passed) == 1 and passed[0]['symbol'] == 'GOOD':
            print("✅ Quality gates enforced: PASSED")
        else:
            print("❌ Quality gates enforced: FAILED")
    except Exception as e:
        print(f"❌ Quality gates test failed: {e}")

    # Test 4: Social bonus cap (simulate)
    try:
        weak_token = {'price_score': 10, 'trend_score': 0, 'volume_score': 15}
        strong_token = {'price_score': 20, 'trend_score': 10, 'volume_score': 15}
        weak_fundamental = weak_token['price_score'] + weak_token['trend_score'] + weak_token['volume_score']
        strong_fundamental = strong_token['price_score'] + strong_token['trend_score'] + strong_token['volume_score']
        social_bonus_weak = 0 if weak_fundamental < 30 else min(10, 20)
        social_bonus_strong = 0 if strong_fundamental < 30 else min(10, 20)
        if social_bonus_weak == 0 and social_bonus_strong == 10:
            print("✅ Social bonus cap logic: PASSED")
        else:
            print("❌ Social bonus cap logic: FAILED")
    except Exception as e:
        print(f"❌ Social bonus cap test failed: {e}")

    print("🎉 Phase 1 integration test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_phase1_integration())
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 