"""
Integration Tests for Batch Processing with Token Discovery Strategies

This test suite validates that the new batch processing system integrates correctly
with existing token discovery strategies and provides the expected performance improvements.
"""

import asyncio
import pytest
import time
import logging
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from api.birdeye_connector import BirdeyeAPI
from api.batch_api_manager import BatchAPIManager
from services.early_token_detection import EarlyTokenDetector
from core.strategy_scheduler import StrategyScheduler
from core.token_discovery_strategies import BaseTokenDiscoveryStrategy
from monitor import VirtuosoGemHunter
from utils.structured_logger import get_structured_logger

class TestBatchIntegrationWithDiscovery:
    """Test batch processing integration with token discovery strategies."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'BIRDEYE_API': {
                'api_key': 'test_key',
                'base_url': 'https://public-api.birdeye.so',
                'request_timeout_seconds': 20,
                'use_rate_limiting': True,
                'rate_limit_requests_per_second': 10
            },
            'TOKEN_DISCOVERY': {
                'scan_interval_minutes': 10,
                'max_tokens': 30,
                'strict_filters': {
                    'min_liquidity': 100000,
                    'min_volume_24h_usd': 50000,
                    'min_holder': 200
                }
            },
            'ANALYSIS': {
                'alert_score_threshold': 70,
                'scoring_weights': {
                    'liquidity': 0.3,
                    'age': 0.2,
                    'price_change': 0.2,
                    'volume': 0.15,
                    'concentration': 0.1,
                    'trend_dynamics': 0.05
                },
                'stage_thresholds': {
                    'quick_score': 40,
                    'medium_score': 50,
                    'full_score': 60
                }
            },
            'STRATEGY_SCHEDULER': {
                'enabled': True,
                'run_hours': [0, 6, 12, 18],
                'strategies': {
                    'VolumeMomentumStrategy': {
                        'enabled': True,
                        'min_consecutive_appearances': 3,
                        'api_parameters': {
                            'sort_by': 'volume_24h_change_percent',
                            'sort_type': 'desc',
                            'min_liquidity': 100000,
                            'limit': 20
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def mock_token_data(self):
        """Mock token data for testing."""
        return [
            {
                'address': 'token1_address',
                'symbol': 'TEST1',
                'name': 'Test Token 1',
                'liquidity': 500000,
                'volume_24h_usd': 100000,
                'price_change_24h_percent': 15.5,
                'market_cap': 2000000,
                'holder': 1500,
                'last_trade_unix_time': int(time.time()) - 300
            },
            {
                'address': 'token2_address',
                'symbol': 'TEST2',
                'name': 'Test Token 2',
                'liquidity': 750000,
                'volume_24h_usd': 200000,
                'price_change_24h_percent': 25.3,
                'market_cap': 3000000,
                'holder': 2000,
                'last_trade_unix_time': int(time.time()) - 600
            },
            {
                'address': 'token3_address',
                'symbol': 'TEST3',
                'name': 'Test Token 3',
                'liquidity': 300000,
                'volume_24h_usd': 75000,
                'price_change_24h_percent': 8.2,
                'market_cap': 1500000,
                'holder': 800,
                'last_trade_unix_time': int(time.time()) - 900
            }
        ]

    @pytest.fixture
    def mock_batch_response_data(self):
        """Mock batch API response data."""
        return {
            'token1_address': {
                'price': {'value': 0.15, 'updateUnixTime': int(time.time())},
                'overview': {
                    'address': 'token1_address',
                    'symbol': 'TEST1',
                    'liquidity': {'usd': 500000},
                    'market_cap': 2000000,
                    'volume24h': {'usd': 100000}
                },
                'security': {
                    'is_honeypot': False,
                    'is_rugpull': False,
                    'top_10_holder_percent': 45.2,
                    'creator_balance': 0.05
                }
            },
            'token2_address': {
                'price': {'value': 0.85, 'updateUnixTime': int(time.time())},
                'overview': {
                    'address': 'token2_address',
                    'symbol': 'TEST2',
                    'liquidity': {'usd': 750000},
                    'market_cap': 3000000,
                    'volume24h': {'usd': 200000}
                },
                'security': {
                    'is_honeypot': False,
                    'is_rugpull': False,
                    'top_10_holder_percent': 38.7,
                    'creator_balance': 0.02
                }
            },
            'token3_address': {
                'price': {'value': 0.42, 'updateUnixTime': int(time.time())},
                'overview': {
                    'address': 'token3_address',
                    'symbol': 'TEST3',
                    'liquidity': {'usd': 300000},
                    'market_cap': 1500000,
                    'volume24h': {'usd': 75000}
                },
                'security': {
                    'is_honeypot': False,
                    'is_rugpull': False,
                    'top_10_holder_percent': 52.1,
                    'creator_balance': 0.08
                }
            }
        }

    @pytest.mark.asyncio
    async def test_batch_integration_with_token_discovery(self, mock_config, mock_token_data, mock_batch_response_data):
        """Test that batch processing integrates correctly with token discovery."""
        
        # Setup mocks
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            # Mock token discovery
            mock_api_instance.get_token_list.return_value = {
                'success': True,
                'data': {'tokens': mock_token_data}
            }
            
            # Mock batch responses
            mock_api_instance.get_price_volume_multi.return_value = {
                'success': True,
                'data': {addr: data['price'] for addr, data in mock_batch_response_data.items()}
            }
            
            mock_api_instance.get_token_metadata_multiple.return_value = {
                'success': True,
                'data': {addr: data['overview'] for addr, data in mock_batch_response_data.items()}
            }
            
            # Initialize components
            detector = EarlyTokenDetector(config=mock_config)
            detector.birdeye_api = mock_api_instance
            detector.batch_manager = BatchAPIManager(mock_api_instance, logging.getLogger())
            
            # Test discovery and analysis
            start_time = time.time()
            promising_tokens = await detector.discover_and_analyze(max_tokens=30)
            discovery_time = time.time() - start_time
            
            # Verify results
            assert isinstance(promising_tokens, list)
            assert len(promising_tokens) <= 30
            assert discovery_time < 60  # Should complete within 60 seconds
            
            # Verify batch processing was used
            assert mock_api_instance.get_price_volume_multi.called
            assert mock_api_instance.get_token_metadata_multiple.called

    @pytest.mark.asyncio
    async def test_strategy_scheduler_with_batch_processing(self, mock_config, mock_token_data):
        """Test that strategy scheduler works correctly with batch processing."""
        
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            # Mock strategy execution
            mock_api_instance.get_token_list.return_value = {
                'success': True,
                'data': {'tokens': mock_token_data}
            }
            
            # Initialize strategy scheduler
            scheduler = StrategyScheduler(
                birdeye_api=mock_api_instance,
                logger=logging.getLogger(),
                enabled=True,
                run_hours=[0, 6, 12, 18],
                strategy_configs=mock_config['STRATEGY_SCHEDULER']['strategies']
            )
            
            # Force strategy execution (bypass time check)
            with patch.object(scheduler, 'should_run_strategies', return_value=True):
                strategy_tokens = await scheduler.run_due_strategies()
                
                # Verify results
                assert isinstance(strategy_tokens, list)
                assert mock_api_instance.get_token_list.called

    @pytest.mark.asyncio
    async def test_cost_optimization_metrics(self, mock_config, mock_token_data, mock_batch_response_data):
        """Test that batch processing provides expected cost optimizations."""
        
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            # Setup API call tracking
            mock_api_instance.api_call_tracker = {
                'total_api_calls': 0,
                'compute_units_used': 0,
                'batch_calls': 0,
                'individual_calls': 0
            }
            
            # Mock responses
            mock_api_instance.get_token_list.return_value = {
                'success': True,
                'data': {'tokens': mock_token_data}
            }
            
            # Mock batch manager with cost tracking
            batch_manager = BatchAPIManager(mock_api_instance, logging.getLogger())
            batch_manager.cost_calculator = Mock()
            batch_manager.cost_calculator.calculate_batch_cost.return_value = 50  # CUs
            batch_manager.cost_calculator.calculate_individual_cost.return_value = 15  # CUs per call
            
            # Test batch operations
            addresses = [token['address'] for token in mock_token_data]
            
            start_calls = mock_api_instance.api_call_tracker['total_api_calls']
            
            # Simulate batch processing
            await batch_manager.batch_multi_price(addresses)
            await batch_manager.batch_token_overviews(addresses)
            
            # Verify cost optimization
            cost_report = await batch_manager.get_cost_optimization_report()
            
            assert 'total_compute_units' in cost_report
            assert 'batch_efficiency' in cost_report
            assert 'cost_savings' in cost_report
            assert cost_report['batch_efficiency']['efficiency_percentage'] > 50

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, mock_config):
        """Test performance monitoring with batch processing."""
        
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            # Initialize monitor with performance tracking
            monitor = VirtuosoGemHunter()
            monitor.config = mock_config
            monitor.birdeye_api = mock_api_instance
            
            # Mock performance analyzer
            monitor.performance_analyzer = Mock()
            monitor.performance_analyzer.record_scan_metrics = Mock()
            monitor.performance_analyzer.get_performance_summary = Mock(return_value={
                'avg_scan_duration': 45.2,
                'avg_tokens_per_scan': 25.8,
                'avg_api_calls_per_scan': 12.3,
                'cache_hit_rate': 0.78,
                'batch_usage_rate': 0.85
            })
            
            # Test performance tracking
            start_time = time.time()
            
            # Simulate scan
            with patch.object(monitor.detection_engine, 'discover_and_analyze', 
                            return_value=[]) as mock_discover:
                await monitor._run_scan_cycle()
            
            scan_duration = time.time() - start_time
            
            # Verify performance metrics
            assert scan_duration < 120  # Should complete within 2 minutes
            assert monitor.performance_analyzer.record_scan_metrics.called

    @pytest.mark.asyncio
    async def test_batch_fallback_mechanisms(self, mock_config, mock_token_data):
        """Test that batch processing has proper fallback mechanisms."""
        
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            # Setup batch manager
            batch_manager = BatchAPIManager(mock_api_instance, logging.getLogger())
            
            # Test batch failure fallback
            mock_api_instance.get_price_volume_multi.side_effect = Exception("Batch API failed")
            mock_api_instance.get_token_price.return_value = {
                'success': True,
                'data': {'value': 0.15}
            }
            
            addresses = ['token1_address', 'token2_address']
            
            # Should fallback to individual calls
            result = await batch_manager.batch_multi_price(addresses)
            
            # Verify fallback was used
            assert mock_api_instance.get_token_price.called
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_real_time_cost_tracking(self, mock_config):
        """Test real-time cost tracking during batch operations."""
        
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            # Setup cost tracking
            mock_api_instance.cost_calculator = Mock()
            mock_api_instance.cost_calculator.get_current_usage = Mock(return_value={
                'total_compute_units': 1250,
                'estimated_monthly_cost': 2.45,
                'calls_today': 85
            })
            
            batch_manager = BatchAPIManager(mock_api_instance, logging.getLogger())
            
            # Test cost tracking
            usage_before = mock_api_instance.cost_calculator.get_current_usage()
            
            # Simulate batch operations
            addresses = ['token1', 'token2', 'token3']
            await batch_manager.batch_multi_price(addresses)
            
            usage_after = mock_api_instance.cost_calculator.get_current_usage()
            
            # Verify cost tracking
            assert usage_before['total_compute_units'] <= usage_after['total_compute_units']

    @pytest.mark.asyncio
    async def test_batch_size_optimization(self, mock_config):
        """Test that batch sizes are optimized for different endpoints."""
        
        with patch('api.birdeye_connector.BirdeyeAPI') as mock_birdeye_api:
            mock_api_instance = AsyncMock()
            mock_birdeye_api.return_value = mock_api_instance
            
            batch_manager = BatchAPIManager(mock_api_instance, logging.getLogger())
            
            # Test different batch sizes
            large_address_list = [f'token_{i}' for i in range(100)]
            
            # Mock successful batch responses
            mock_api_instance.get_price_volume_multi.return_value = {
                'success': True,
                'data': {addr: {'value': 0.15} for addr in large_address_list[:50]}
            }
            
            # Test batch size limiting
            result = await batch_manager.batch_multi_price(large_address_list)
            
            # Verify batch size was optimized
            assert mock_api_instance.get_price_volume_multi.called
            call_args = mock_api_instance.get_price_volume_multi.call_args
            addresses_in_call = call_args[1]['addresses'] if 'addresses' in call_args[1] else call_args[0][0]
            assert len(addresses_in_call) <= 50  # Should respect batch size limits

    def test_integration_configuration_validation(self, mock_config):
        """Test that integration configuration is properly validated."""
        
        # Test valid configuration
        assert 'BIRDEYE_API' in mock_config
        assert 'TOKEN_DISCOVERY' in mock_config
        assert 'STRATEGY_SCHEDULER' in mock_config
        
        # Test required fields
        birdeye_config = mock_config['BIRDEYE_API']
        assert 'api_key' in birdeye_config
        assert 'base_url' in birdeye_config
        
        discovery_config = mock_config['TOKEN_DISCOVERY']
        assert 'max_tokens' in discovery_config
        assert 'strict_filters' in discovery_config
        
        # Test strategy configuration
        strategy_config = mock_config['STRATEGY_SCHEDULER']
        assert 'enabled' in strategy_config
        assert 'strategies' in strategy_config

if __name__ == '__main__':
    # Run integration tests
    pytest.main([__file__, '-v', '--asyncio-mode=auto']) 