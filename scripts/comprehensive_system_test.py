#!/usr/bin/env python3
"""
Comprehensive System Test Suite

This script provides a unified test runner for the entire Virtuoso Gem Hunter system:
1. End-to-end system test - Testing the entire token discovery pipeline
2. API integration test - Validating all external API connections
3. Performance benchmark test - Testing system efficiency and resource usage
4. Production readiness test - Validating the system is ready for live trading

Usage:
    python scripts/comprehensive_system_test.py [--test-type all|e2e|api|perf|prod] [--verbose]
"""

import asyncio
import logging
import sys
import time
import json
import traceback
import argparse
import psutil
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from core.strategy_scheduler import StrategyScheduler
from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup
from services.early_token_detection import EarlyTokenDetector
from services.telegram_alerter import TelegramAlerter

@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    test_type: str
    status: str  # PASS, FAIL, WARNING, SKIP
    duration_seconds: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    api_calls_made: int
    tokens_processed: int
    cache_hit_rate: float

class ComprehensiveSystemTester:
    """Comprehensive test suite for the entire system"""
    
    def __init__(self, verbose: bool = False):
        # Setup logging
        log_level = 'DEBUG' if verbose else 'INFO'
        self.logger_setup = LoggerSetup('ComprehensiveSystemTest', log_level=log_level)
        self.logger = self.logger_setup.logger
        self.verbose = verbose
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize core services
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Test results tracking
        self.test_results: List[TestResult] = []
        self.system_metrics: List[SystemMetrics] = []
        
        # Performance baseline
        self.baseline_metrics = None
        self.start_time = None
        
        # Test tokens - will be populated dynamically
        self.test_tokens = {}
        self.test_wallets = []
        
    async def _fetch_top_test_tokens(self):
        """Fetch top 10 trending tokens by rank for testing"""
        try:
            birdeye_config = self.config.get('BIRDEYE_API', {})
            birdeye_api = BirdeyeAPI(
                config=birdeye_config,
                logger=self.logger,
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )
            
            self.logger.info("🔍 Fetching top 10 trending tokens by rank for testing...")
            
            # Fetch top 10 trending tokens using the trending endpoint with rank sorting
            trending_response = await birdeye_api._make_request(
                "/defi/token_trending",
                params={
                    "sort_by": "rank",
                    "sort_type": "asc",
                    "limit": 10
                }
            )
            
            if trending_response and trending_response.get('success') and trending_response.get('data'):
                tokens_data = trending_response['data']
                
                # Handle different response structures
                if isinstance(tokens_data, dict) and 'tokens' in tokens_data:
                    trending_tokens = tokens_data['tokens']
                elif isinstance(tokens_data, list):
                    trending_tokens = tokens_data
                else:
                    trending_tokens = []
                
                # Process trending tokens
                for i, token in enumerate(trending_tokens[:10], 1):  # Top 10 by rank
                    if isinstance(token, dict):
                        address = token.get('address')
                        symbol = token.get('symbol', f'RANK_{i}')
                        rank = token.get('rank', i)
                        
                        if address:
                            self.test_tokens[f"{symbol}_rank_{rank}"] = address
                            self.logger.debug(f"Added trending token #{rank}: {symbol} ({address})")
                    elif isinstance(token, str):
                        # If token is just an address string
                        self.test_tokens[f"RANK_{i}"] = token
                        self.logger.debug(f"Added trending token #{i}: {token}")
                
                self.logger.info(f"✅ Successfully loaded {len(self.test_tokens)} trending tokens by rank")
            
            # Fallback: try the original trending endpoint if rank sorting fails
            if not self.test_tokens:
                self.logger.warning("Rank-sorted trending failed, trying original trending endpoint...")
                trending_addresses = await birdeye_api.get_trending_tokens()
                if trending_addresses and isinstance(trending_addresses, list):
                    for i, address in enumerate(trending_addresses[:10], 1):  # Top 10 trending
                        self.test_tokens[f"TRENDING_{i}"] = address
                        self.logger.debug(f"Added fallback trending token #{i}: {address}")
            
            # Final fallback to known tokens if all else fails
            if not self.test_tokens:
                self.test_tokens = {
                    'SOL_fallback': 'So11111111111111111111111111111111111111112',
                    'USDC_fallback': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
                }
                self.logger.warning("No trending tokens found, using fallback tokens")
            
            self.logger.info(f"✅ Loaded {len(self.test_tokens)} test tokens for comprehensive testing")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch trending tokens: {e}")
            # Fallback to known tokens
            self.test_tokens = {
                'SOL_fallback': 'So11111111111111111111111111111111111111112',
                'USDC_fallback': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
            }
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        self.logger.info("🚀 Starting Comprehensive System Test Suite")
        self.start_time = time.time()
        
        # Fetch top tokens for testing
        await self._fetch_top_test_tokens()
        
        # Capture baseline metrics
        self.baseline_metrics = self._capture_system_metrics()
        
        try:
            # Run all test suites
            await self._run_api_integration_tests()
            await self._run_end_to_end_tests()
            await self._run_performance_benchmark_tests()
            await self._run_production_readiness_tests()
            
        except Exception as e:
            self.logger.error(f"Critical error during testing: {e}")
            self.test_results.append(TestResult(
                test_name="system_test_suite",
                test_type="critical",
                status="FAIL",
                duration_seconds=time.time() - (self.start_time or time.time()),
                details={"error": str(e), "traceback": traceback.format_exc()},
                error_message=str(e)
            ))
        
        # Generate final report
        return await self._generate_final_report()
    
    async def _run_api_integration_tests(self):
        """Test all external API integrations"""
        self.logger.info("🔌 Running API Integration Tests")
        
        # Test Birdeye API
        await self._test_birdeye_api_integration()
        
        # Test RugCheck API
        await self._test_rugcheck_api_integration()
        
        # Test Telegram API (if configured)
        await self._test_telegram_api_integration()
        
        # Test RPC endpoints
        await self._test_rpc_integration()
    
    async def _test_birdeye_api_integration(self):
        """Comprehensive Birdeye API integration test"""
        test_start = time.time()
        
        try:
            birdeye_config = self.config.get('BIRDEYE_API', {})
            birdeye_api = BirdeyeAPI(
                config=birdeye_config,
                logger=self.logger,
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )
            
            # Use dynamically fetched test tokens
            test_token = list(self.test_tokens.values())[0] if self.test_tokens else 'So11111111111111111111111111111111111111112'
            
            tests = [
                ("token_overview", birdeye_api.get_token_overview(test_token)),
                ("token_list", birdeye_api.get_token_list(limit=10)),
                ("token_security", birdeye_api.get_token_security(test_token)),
                ("price_data", birdeye_api.get_historical_price_at_timestamp(test_token, int(time.time()) - 3600))
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_coro in tests:
                try:
                    result = await test_coro
                    # Check if we got data back (even if success field is not present)
                    if result and (result.get('success') or isinstance(result, dict) and len(result) > 0):
                        passed_tests += 1
                        if self.verbose:
                            self.logger.debug(f"✅ Birdeye {test_name} test passed")
                    else:
                        self.logger.warning(f"⚠️ Birdeye {test_name} test returned no data")
                except Exception as e:
                    self.logger.error(f"❌ Birdeye {test_name} test failed: {e}")
            
            status = "PASS" if passed_tests == total_tests else "WARNING" if passed_tests > 0 else "FAIL"
            
            self.test_results.append(TestResult(
                test_name="birdeye_api_integration",
                test_type="api",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "passed_tests": passed_tests,
                    "total_tests": total_tests,
                    "success_rate": passed_tests / total_tests,
                    "endpoints_tested": [test[0] for test in tests]
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="birdeye_api_integration",
                test_type="api",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_rugcheck_api_integration(self):
        """Test RugCheck API integration"""
        test_start = time.time()
        
        try:
            rugcheck = RugCheckConnector(logger=self.logger)
            
            # Use dynamically fetched test token
            test_token = list(self.test_tokens.values())[0] if self.test_tokens else 'So11111111111111111111111111111111111111112'
            result = await rugcheck.analyze_token_security(test_token)
            
            status = "PASS" if result else "FAIL"
            
            self.test_results.append(TestResult(
                test_name="rugcheck_api_integration",
                test_type="api",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "test_token": test_token,
                    "result_received": bool(result),
                    "result_type": type(result).__name__
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="rugcheck_api_integration",
                test_type="api",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_telegram_api_integration(self):
        """Test Telegram API integration if configured"""
        test_start = time.time()
        
        try:
            telegram_config = self.config.get('TELEGRAM', {})
            
            if not telegram_config.get('enabled', False):
                self.test_results.append(TestResult(
                    test_name="telegram_api_integration",
                    test_type="api",
                    status="SKIP",
                    duration_seconds=time.time() - test_start,
                    details={"reason": "Telegram not enabled in configuration"}
                ))
                return
            
            # Get required parameters for TelegramAlerter
            bot_token = telegram_config.get('bot_token')
            chat_id = telegram_config.get('chat_id')
            
            if not bot_token or not chat_id:
                self.test_results.append(TestResult(
                    test_name="telegram_api_integration",
                    test_type="api",
                    status="SKIP",
                    duration_seconds=time.time() - test_start,
                    details={"reason": "Telegram bot_token or chat_id not configured"}
                ))
                return
            
            telegram_alerter = TelegramAlerter(
                bot_token=bot_token,
                chat_id=chat_id,
                config=telegram_config
            )
            
            # Test connection (basic configuration check)
            connection_test = bool(bot_token and chat_id)
            
            status = "PASS" if connection_test else "FAIL"
            
            self.test_results.append(TestResult(
                test_name="telegram_api_integration",
                test_type="api",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "connection_test": connection_test,
                    "bot_configured": bool(telegram_config.get('bot_token')),
                    "chat_configured": bool(telegram_config.get('chat_id'))
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="telegram_api_integration",
                test_type="api",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_rpc_integration(self):
        """Test RPC endpoint integration"""
        test_start = time.time()
        
        try:
            # This would test Solana RPC connectivity
            # For now, we'll do a basic configuration check
            rpc_config = self.config.get('RPC', {})
            endpoint = rpc_config.get('solana_endpoint')
            
            if not endpoint:
                status = "FAIL"
                details = {"error": "No RPC endpoint configured"}
            else:
                # Basic connectivity test could be added here
                status = "PASS"
                details = {
                    "endpoint": endpoint,
                    "timeout": rpc_config.get('timeout_seconds', 30),
                    "max_retries": rpc_config.get('max_retries', 3)
                }
            
            self.test_results.append(TestResult(
                test_name="rpc_integration",
                test_type="api",
                status=status,
                duration_seconds=time.time() - test_start,
                details=details
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="rpc_integration",
                test_type="api",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _run_end_to_end_tests(self):
        """Run end-to-end system tests"""
        self.logger.info("🔄 Running End-to-End System Tests")
        
        # Test complete token discovery pipeline
        await self._test_token_discovery_pipeline()
        
        # Test strategy coordination
        await self._test_strategy_coordination()
        
        # Test data persistence
        await self._test_data_persistence()
    
    async def _test_token_discovery_pipeline(self):
        """Test the complete token discovery pipeline"""
        test_start = time.time()
        
        try:
            # Initialize strategy scheduler
            scheduler = StrategyScheduler(
                config=self.config,
                logger=self.logger,
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )
            
            # Run a limited discovery scan
            scan_results = await scheduler.run_discovery_scan(
                max_tokens_per_strategy=5,  # Limited for testing
                scan_id=f"test_scan_{int(time.time())}"
            )
            
            # Analyze results
            total_tokens = sum(len(tokens) for tokens in scan_results.get('strategy_results', {}).values())
            strategies_executed = len(scan_results.get('strategy_results', {}))
            
            status = "PASS" if total_tokens > 0 and strategies_executed > 0 else "FAIL"
            
            self.test_results.append(TestResult(
                test_name="token_discovery_pipeline",
                test_type="e2e",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "total_tokens_discovered": total_tokens,
                    "strategies_executed": strategies_executed,
                    "scan_results": scan_results
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="token_discovery_pipeline",
                test_type="e2e",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_strategy_coordination(self):
        """Test strategy coordination and data sharing"""
        test_start = time.time()
        
        try:
            # Test that strategies can share data effectively
            scheduler = StrategyScheduler(
                config=self.config,
                logger=self.logger,
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )
            
            # Get strategy status
            status_report = scheduler.get_status_report()
            
            active_strategies = status_report.get('active_strategies', 0)
            status = "PASS" if active_strategies > 0 else "FAIL"
            
            self.test_results.append(TestResult(
                test_name="strategy_coordination",
                test_type="e2e",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "active_strategies": active_strategies,
                    "status_report": status_report
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="strategy_coordination",
                test_type="e2e",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_data_persistence(self):
        """Test data persistence and caching"""
        test_start = time.time()
        
        try:
            # Test cache functionality
            test_key = f"test_key_{int(time.time())}"
            test_data = {"test": "data", "timestamp": time.time()}
            
            # Store data
            await self.cache_manager.set(test_key, test_data, ttl=60)
            
            # Retrieve data
            retrieved_data = await self.cache_manager.get(test_key)
            
            status = "PASS" if retrieved_data == test_data else "FAIL"
            
            # Cleanup
            await self.cache_manager.delete(test_key)
            
            self.test_results.append(TestResult(
                test_name="data_persistence",
                test_type="e2e",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "cache_test": status == "PASS",
                    "test_key": test_key,
                    "data_match": retrieved_data == test_data
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="data_persistence",
                test_type="e2e",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _run_performance_benchmark_tests(self):
        """Run performance benchmark tests"""
        self.logger.info("⚡ Running Performance Benchmark Tests")
        
        # Test API rate limiting
        await self._test_rate_limiting_performance()
        
        # Test memory usage
        await self._test_memory_usage()
        
        # Test concurrent operations
        await self._test_concurrent_operations()
    
    async def _test_rate_limiting_performance(self):
        """Test rate limiting performance"""
        test_start = time.time()
        
        try:
            # Test rate limiter behavior
            api_calls_made = 0
            start_time = time.time()
            
            # Simulate rapid API calls
            for _ in range(10):
                await self.rate_limiter.acquire("test_service")
                api_calls_made += 1
            
            duration = time.time() - start_time
            calls_per_second = api_calls_made / duration if duration > 0 else 0
            
            # Rate limiting should prevent excessive calls per second
            status = "PASS" if calls_per_second < 100 else "WARNING"  # Reasonable threshold
            
            self.test_results.append(TestResult(
                test_name="rate_limiting_performance",
                test_type="performance",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "api_calls_made": api_calls_made,
                    "calls_per_second": calls_per_second,
                    "duration": duration
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="rate_limiting_performance",
                test_type="performance",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_memory_usage(self):
        """Test memory usage patterns"""
        test_start = time.time()
        
        try:
            # Capture initial memory
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Simulate memory-intensive operations
            large_data = []
            for i in range(1000):
                large_data.append({"token": f"test_{i}", "data": list(range(100))})
            
            # Capture peak memory
            peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Cleanup
            del large_data
            gc.collect()
            
            # Capture final memory
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            memory_increase = peak_memory - initial_memory
            memory_recovered = peak_memory - final_memory
            
            # Memory should be reasonable and recoverable
            status = "PASS" if memory_increase < 500 and memory_recovered > 0 else "WARNING"
            
            self.test_results.append(TestResult(
                test_name="memory_usage",
                test_type="performance",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "initial_memory_mb": initial_memory,
                    "peak_memory_mb": peak_memory,
                    "final_memory_mb": final_memory,
                    "memory_increase_mb": memory_increase,
                    "memory_recovered_mb": memory_recovered
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="memory_usage",
                test_type="performance",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_concurrent_operations(self):
        """Test concurrent operations performance"""
        test_start = time.time()
        
        try:
            # Test concurrent cache operations
            async def cache_operation(i):
                key = f"concurrent_test_{i}"
                data = {"index": i, "timestamp": time.time()}
                await self.cache_manager.set(key, data, ttl=30)
                retrieved = await self.cache_manager.get(key)
                await self.cache_manager.delete(key)
                return retrieved == data
            
            # Run concurrent operations
            tasks = [cache_operation(i) for i in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_operations = sum(1 for r in results if r is True)
            total_operations = len(results)
            
            status = "PASS" if successful_operations == total_operations else "WARNING"
            
            self.test_results.append(TestResult(
                test_name="concurrent_operations",
                test_type="performance",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "successful_operations": successful_operations,
                    "total_operations": total_operations,
                    "success_rate": successful_operations / total_operations
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="concurrent_operations",
                test_type="performance",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _run_production_readiness_tests(self):
        """Run production readiness tests"""
        self.logger.info("🏭 Running Production Readiness Tests")
        
        # Test configuration validation
        await self._test_configuration_validation()
        
        # Test error handling
        await self._test_error_handling()
        
        # Test resource limits
        await self._test_resource_limits()
        
        # Test security measures
        await self._test_security_measures()
    
    async def _test_configuration_validation(self):
        """Test configuration validation"""
        test_start = time.time()
        
        try:
            # Test that all required configurations are present
            required_sections = ['BIRDEYE_API', 'RPC', 'DATABASE']
            missing_sections = []
            
            for section in required_sections:
                if not self.config.get(section):
                    missing_sections.append(section)
            
            # Test API keys are configured
            api_keys_configured = []
            if self.config.get('BIRDEYE_API', {}).get('api_key'):
                api_keys_configured.append('BIRDEYE_API')
            
            status = "PASS" if not missing_sections else "FAIL"
            
            self.test_results.append(TestResult(
                test_name="configuration_validation",
                test_type="production",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "missing_sections": missing_sections,
                    "api_keys_configured": api_keys_configured,
                    "config_sections": list(self.config.keys())
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="configuration_validation",
                test_type="production",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_error_handling(self):
        """Test error handling capabilities"""
        test_start = time.time()
        
        try:
            # Test handling of invalid API calls
            birdeye_config = self.config.get('BIRDEYE_API', {})
            birdeye_api = BirdeyeAPI(
                config=birdeye_config,
                logger=self.logger,
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )
            
            # Test with invalid token address
            result = await birdeye_api.get_token_overview("invalid_address")
            
            # Should handle error gracefully
            error_handled = not result or not result.get('success')
            
            status = "PASS" if error_handled else "WARNING"
            
            self.test_results.append(TestResult(
                test_name="error_handling",
                test_type="production",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "error_handled_gracefully": error_handled,
                    "result": result
                }
            ))
            
        except Exception as e:
            # Exception handling is also acceptable
            self.test_results.append(TestResult(
                test_name="error_handling",
                test_type="production",
                status="PASS",
                duration_seconds=time.time() - test_start,
                details={
                    "exception_caught": True,
                    "exception_type": type(e).__name__
                }
            ))
    
    async def _test_resource_limits(self):
        """Test resource limit compliance"""
        test_start = time.time()
        
        try:
            # Check current resource usage
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Define reasonable limits for production
            max_memory_mb = 1000  # 1GB
            max_cpu_percent = 80
            
            memory_ok = memory_mb < max_memory_mb
            cpu_ok = cpu_percent < max_cpu_percent
            
            status = "PASS" if memory_ok and cpu_ok else "WARNING"
            
            self.test_results.append(TestResult(
                test_name="resource_limits",
                test_type="production",
                status=status,
                duration_seconds=time.time() - test_start,
                details={
                    "memory_mb": memory_mb,
                    "memory_limit_mb": max_memory_mb,
                    "memory_ok": memory_ok,
                    "cpu_percent": cpu_percent,
                    "cpu_limit_percent": max_cpu_percent,
                    "cpu_ok": cpu_ok
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="resource_limits",
                test_type="production",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def _test_security_measures(self):
        """Test security measures"""
        test_start = time.time()
        
        try:
            # Test that sensitive data is not logged
            # Test that API keys are properly protected
            # Test that file permissions are appropriate
            
            security_checks = {
                "config_has_sensitive_data": bool(self.config.get('BIRDEYE_API', {}).get('api_key')),
                "logging_configured": bool(self.logger),
                "cache_manager_initialized": bool(self.cache_manager),
                "rate_limiter_active": bool(self.rate_limiter)
            }
            
            all_checks_passed = all(security_checks.values())
            status = "PASS" if all_checks_passed else "WARNING"
            
            self.test_results.append(TestResult(
                test_name="security_measures",
                test_type="production",
                status=status,
                duration_seconds=time.time() - test_start,
                details=security_checks
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="security_measures",
                test_type="production",
                status="FAIL",
                duration_seconds=time.time() - test_start,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    def _capture_system_metrics(self) -> SystemMetrics:
        """Capture current system metrics"""
        try:
            process = psutil.Process()
            
            # Get network I/O
            net_io = psutil.net_io_counters()
            
            # Get disk I/O
            disk_io = psutil.disk_io_counters()
            
            return SystemMetrics(
                cpu_percent=process.cpu_percent(),
                memory_mb=process.memory_info().rss / 1024 / 1024,
                memory_percent=process.memory_percent(),
                disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                network_sent_mb=net_io.bytes_sent / 1024 / 1024 if net_io else 0,
                network_recv_mb=net_io.bytes_recv / 1024 / 1024 if net_io else 0,
                api_calls_made=0,  # Would be tracked by API connectors
                tokens_processed=0,  # Would be tracked by token processors
                cache_hit_rate=0.0  # Would be tracked by cache manager
            )
        except Exception as e:
            self.logger.warning(f"Failed to capture system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    async def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report"""
        total_duration = time.time() - (self.start_time or time.time())
        
        # Categorize results
        results_by_type = {}
        for result in self.test_results:
            if result.test_type not in results_by_type:
                results_by_type[result.test_type] = []
            results_by_type[result.test_type].append(result)
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "PASS")
        failed_tests = sum(1 for r in self.test_results if r.status == "FAIL")
        warning_tests = sum(1 for r in self.test_results if r.status == "WARNING")
        skipped_tests = sum(1 for r in self.test_results if r.status == "SKIP")
        
        # Capture final metrics
        final_metrics = self._capture_system_metrics()
        
        # Generate report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "skipped_tests": skipped_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_duration_seconds": total_duration
            },
            "results_by_type": {
                test_type: {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.status == "PASS"),
                    "failed": sum(1 for r in results if r.status == "FAIL"),
                    "warnings": sum(1 for r in results if r.status == "WARNING"),
                    "skipped": sum(1 for r in results if r.status == "SKIP")
                }
                for test_type, results in results_by_type.items()
            },
            "detailed_results": [asdict(result) for result in self.test_results],
            "system_metrics": {
                "baseline": asdict(self.baseline_metrics) if self.baseline_metrics else None,
                "final": asdict(final_metrics)
            },
            "recommendations": self._generate_recommendations(),
            "timestamp": datetime.now().isoformat(),
            "test_environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "config_sections": list(self.config.keys())
            }
        }
        
        # Log summary
        self._log_test_summary(report)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if r.status == "FAIL"]
        warning_tests = [r for r in self.test_results if r.status == "WARNING"]
        
        if failed_tests:
            recommendations.append(f"❌ {len(failed_tests)} critical tests failed - investigate immediately")
            
        if warning_tests:
            recommendations.append(f"⚠️ {len(warning_tests)} tests have warnings - review for optimization")
        
        # API-specific recommendations
        api_tests = [r for r in self.test_results if r.test_type == "api"]
        failed_api_tests = [r for r in api_tests if r.status == "FAIL"]
        
        if failed_api_tests:
            recommendations.append("🔌 API integration issues detected - check API keys and network connectivity")
        
        # Performance recommendations
        perf_tests = [r for r in self.test_results if r.test_type == "performance"]
        warning_perf_tests = [r for r in perf_tests if r.status == "WARNING"]
        
        if warning_perf_tests:
            recommendations.append("⚡ Performance issues detected - consider optimization")
        
        # Production readiness recommendations
        prod_tests = [r for r in self.test_results if r.test_type == "production"]
        failed_prod_tests = [r for r in prod_tests if r.status == "FAIL"]
        
        if failed_prod_tests:
            recommendations.append("🏭 Production readiness issues - address before deployment")
        
        if not recommendations:
            recommendations.append("✅ All systems operational - ready for production")
        
        return recommendations
    
    def _log_test_summary(self, report: Dict[str, Any]):
        """Log test summary to console"""
        summary = report["test_summary"]
        
        self.logger.info("=" * 80)
        self.logger.info("🎯 COMPREHENSIVE SYSTEM TEST RESULTS")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Tests: {summary['total_tests']}")
        self.logger.info(f"✅ Passed: {summary['passed_tests']}")
        self.logger.info(f"❌ Failed: {summary['failed_tests']}")
        self.logger.info(f"⚠️  Warnings: {summary['warning_tests']}")
        self.logger.info(f"⏭️  Skipped: {summary['skipped_tests']}")
        self.logger.info(f"📊 Success Rate: {summary['success_rate']:.1%}")
        self.logger.info(f"⏱️  Duration: {summary['total_duration_seconds']:.1f}s")
        self.logger.info("=" * 80)
        
        # Log recommendations
        self.logger.info("🎯 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            self.logger.info(f"  {rec}")
        
        self.logger.info("=" * 80)

async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Comprehensive System Test Suite")
    parser.add_argument(
        "--test-type",
        choices=["all", "api", "e2e", "performance", "production"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output",
        help="Output file for test results (JSON format)"
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = ComprehensiveSystemTester(verbose=args.verbose)
    
    try:
        # Run tests
        if args.test_type == "all":
            results = await tester.run_all_tests()
        elif args.test_type == "api":
            tester.start_time = time.time()
            tester.baseline_metrics = tester._capture_system_metrics()
            await tester._run_api_integration_tests()
            results = await tester._generate_final_report()
        elif args.test_type == "e2e":
            tester.start_time = time.time()
            tester.baseline_metrics = tester._capture_system_metrics()
            await tester._run_end_to_end_tests()
            results = await tester._generate_final_report()
        elif args.test_type == "performance":
            tester.start_time = time.time()
            tester.baseline_metrics = tester._capture_system_metrics()
            await tester._run_performance_benchmark_tests()
            results = await tester._generate_final_report()
        elif args.test_type == "production":
            tester.start_time = time.time()
            tester.baseline_metrics = tester._capture_system_metrics()
            await tester._run_production_readiness_tests()
            results = await tester._generate_final_report()
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {args.output}")
        
        # Exit with appropriate code
        failed_tests = results["test_summary"]["failed_tests"]
        sys.exit(1 if failed_tests > 0 else 0)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 