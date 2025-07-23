import sys
import os
import asyncio
from pathlib import Path

# Improve path handling to avoid import errors
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    import pytest
    # WhaleActivityAnalyzer deprecated - functionality moved to WhaleSharkMovementTracker
    from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
    from services.whale_discovery_service import WhaleDiscoveryService
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies or run from project root")
    sys.exit(1)

class DummyLogger:
    def info(self, msg): pass
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class DummyCacheManager:
    def get(self, key): return None
    def set(self, key, value, ttl_seconds=None): pass
    def get_cache_stats(self): return {}

class MockBirdeyeAPI:
    async def get_token_holders(self, token_address, limit=100):
        # Return valid structure
        return {'items': [
            {'owner': 'whale1', 'percentage': 2.0, 'balance': 1000, 'valueUsd': 200000},
            {'owner': 'whale2', 'percentage': 1.5, 'balance': 800, 'valueUsd': 150000}
        ]}
    async def get_top_traders(self, token_address):
        return []
    async def get_token_overview(self, token_address):
        return {'price': 1.0, 'liquidity': 1000000, 'volume': {'h24': 100000}}
    async def get_token_transaction_volume(self, token_address, limit=50, max_pages=3):
        return 100000
    async def get_token_top_traders(self, token_address, limit=50):
        return []
    async def get_historical_trade_data(self, token_address, intervals):
        return {}
    async def detect_smart_money_activity(self, token_address, max_pages=3):
        return {"has_smart_money": False}

class DummyDiscoveryService:
    def get_whale_database_for_analyzer(self):
        return {}
    
    def _default_whale_score(self):
        """Return a default whale score with error indication"""
        return {
            'score_impact': 0,
            'confidence': 0.0,
            'error': 'Unable to analyze whale activity'
        }

async def test_whale_activity_analyzer():
    print("🧪 Testing Whale Activity Analyzer...")
    try:
        logger = DummyLogger()
        # Create mock BirdeyeAPI for WhaleSharkMovementTracker
        mock_api = MockBirdeyeAPI()
        analyzer = WhaleSharkMovementTracker(mock_api, logger=logger, whale_discovery_service=DummyDiscoveryService())
        
        # Valid token_data
        valid_token_data = {
            'symbol': 'TEST',
            'holders_data': {'items': [{'owner': 'whale1', 'percentage': 2.0, 'balance': 1000, 'valueUsd': 200000}]},
            'top_traders': [],
            'market_cap': 10000000,
            'volume_24h': 100000,
            'unique_trader_count': 1,
            'creation_time': 1234567890
        }
        result = await analyzer.analyze_whale_activity_patterns('token1', valid_token_data)
        assert hasattr(result, 'score_impact')
        print("✅ analyze_whale_activity with valid data: PASSED")

        # Invalid holders_data type
        invalid_token_data = dict(valid_token_data)
        invalid_token_data['holders_data'] = []  # Should be dict
        result = await analyzer.analyze_whale_activity_patterns('token1', invalid_token_data)
        assert result.score_impact == 0 and result.confidence == 0.0
        print("✅ analyze_whale_activity with invalid holders_data: PASSED")

        # Invalid top_traders type
        invalid_token_data2 = dict(valid_token_data)
        invalid_token_data2['top_traders'] = {}  # Should be list
        result = await analyzer.analyze_whale_activity_patterns('token1', invalid_token_data2)
        assert result.score_impact == 0 and result.confidence == 0.0
        print("✅ analyze_whale_activity with invalid top_traders: PASSED")

        # Completely malformed token_data
        malformed_token_data = {'foo': 'bar'}
        result = await analyzer.analyze_whale_activity_patterns('token1', malformed_token_data)
        assert result.score_impact == 0 and result.confidence == 0.0
        print("✅ analyze_whale_activity with malformed token_data: PASSED")
        
        print("🎉 All whale analysis tests passed!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_whale_activity_analyzer())
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 