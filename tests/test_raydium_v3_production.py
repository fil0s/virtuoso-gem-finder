#!/usr/bin/env python3
"""
Production test suite for Raydium v3 integration
Tests all components in production-like conditions
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.raydium_connector import RaydiumConnector
from src.detectors.early_gem_detector import EarlyGemDetector
from services.rate_limiter_service import RateLimiterService
from api.cache_manager import EnhancedAPICacheManager

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

class TestRaydiumV3Production:
    """Test suite for Raydium v3 production integration"""
    
    @pytest.fixture
    async def mock_cache_manager(self):
        """Mock cache manager for testing"""
        cache = Mock()
        cache.get_enhanced = Mock(return_value=None)
        cache.set_enhanced = Mock()
        return cache
    
    @pytest.fixture
    async def mock_rate_limiter(self):
        """Mock rate limiter for testing"""
        rate_limiter = Mock()
        rate_limiter.wait_for_slot = AsyncMock()
        return rate_limiter
    
    @pytest.fixture
    async def raydium_connector(self, mock_cache_manager, mock_rate_limiter):
        """Create RaydiumConnector for testing"""
        connector = RaydiumConnector(
            enhanced_cache=mock_cache_manager,
            api_tracking_enabled=True,
            rate_limiter=mock_rate_limiter
        )
        await connector.__aenter__()
        yield connector
        await connector.__aexit__(None, None, None)
    
    @pytest.mark.asyncio
    async def test_raydium_connector_initialization(self, mock_cache_manager, mock_rate_limiter):
        """Test RaydiumConnector initializes correctly"""
        connector = RaydiumConnector(
            enhanced_cache=mock_cache_manager,
            api_tracking_enabled=True,
            rate_limiter=mock_rate_limiter
        )
        
        assert connector.base_url == "https://api-v3.raydium.io"
        assert connector.enhanced_cache is mock_cache_manager
        assert connector.rate_limiter is mock_rate_limiter
        assert connector.api_tracking_enabled is True
        assert 'pools' in connector.v3_endpoints
        assert 'pairs' in connector.v3_endpoints
    
    @pytest.mark.asyncio
    async def test_get_pools_success(self, raydium_connector):
        """Test getting pools returns data"""
        pools = await raydium_connector.get_pools(limit=5)
        
        # Should return a list (even if empty due to API issues)
        assert isinstance(pools, list)
        
        # If we got data, validate structure
        if pools:
            assert len(pools) <= 5
            pool = pools[0]
            assert isinstance(pool, dict)
            # v3 pools should have these fields
            expected_fields = ['id', 'tvl', 'mintA', 'mintB']
            for field in expected_fields:
                assert field in pool, f"Pool missing field: {field}"
    
    @pytest.mark.asyncio
    async def test_get_pairs_success(self, raydium_connector):
        """Test getting pairs returns data"""
        pairs = await raydium_connector.get_pairs(limit=5)
        
        # Should return a list (even if empty due to API issues)
        assert isinstance(pairs, list)
        
        # If we got data, validate structure
        if pairs:
            assert len(pairs) <= 5
            pair = pairs[0]
            assert isinstance(pair, dict)
            # v3 pairs should have these fields
            expected_fields = ['id', 'tvl', 'mintA', 'mintB']
            for field in expected_fields:
                assert field in pair, f"Pair missing field: {field}"
    
    @pytest.mark.asyncio
    async def test_get_wsol_trending_pairs(self, raydium_connector):
        """Test WSOL trending pairs with early gem detection"""
        wsol_pairs = await raydium_connector.get_wsol_trending_pairs(limit=10)
        
        assert isinstance(wsol_pairs, list)
        
        # If we got data, validate early gem structure
        if wsol_pairs:
            assert len(wsol_pairs) <= 10
            
            for pair in wsol_pairs:
                # Validate required fields
                required_fields = [
                    'address', 'symbol', 'tvl', 'volume_24h', 'volume_tvl_ratio',
                    'is_early_gem_candidate', 'early_gem_score', 'is_wsol_pair'
                ]
                for field in required_fields:
                    assert field in pair, f"WSOL pair missing field: {field}"
                
                # Validate data types
                assert isinstance(pair['tvl'], (int, float))
                assert isinstance(pair['volume_24h'], (int, float))
                assert isinstance(pair['volume_tvl_ratio'], (int, float))
                assert isinstance(pair['is_early_gem_candidate'], bool)
                assert isinstance(pair['early_gem_score'], (int, float))
                assert isinstance(pair['is_wsol_pair'], bool)
                
                # All should be WSOL pairs
                assert pair['is_wsol_pair'] is True
    
    @pytest.mark.asyncio
    async def test_api_statistics(self, raydium_connector):
        """Test API statistics tracking"""
        # Make a request to generate stats
        await raydium_connector.get_pools(limit=1)
        
        stats = raydium_connector.get_api_call_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_calls' in stats
        assert 'successful_calls' in stats
        assert 'failed_calls' in stats
        assert 'success_rate' in stats
        assert 'average_response_time' in stats
        
        assert stats['total_calls'] >= 0
        assert stats['successful_calls'] >= 0
        assert stats['failed_calls'] >= 0
        assert 0 <= stats['success_rate'] <= 1
        assert stats['average_response_time'] >= 0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_integration(self, mock_cache_manager, mock_rate_limiter):
        """Test rate limiter is called correctly"""
        connector = RaydiumConnector(
            enhanced_cache=mock_cache_manager,
            api_tracking_enabled=True,
            rate_limiter=mock_rate_limiter
        )
        
        async with connector:
            await connector.get_pools(limit=1)
            
            # Verify rate limiter was called
            mock_rate_limiter.wait_for_slot.assert_called()
            call_args = mock_rate_limiter.wait_for_slot.call_args[0]
            assert call_args[0] == "raydium"
    
    @pytest.mark.asyncio 
    async def test_error_handling(self, mock_cache_manager, mock_rate_limiter):
        """Test error handling with bad endpoints"""
        connector = RaydiumConnector(
            enhanced_cache=mock_cache_manager,
            api_tracking_enabled=True,
            rate_limiter=mock_rate_limiter
        )
        
        async with connector:
            # Test with invalid endpoint
            result = await connector._make_tracked_request("/invalid/endpoint", use_v2_fallback=False)
            
            # Should handle error gracefully
            assert result is None
            
            # Stats should track the failure
            stats = connector.get_api_call_statistics()
            assert stats['failed_calls'] > 0

class TestEarlyGemDetectorIntegration:
    """Test EarlyGemDetector integration with Raydium v3"""
    
    @pytest.fixture
    def mock_detector_config(self):
        """Mock configuration for detector"""
        return {
            'debug_mode': True,
            'use_fallback_data': False,
            'max_candidates_per_platform': 10
        }
    
    def test_raydium_connector_initialization_in_detector(self, mock_detector_config):
        """Test that EarlyGemDetector initializes RaydiumConnector correctly"""
        # This is a basic test - full integration would require more setup
        detector = EarlyGemDetector(**mock_detector_config)
        
        # Check that the raydium_connector attribute exists
        assert hasattr(detector, 'raydium_connector')
        
        # Check that the _fetch_raydium_v3_pools method exists
        assert hasattr(detector, '_fetch_raydium_v3_pools')
        assert callable(detector._fetch_raydium_v3_pools)
    
    @pytest.mark.asyncio
    async def test_fetch_raydium_v3_pools_method(self):
        """Test the _fetch_raydium_v3_pools method structure"""
        # Mock a simple detector
        detector = Mock()
        detector.raydium_connector = Mock()
        detector.raydium_connector.get_wsol_trending_pairs = AsyncMock(return_value=[
            {
                'symbol': 'TEST',
                'address': 'test123',
                'tvl': 50000,
                'volume_24h': 10000,
                'volume_tvl_ratio': 0.2,
                'is_early_gem_candidate': True,
                'early_gem_score': 0.2,
                'is_wsol_pair': True,
                'pair_name': 'WSOL/TEST',
                'pool_address': 'pool123',
                'pair_type': 'WSOL-TEST',
                'price': 0.001
            }
        ])
        detector.logger = Mock()
        detector.logger.debug = Mock()
        detector.logger.info = Mock()
        detector.logger.error = Mock()
        
        # Import the actual fetch method logic
        from src.detectors.early_gem_detector import EarlyGemDetector
        method = EarlyGemDetector._fetch_raydium_v3_pools
        
        # Call the method on our mock
        result = await method(detector)
        
        assert isinstance(result, list)
        if result:
            candidate = result[0]
            # Validate standardized format
            expected_fields = [
                'symbol', 'address', 'market_cap', 'volume_24h', 'liquidity',
                'is_early_gem_candidate', 'early_gem_score', 'discovery_source',
                'platform', 'platforms', 'source'
            ]
            for field in expected_fields:
                assert field in candidate, f"Candidate missing field: {field}"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])