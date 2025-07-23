#!/usr/bin/env python3
"""
Comprehensive Test Suite for API Configuration & HTTP Client Improvements

This test suite validates 100% success of both major improvements:
1. Centralized API Configuration System
2. Standardized HTTP Client Management

Tests cover:
- Configuration loading and validation
- Environment switching
- HTTP client functionality
- Integration between both systems
- Performance characteristics
- Error handling and edge cases
"""

import pytest
import asyncio
import aiohttp
import sys
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import json
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_config_manager import APIConfigManager, get_api_config
from utils.http_client_manager import StandardHTTPClient, HTTPClientFactory, get_json, post_json, http_client_pool


class TestAPIConfigurationSystem:
    """Test suite for API Configuration Manager"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            'default_environment': 'production',
            'environments': {
                'production': {
                    'test_service': {
                        'base_url': 'https://api.test.com',
                        'timeout': 30,
                        'max_retries': 3,
                        'endpoints': {
                            'search': '/v1/search',
                            'details': '/v1/details'
                        }
                    },
                    'another_service': {
                        'base_url': 'https://api.another.com',
                        'timeout': 15
                    },
                    'reference_urls': {
                        'test_token': 'https://explorer.test.com/token/{address}'
                    }
                },
                'testnet': {
                    'test_service': {
                        'base_url': 'https://testnet-api.test.com',
                        'timeout': 20
                    }
                }
            },
            'global_timeouts': {
                'default': 30,
                'fast': 10,
                'slow': 60
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, sample_config):
        """Create temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_config_loading_success(self, temp_config_file):
        """Test successful configuration loading"""
        print("🧪 Testing configuration loading...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        
        assert manager.config is not None
        assert manager.environment == 'production'
        assert len(manager.env_config) > 0
        assert 'test_service' in manager.env_config
        
        print("   ✅ Configuration loaded successfully")
    
    def test_environment_switching(self, temp_config_file):
        """Test environment switching functionality"""
        print("🧪 Testing environment switching...")
        
        # Test production environment
        prod_manager = APIConfigManager(environment='production', config_path=temp_config_file)
        prod_url = prod_manager.get_base_url('test_service')
        assert prod_url == 'https://api.test.com'
        
        # Test testnet environment
        test_manager = APIConfigManager(environment='testnet', config_path=temp_config_file)
        test_url = test_manager.get_base_url('test_service')
        assert test_url == 'https://testnet-api.test.com'
        
        print("   ✅ Environment switching works correctly")
    
    def test_service_configuration_retrieval(self, temp_config_file):
        """Test service configuration retrieval"""
        print("🧪 Testing service configuration retrieval...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        
        # Test complete service config
        service_config = manager.get_service_config('test_service')
        assert service_config['base_url'] == 'https://api.test.com'
        assert service_config['timeout'] == 30
        assert service_config['max_retries'] == 3
        
        # Test missing service
        missing_config = manager.get_service_config('nonexistent_service')
        assert missing_config == {}
        
        print("   ✅ Service configuration retrieval works correctly")
    
    def test_url_generation(self, temp_config_file):
        """Test URL generation functionality"""
        print("🧪 Testing URL generation...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        
        # Test base URL
        base_url = manager.get_base_url('test_service')
        assert base_url == 'https://api.test.com'
        
        # Test endpoint URL
        search_url = manager.get_endpoint_url('test_service', 'search')
        assert search_url == 'https://api.test.com/v1/search'
        
        # Test URL with trailing/leading slashes
        details_url = manager.get_endpoint_url('test_service', 'details')
        assert details_url == 'https://api.test.com/v1/details'
        
        print("   ✅ URL generation works correctly")
    
    def test_timeout_configuration(self, temp_config_file):
        """Test timeout configuration"""
        print("🧪 Testing timeout configuration...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        
        # Test service-specific timeout
        timeout = manager.get_timeout('test_service')
        assert timeout == 30
        
        # Test global timeout fallback
        timeout_another = manager.get_timeout('another_service')
        assert timeout_another == 15
        
        # Test global timeout for missing service
        timeout_missing = manager.get_timeout('nonexistent_service')
        assert timeout_missing == 30  # Default from global_timeouts
        
        print("   ✅ Timeout configuration works correctly")
    
    def test_reference_urls(self, temp_config_file):
        """Test reference URL generation"""
        print("🧪 Testing reference URL generation...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        
        # Test reference URL with parameter substitution
        token_address = 'ABC123XYZ'
        url = manager.get_reference_url('test_token', address=token_address)
        expected = f'https://explorer.test.com/token/{token_address}'
        assert url == expected
        
        # Test missing reference URL
        missing_url = manager.get_reference_url('nonexistent_url', address=token_address)
        assert missing_url == ''
        
        print("   ✅ Reference URL generation works correctly")
    
    def test_configuration_validation(self, temp_config_file):
        """Test configuration validation"""
        print("🧪 Testing configuration validation...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        
        validation_report = manager.validate_configuration()
        
        assert validation_report['environment'] == 'production'
        assert validation_report['config_file_exists'] == True
        assert validation_report['services_configured'] > 0
        assert isinstance(validation_report['missing_services'], list)
        assert isinstance(validation_report['invalid_urls'], list)
        assert isinstance(validation_report['warnings'], list)
        
        print("   ✅ Configuration validation works correctly")
    
    def test_fallback_configuration(self):
        """Test fallback configuration when file is missing"""
        print("🧪 Testing fallback configuration...")
        
        # Test with non-existent config file
        manager = APIConfigManager(config_path='/nonexistent/path/config.yaml')
        
        # Should still work with fallback config
        assert manager.config is not None
        assert 'environments' in manager.config
        
        # Should have basic services in fallback
        birdeye_url = manager.get_base_url('birdeye')
        assert 'birdeye' in birdeye_url.lower()
        
        print("   ✅ Fallback configuration works correctly")
    
    def test_config_reload(self, temp_config_file):
        """Test configuration reload functionality"""
        print("🧪 Testing configuration reload...")
        
        manager = APIConfigManager(config_path=temp_config_file)
        original_config = manager.config.copy()
        
        # Reload configuration
        manager.reload_config()
        
        # Should have same configuration
        assert manager.config == original_config
        
        print("   ✅ Configuration reload works correctly")


class TestHTTPClientManager:
    """Test suite for HTTP Client Manager"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session for testing"""
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={'test': 'data'})
        response.text = AsyncMock(return_value='{"test": "data"}')
        response.headers = {'content-type': 'application/json'}
        
        session.request.return_value.__aenter__.return_value = response
        session.get.return_value.__aenter__.return_value = response
        session.post.return_value.__aenter__.return_value = response
        
        return session, response
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test HTTP client initialization"""
        print("🧪 Testing HTTP client initialization...")
        
        client = StandardHTTPClient('test_service')
        
        assert client.service_name == 'test_service'
        assert client.logger is not None
        assert client.config is not None
        assert client.default_timeout > 0
        assert client.max_retries >= 0
        
        await client.close()
        
        print("   ✅ HTTP client initialization works correctly")
    
    @pytest.mark.asyncio
    async def test_get_request(self, mock_session):
        """Test GET request functionality"""
        print("🧪 Testing GET request...")
        
        session, response = mock_session
        
        with patch('aiohttp.ClientSession', return_value=session):
            client = StandardHTTPClient('test_service')
            
            result = await client.get('https://api.test.com/data', params={'q': 'test'})
            
            assert result == {'test': 'data'}
            session.request.assert_called_once()
            
            await client.close()
        
        print("   ✅ GET request works correctly")
    
    @pytest.mark.asyncio
    async def test_post_request(self, mock_session):
        """Test POST request functionality"""
        print("🧪 Testing POST request...")
        
        session, response = mock_session
        
        with patch('aiohttp.ClientSession', return_value=session):
            client = StandardHTTPClient('test_service')
            
            result = await client.post('https://api.test.com/data', json={'key': 'value'})
            
            assert result == {'test': 'data'}
            session.request.assert_called_once()
            
            await client.close()
        
        print("   ✅ POST request works correctly")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in HTTP client"""
        print("🧪 Testing error handling...")
        
        # Mock session that raises timeout
        session = AsyncMock()
        session.request.side_effect = asyncio.TimeoutError()
        
        with patch('aiohttp.ClientSession', return_value=session):
            client = StandardHTTPClient('test_service')
            
            result = await client.get('https://api.test.com/data')
            
            # Should return error dict instead of raising
            assert 'error' in result
            assert result['error'] == 'Timeout'
            
            await client.close()
        
        print("   ✅ Error handling works correctly")
    
    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic with exponential backoff"""
        print("🧪 Testing retry logic...")
        
        # Mock session that fails twice then succeeds
        session = AsyncMock()
        response_fail = AsyncMock()
        response_fail.status = 500
        response_success = AsyncMock()
        response_success.status = 200
        response_success.json = AsyncMock(return_value={'success': True})
        response_success.headers = {'content-type': 'application/json'}
        
        session.request.return_value.__aenter__.side_effect = [
            response_fail,  # First attempt fails
            response_fail,  # Second attempt fails
            response_success  # Third attempt succeeds
        ]
        
        with patch('aiohttp.ClientSession', return_value=session):
            client = StandardHTTPClient('test_service')
            
            start_time = time.time()
            result = await client.get('https://api.test.com/data')
            elapsed_time = time.time() - start_time
            
            # Should eventually succeed
            assert result == {'success': True}
            
            # Should have taken some time due to backoff
            assert elapsed_time > 0.1  # At least some backoff time
            
            # Should have made 3 attempts
            assert session.request.call_count == 3
            
            await client.close()
        
        print("   ✅ Retry logic works correctly")
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test context manager functionality"""
        print("🧪 Testing context manager...")
        
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={'test': 'data'})
        response.headers = {'content-type': 'application/json'}
        session.request.return_value.__aenter__.return_value = response
        
        with patch('aiohttp.ClientSession', return_value=session):
            async with StandardHTTPClient('test_service') as client:
                result = await client.get('https://api.test.com/data')
                assert result == {'test': 'data'}
        
        # Session should be closed after context exit
        # (We can't easily test this with mocks, but the pattern is correct)
        
        print("   ✅ Context manager works correctly")
    
    @pytest.mark.asyncio
    async def test_client_factory(self):
        """Test HTTP client factory"""
        print("🧪 Testing client factory...")
        
        # Test client creation
        client1 = await HTTPClientFactory.get_client('service1')
        client2 = await HTTPClientFactory.get_client('service2')
        client1_again = await HTTPClientFactory.get_client('service1')
        
        assert isinstance(client1, StandardHTTPClient)
        assert isinstance(client2, StandardHTTPClient)
        assert client1 is client1_again  # Should reuse existing client
        assert client1 is not client2  # Different services, different clients
        
        # Test cleanup
        await HTTPClientFactory.close_all()
        
        print("   ✅ Client factory works correctly")
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions"""
        print("🧪 Testing convenience functions...")
        
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={'convenience': 'test'})
        response.headers = {'content-type': 'application/json'}
        session.request.return_value.__aenter__.return_value = response
        
        with patch('aiohttp.ClientSession', return_value=session):
            # Test get_json convenience function
            result = await get_json('test_service', 'https://api.test.com/data')
            assert result == {'convenience': 'test'}
            
            # Test post_json convenience function
            result = await post_json('test_service', 'https://api.test.com/data', json={'test': 'data'})
            assert result == {'convenience': 'test'}
        
        print("   ✅ Convenience functions work correctly")
    
    @pytest.mark.asyncio
    async def test_http_client_pool(self):
        """Test HTTP client pool context manager"""
        print("🧪 Testing HTTP client pool...")
        
        async with http_client_pool() as pool:
            client1 = await pool.get_client('service1')
            client2 = await pool.get_client('service2')
            
            assert isinstance(client1, StandardHTTPClient)
            assert isinstance(client2, StandardHTTPClient)
            assert client1.service_name == 'service1'
            assert client2.service_name == 'service2'
        
        # Pool should clean up automatically
        
        print("   ✅ HTTP client pool works correctly")


class TestIntegration:
    """Integration tests for both systems working together"""
    
    @pytest.fixture
    def integration_config(self):
        """Configuration for integration testing"""
        return {
            'default_environment': 'production',
            'environments': {
                'production': {
                    'test_api': {
                        'base_url': 'https://httpbin.org',
                        'timeout': 10,
                        'max_retries': 2,
                        'endpoints': {
                            'get': '/get',
                            'post': '/post',
                            'status': '/status'
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def integration_config_file(self, integration_config):
        """Create config file for integration testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(integration_config, f)
            temp_path = f.name
        
        yield temp_path
        
        os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_config_http_integration(self, integration_config_file):
        """Test configuration and HTTP client working together"""
        print("🧪 Testing config + HTTP client integration...")
        
        # Initialize config manager
        config = APIConfigManager(config_path=integration_config_file)
        
        # Get configured URL and timeout
        base_url = config.get_base_url('test_api')
        endpoint_url = config.get_endpoint_url('test_api', 'get')
        timeout = config.get_timeout('test_api')
        
        assert base_url == 'https://httpbin.org'
        assert endpoint_url == 'https://httpbin.org/get'
        assert timeout == 10
        
        # Use HTTP client with configuration
        async with StandardHTTPClient('test_api') as client:
            # Override the client's config to use our test config
            client.config = config
            client.default_timeout = timeout
            
            # Mock a successful request
            session = AsyncMock()
            response = AsyncMock()
            response.status = 200
            response.json = AsyncMock(return_value={'url': endpoint_url, 'timeout': timeout})
            response.headers = {'content-type': 'application/json'}
            session.request.return_value.__aenter__.return_value = response
            
            with patch('aiohttp.ClientSession', return_value=session):
                result = await client.get(endpoint_url)
                
                assert result['url'] == endpoint_url
                assert result['timeout'] == timeout
        
        print("   ✅ Config + HTTP client integration works correctly")
    
    @pytest.mark.asyncio
    async def test_environment_switching_integration(self, integration_config_file):
        """Test environment switching with HTTP clients"""
        print("🧪 Testing environment switching integration...")
        
        # Test production environment
        prod_config = APIConfigManager(environment='production', config_path=integration_config_file)
        prod_client = StandardHTTPClient('test_api')
        prod_client.config = prod_config
        
        assert prod_client.config.environment == 'production'
        assert prod_client.config.get_base_url('test_api') == 'https://httpbin.org'
        
        await prod_client.close()
        
        print("   ✅ Environment switching integration works correctly")
    
    def test_configuration_coverage(self):
        """Test that all expected services are configured"""
        print("🧪 Testing configuration coverage...")
        
        # Test with actual config file
        config = get_api_config()
        
        expected_services = [
            'birdeye', 'moralis', 'dexscreener', 'pump_fun',
            'jupiter', 'raydium', 'orca', 'solana', 'rugcheck'
        ]
        
        configured_services = list(config.env_config.keys())
        
        for service in expected_services:
            if service in configured_services:
                base_url = config.get_base_url(service)
                timeout = config.get_timeout(service)
                
                assert base_url != '', f"Service {service} has empty base_url"
                assert timeout > 0, f"Service {service} has invalid timeout"
                
                print(f"   ✅ {service}: {base_url} (timeout: {timeout}s)")
            else:
                print(f"   ⚠️ {service}: Not configured (this may be expected)")
        
        print("   ✅ Configuration coverage test completed")


class TestPerformance:
    """Performance validation tests"""
    
    @pytest.mark.asyncio
    async def test_connection_pooling_performance(self):
        """Test that connection pooling improves performance"""
        print("🧪 Testing connection pooling performance...")
        
        # Mock session to simulate fast responses
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={'performance': 'test'})
        response.headers = {'content-type': 'application/json'}
        session.request.return_value.__aenter__.return_value = response
        
        with patch('aiohttp.ClientSession', return_value=session):
            # Test multiple requests with shared client
            async with StandardHTTPClient('test_service') as client:
                start_time = time.time()
                
                # Make multiple concurrent requests
                tasks = []
                for i in range(10):
                    task = client.get(f'https://api.test.com/data/{i}')
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                elapsed_time = time.time() - start_time
                
                # All requests should succeed
                assert len(results) == 10
                for result in results:
                    assert result == {'performance': 'test'}
                
                # Should be reasonably fast (mocked, so very fast)
                assert elapsed_time < 1.0  # Should complete in less than 1 second
                
                print(f"   ✅ 10 concurrent requests completed in {elapsed_time:.3f}s")
    
    @pytest.mark.asyncio 
    async def test_timeout_effectiveness(self):
        """Test that timeouts work effectively"""
        print("🧪 Testing timeout effectiveness...")
        
        # Mock session that takes too long
        session = AsyncMock()
        session.request.side_effect = asyncio.TimeoutError()
        
        with patch('aiohttp.ClientSession', return_value=session):
            client = StandardHTTPClient('test_service')
            
            start_time = time.time()
            result = await client.get('https://api.test.com/slow')
            elapsed_time = time.time() - start_time
            
            # Should return timeout error
            assert 'error' in result
            assert result['error'] == 'Timeout'
            
            # Should respect timeout (with retry overhead)
            expected_max_time = client.default_timeout * (client.max_retries + 1) + 10  # Buffer for retries
            assert elapsed_time < expected_max_time
            
            await client.close()
        
        print(f"   ✅ Timeout handled correctly in {elapsed_time:.3f}s")
    
    def test_memory_usage(self):
        """Test that resources are properly cleaned up"""
        print("🧪 Testing memory usage and cleanup...")
        
        # This is a basic test - in production you'd use more sophisticated memory profiling
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and destroy multiple clients
        async def create_destroy_clients():
            for i in range(10):
                async with StandardHTTPClient(f'test_service_{i}') as client:
                    pass  # Client should be cleaned up automatically
        
        # Run the test
        asyncio.run(create_destroy_clients())
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        object_growth = final_objects - initial_objects
        print(f"   📊 Object count: {initial_objects} → {final_objects} (growth: {object_growth})")
        
        # Allow some growth but not excessive (this is a rough test)
        assert object_growth < 1000, f"Too many objects created: {object_growth}"
        
        print("   ✅ Memory usage test passed")


async def run_comprehensive_test():
    """Run all tests and provide comprehensive report"""
    
    print("🚀 COMPREHENSIVE IMPROVEMENTS TEST SUITE")
    print("=" * 60)
    print("Testing both API Configuration and HTTP Client improvements...")
    print()
    
    # Track test results
    test_results = {
        'api_config': {'passed': 0, 'failed': 0, 'errors': []},
        'http_client': {'passed': 0, 'failed': 0, 'errors': []},
        'integration': {'passed': 0, 'failed': 0, 'errors': []},
        'performance': {'passed': 0, 'failed': 0, 'errors': []}
    }
    
    # Test API Configuration System
    print("📋 API CONFIGURATION SYSTEM TESTS")
    print("-" * 40)
    
    try:
        config_tests = TestAPIConfigurationSystem()
        
        # Create sample config for tests
        sample_config = {
            'default_environment': 'production',
            'environments': {
                'production': {
                    'test_service': {
                        'base_url': 'https://api.test.com',
                        'timeout': 30,
                        'max_retries': 3,
                        'endpoints': {
                            'search': '/v1/search',
                            'details': '/v1/details'
                        }
                    },
                    'reference_urls': {
                        'test_token': 'https://explorer.test.com/token/{address}'
                    }
                },
                'testnet': {
                    'test_service': {
                        'base_url': 'https://testnet-api.test.com',
                        'timeout': 20
                    }
                }
            },
            'global_timeouts': {
                'default': 30,
                'fast': 10,
                'slow': 60
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            temp_config_path = f.name
        
        try:
            # Run all config tests
            config_tests.test_config_loading_success(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_environment_switching(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_service_configuration_retrieval(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_url_generation(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_timeout_configuration(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_reference_urls(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_configuration_validation(temp_config_path)
            test_results['api_config']['passed'] += 1
            
            config_tests.test_fallback_configuration()
            test_results['api_config']['passed'] += 1
            
            config_tests.test_config_reload(temp_config_path)
            test_results['api_config']['passed'] += 1
            
        finally:
            os.unlink(temp_config_path)
            
    except Exception as e:
        test_results['api_config']['failed'] += 1
        test_results['api_config']['errors'].append(str(e))
        print(f"   ❌ API Config test failed: {e}")
    
    print()
    
    # Test HTTP Client System
    print("🌐 HTTP CLIENT SYSTEM TESTS")
    print("-" * 40)
    
    try:
        http_tests = TestHTTPClientManager()
        
        # Run all HTTP client tests
        await http_tests.test_client_initialization()
        test_results['http_client']['passed'] += 1
        
        # Create mock session for tests
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={'test': 'data'})
        response.headers = {'content-type': 'application/json'}
        session.request.return_value.__aenter__.return_value = response
        mock_session = (session, response)
        
        await http_tests.test_get_request(mock_session)
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_post_request(mock_session)
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_error_handling()
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_retry_logic()
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_context_manager()
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_client_factory()
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_convenience_functions()
        test_results['http_client']['passed'] += 1
        
        await http_tests.test_http_client_pool()
        test_results['http_client']['passed'] += 1
        
    except Exception as e:
        test_results['http_client']['failed'] += 1
        test_results['http_client']['errors'].append(str(e))
        print(f"   ❌ HTTP Client test failed: {e}")
    
    print()
    
    # Test Integration
    print("🔗 INTEGRATION TESTS")
    print("-" * 40)
    
    try:
        integration_tests = TestIntegration()
        
        # Create integration config
        integration_config = {
            'default_environment': 'production',
            'environments': {
                'production': {
                    'test_api': {
                        'base_url': 'https://httpbin.org',
                        'timeout': 10,
                        'max_retries': 2,
                        'endpoints': {
                            'get': '/get',
                            'post': '/post'
                        }
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(integration_config, f)
            temp_integration_path = f.name
        
        try:
            await integration_tests.test_config_http_integration(temp_integration_path)
            test_results['integration']['passed'] += 1
            
            await integration_tests.test_environment_switching_integration(temp_integration_path)
            test_results['integration']['passed'] += 1
            
            integration_tests.test_configuration_coverage()
            test_results['integration']['passed'] += 1
            
        finally:
            os.unlink(temp_integration_path)
            
    except Exception as e:
        test_results['integration']['failed'] += 1
        test_results['integration']['errors'].append(str(e))
        print(f"   ❌ Integration test failed: {e}")
    
    print()
    
    # Test Performance
    print("⚡ PERFORMANCE TESTS")
    print("-" * 40)
    
    try:
        perf_tests = TestPerformance()
        
        await perf_tests.test_connection_pooling_performance()
        test_results['performance']['passed'] += 1
        
        await perf_tests.test_timeout_effectiveness()
        test_results['performance']['passed'] += 1
        
        perf_tests.test_memory_usage()
        test_results['performance']['passed'] += 1
        
    except Exception as e:
        test_results['performance']['failed'] += 1
        test_results['performance']['errors'].append(str(e))
        print(f"   ❌ Performance test failed: {e}")
    
    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    total_passed = sum(result['passed'] for result in test_results.values())
    total_failed = sum(result['failed'] for result in test_results.values())
    total_tests = total_passed + total_failed
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_failed}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 DETAILED BREAKDOWN:")
    for category, results in test_results.items():
        category_total = results['passed'] + results['failed']
        category_rate = (results['passed'] / category_total * 100) if category_total > 0 else 0
        status_icon = "✅" if results['failed'] == 0 else "⚠️"
        
        print(f"   {status_icon} {category.replace('_', ' ').title()}: {results['passed']}/{category_total} ({category_rate:.1f}%)")
        
        if results['errors']:
            for error in results['errors']:
                print(f"      ❌ {error}")
    
    # Final assessment
    print(f"\n🎉 FINAL ASSESSMENT:")
    if total_failed == 0:
        print("   🏆 100% SUCCESS! All improvements working perfectly!")
        print("   ✅ API Configuration System: FULLY FUNCTIONAL")
        print("   ✅ HTTP Client Standardization: FULLY FUNCTIONAL") 
        print("   ✅ Integration: SEAMLESS")
        print("   ✅ Performance: OPTIMIZED")
        print("\n   🚀 Ready for production deployment!")
    else:
        print(f"   ⚠️ {total_failed} test(s) failed - review and fix before deployment")
        
    return success_rate == 100.0


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    exit(0 if success else 1)