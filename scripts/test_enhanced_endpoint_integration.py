#!/usr/bin/env python3
"""
Enhanced Endpoint Integration Test Suite

This script comprehensively tests the Enhanced Endpoint Integration implementation
including new enrichment services, enhanced strategies, and multi-signal scoring.
"""

import asyncio
import logging
import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigManager
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup

# Import enhanced services
from services.trending_token_monitor import TrendingTokenMonitor
from services.smart_money_detector import SmartMoneyDetector
from services.holder_distribution_analyzer import HolderDistributionAnalyzer

# Import enhanced strategies
from core.strategies.recent_listings_strategy import RecentListingsStrategy
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from core.strategies.volume_momentum_strategy import VolumeMomentumStrategy
from core.strategies.liquidity_growth_strategy import LiquidityGrowthStrategy


class EnhancedEndpointIntegrationTester:
    """
    Comprehensive test suite for Enhanced Endpoint Integration.
    
    Tests:
    - New enrichment services functionality
    - Enhanced strategy implementations
    - Multi-signal scoring system
    - Performance and caching
    - Error handling and fallbacks
    """
    
    def __init__(self):
        """Initialize the test suite."""
        # Setup logging
        self.logger_setup = LoggerSetup("EnhancedIntegrationTest")
        self.logger = self.logger_setup.logger
        
        # Load enhanced configuration
        self.config_manager = ConfigManager()
        try:
            # Try to load enhanced config, fallback to default
            self.config = self.config_manager.load_config("config/config.enhanced.yaml")
            self.logger.info("✅ Loaded enhanced configuration")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load enhanced config, using default: {e}")
            self.config = self.config_manager.get_config()
        
        # Initialize core services
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService(self.config.get('api', {}).get('birdeye', {}))
        
        # Initialize Birdeye API
        birdeye_config = self.config.get('api', {}).get('birdeye', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Test results storage
        self.test_results = {
            'services_tests': {},
            'strategies_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'overall_success': False,
            'test_timestamp': time.time()
        }
        
        self.logger.info("🚀 Enhanced Endpoint Integration Tester initialized")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all test suites.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("🧪 Starting Enhanced Endpoint Integration Test Suite")
        
        try:
            # Phase 1: Test enrichment services
            await self._test_enrichment_services()
            
            # Phase 2: Test enhanced strategies
            await self._test_enhanced_strategies()
            
            # Phase 3: Test integration and scoring
            await self._test_integration_and_scoring()
            
            # Phase 4: Test performance and caching
            await self._test_performance_and_caching()
            
            # Calculate overall success
            self._calculate_overall_success()
            
            # Generate test report
            await self._generate_test_report()
            
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"❌ Test suite failed with error: {e}")
            self.test_results['overall_success'] = False
            self.test_results['error'] = str(e)
            return self.test_results
        
        finally:
            await self.birdeye_api.close_session()
    
    async def _test_enrichment_services(self):
        """Test the three new enrichment services."""
        self.logger.info("📊 Testing enrichment services...")
        
        # Test Trending Token Monitor
        await self._test_trending_token_monitor()
        
        # Test Smart Money Detector
        await self._test_smart_money_detector()
        
        # Test Holder Distribution Analyzer
        await self._test_holder_distribution_analyzer()
    
    async def _test_trending_token_monitor(self):
        """Test the TrendingTokenMonitor service."""
        self.logger.info("🔥 Testing TrendingTokenMonitor...")
        
        test_result = {
            'service_name': 'TrendingTokenMonitor',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize service
            trending_monitor = TrendingTokenMonitor(self.logger)
            
            # Test 1: Get trending tokens
            try:
                trending_tokens = await trending_monitor.get_trending_tokens(self.birdeye_api, limit=10)
                if isinstance(trending_tokens, list):
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Retrieved {len(trending_tokens)} trending tokens")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid trending tokens response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Failed to get trending tokens: {e}")
            
            # Test 2: Check trending status for a token
            try:
                if trending_tokens and len(trending_tokens) > 0:
                    test_address = trending_tokens[0].get('address')
                    if test_address:
                        trending_status = trending_monitor.is_token_trending(test_address)
                        if isinstance(trending_status, dict) and 'is_trending' in trending_status:
                            test_result['tests_passed'] += 1
                            test_result['details'].append("✅ Trending status check working")
                        else:
                            test_result['tests_failed'] += 1
                            test_result['details'].append("❌ Invalid trending status response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Trending status check failed: {e}")
            
            # Test 3: Get metrics
            try:
                metrics = trending_monitor.get_metrics()
                if isinstance(metrics, dict) and 'total_requests' in metrics:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ Metrics collection working")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid metrics response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Metrics collection failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Service initialization failed: {e}")
        
        self.test_results['services_tests']['trending_monitor'] = test_result
        self.logger.info(f"🔥 TrendingTokenMonitor: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_smart_money_detector(self):
        """Test the SmartMoneyDetector service."""
        self.logger.info("🧠 Testing SmartMoneyDetector...")
        
        test_result = {
            'service_name': 'SmartMoneyDetector',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize service
            smart_money_detector = SmartMoneyDetector(self.logger)
            
            # Get a test token address (use SOL as it should have trader data)
            test_address = "So11111111111111111111111111111111111111112"  # Wrapped SOL
            
            # Test 1: Analyze token traders
            try:
                trader_analysis = await smart_money_detector.analyze_token_traders(
                    self.birdeye_api, test_address, limit=10
                )
                if isinstance(trader_analysis, dict) and 'smart_money_detected' in trader_analysis:
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Trader analysis completed for {test_address}")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid trader analysis response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Trader analysis failed: {e}")
            
            # Test 2: Check smart money activity
            try:
                smart_money_status = smart_money_detector.is_smart_money_active(test_address)
                if isinstance(smart_money_status, dict) and 'is_active' in smart_money_status:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ Smart money status check working")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid smart money status response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Smart money status check failed: {e}")
            
            # Test 3: Get metrics
            try:
                metrics = smart_money_detector.get_metrics()
                if isinstance(metrics, dict) and 'total_requests' in metrics:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ Metrics collection working")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid metrics response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Metrics collection failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Service initialization failed: {e}")
        
        self.test_results['services_tests']['smart_money_detector'] = test_result
        self.logger.info(f"🧠 SmartMoneyDetector: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_holder_distribution_analyzer(self):
        """Test the HolderDistributionAnalyzer service."""
        self.logger.info("👥 Testing HolderDistributionAnalyzer...")
        
        test_result = {
            'service_name': 'HolderDistributionAnalyzer',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize service
            holder_analyzer = HolderDistributionAnalyzer(self.logger)
            
            # Get a test token address
            test_address = "So11111111111111111111111111111111111111112"  # Wrapped SOL
            
            # Test 1: Analyze holder distribution
            try:
                holder_analysis = await holder_analyzer.analyze_holder_distribution(
                    self.birdeye_api, test_address, limit=50
                )
                if isinstance(holder_analysis, dict) and 'risk_level' in holder_analysis:
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Holder analysis completed for {test_address}")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid holder analysis response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Holder analysis failed: {e}")
            
            # Test 2: Check distribution health
            try:
                distribution_health = holder_analyzer.is_distribution_healthy(test_address)
                if isinstance(distribution_health, dict) and 'is_healthy' in distribution_health:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ Distribution health check working")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid distribution health response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Distribution health check failed: {e}")
            
            # Test 3: Get metrics
            try:
                metrics = holder_analyzer.get_metrics()
                if isinstance(metrics, dict) and 'total_requests' in metrics:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ Metrics collection working")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid metrics response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Metrics collection failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Service initialization failed: {e}")
        
        self.test_results['services_tests']['holder_analyzer'] = test_result
        self.logger.info(f"👥 HolderDistributionAnalyzer: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_enhanced_strategies(self):
        """Test the enhanced strategy implementations."""
        self.logger.info("🎯 Testing enhanced strategies...")
        
        # Test each enhanced strategy
        await self._test_recent_listings_strategy()
        await self._test_high_trading_activity_strategy()
        await self._test_volume_momentum_strategy()
        await self._test_liquidity_growth_strategy()
    
    async def _test_recent_listings_strategy(self):
        """Test the enhanced Recent Listings Strategy."""
        self.logger.info("🆕 Testing Enhanced Recent Listings Strategy...")
        
        test_result = {
            'strategy_name': 'RecentListingsStrategy',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize strategy
            strategy = RecentListingsStrategy(self.logger)
            
            # Test 1: Execute strategy
            try:
                tokens = await strategy.execute(self.birdeye_api)
                if isinstance(tokens, list):
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Strategy executed, found {len(tokens)} tokens")
                    
                    # Check for enhanced features
                    if tokens:
                        sample_token = tokens[0]
                        if 'strategy_analysis' in sample_token:
                            test_result['tests_passed'] += 1
                            test_result['details'].append("✅ Enhanced strategy analysis present")
                        else:
                            test_result['tests_failed'] += 1
                            test_result['details'].append("❌ Missing enhanced strategy analysis")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid strategy execution response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Strategy execution failed: {e}")
            
            # Test 2: Test new listings data method
            try:
                new_listings = await strategy._get_new_listings_data(self.birdeye_api, limit=5)
                if isinstance(new_listings, list):
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ New listings data retrieved: {len(new_listings)} listings")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid new listings data response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ New listings data retrieval failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Strategy initialization failed: {e}")
        
        self.test_results['strategies_tests']['recent_listings'] = test_result
        self.logger.info(f"🆕 Recent Listings Strategy: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_high_trading_activity_strategy(self):
        """Test the enhanced High Trading Activity Strategy."""
        self.logger.info("⚡ Testing Enhanced High Trading Activity Strategy...")
        
        test_result = {
            'strategy_name': 'HighTradingActivityStrategy',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize strategy
            strategy = HighTradingActivityStrategy(self.logger)
            
            # Test strategy execution
            try:
                tokens = await strategy.execute(self.birdeye_api)
                if isinstance(tokens, list):
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Strategy executed, found {len(tokens)} tokens")
                    
                    # Check for smart money validation features
                    if tokens:
                        sample_token = tokens[0]
                        if 'strategy_analysis' in sample_token:
                            analysis = sample_token['strategy_analysis']
                            if 'smart_money_validation' in analysis:
                                test_result['tests_passed'] += 1
                                test_result['details'].append("✅ Smart money validation present")
                            else:
                                test_result['tests_failed'] += 1
                                test_result['details'].append("❌ Missing smart money validation")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid strategy execution response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Strategy execution failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Strategy initialization failed: {e}")
        
        self.test_results['strategies_tests']['high_trading_activity'] = test_result
        self.logger.info(f"⚡ High Trading Activity Strategy: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_volume_momentum_strategy(self):
        """Test the enhanced Volume Momentum Strategy."""
        self.logger.info("📈 Testing Enhanced Volume Momentum Strategy...")
        
        test_result = {
            'strategy_name': 'VolumeMomentumStrategy',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize strategy
            strategy = VolumeMomentumStrategy(self.logger)
            
            # Test strategy execution
            try:
                tokens = await strategy.execute(self.birdeye_api)
                if isinstance(tokens, list):
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Strategy executed, found {len(tokens)} tokens")
                    
                    # Check for trending cross-reference features
                    if tokens:
                        sample_token = tokens[0]
                        if 'strategy_analysis' in sample_token:
                            analysis = sample_token['strategy_analysis']
                            if 'trending_confirmation' in analysis:
                                test_result['tests_passed'] += 1
                                test_result['details'].append("✅ Trending cross-reference present")
                            else:
                                test_result['tests_failed'] += 1
                                test_result['details'].append("❌ Missing trending cross-reference")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid strategy execution response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Strategy execution failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Strategy initialization failed: {e}")
        
        self.test_results['strategies_tests']['volume_momentum'] = test_result
        self.logger.info(f"📈 Volume Momentum Strategy: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_liquidity_growth_strategy(self):
        """Test the enhanced Liquidity Growth Strategy."""
        self.logger.info("💧 Testing Enhanced Liquidity Growth Strategy...")
        
        test_result = {
            'strategy_name': 'LiquidityGrowthStrategy',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Initialize strategy
            strategy = LiquidityGrowthStrategy(self.logger)
            
            # Test strategy execution
            try:
                tokens = await strategy.execute(self.birdeye_api)
                if isinstance(tokens, list):
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Strategy executed, found {len(tokens)} tokens")
                    
                    # Check for holder distribution features
                    if tokens:
                        sample_token = tokens[0]
                        if 'strategy_analysis' in sample_token:
                            analysis = sample_token['strategy_analysis']
                            if 'holder_distribution_quality' in analysis:
                                test_result['tests_passed'] += 1
                                test_result['details'].append("✅ Holder distribution analysis present")
                            else:
                                test_result['tests_failed'] += 1
                                test_result['details'].append("❌ Missing holder distribution analysis")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Invalid strategy execution response")
            except Exception as e:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Strategy execution failed: {e}")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Strategy initialization failed: {e}")
        
        self.test_results['strategies_tests']['liquidity_growth'] = test_result
        self.logger.info(f"💧 Liquidity Growth Strategy: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_integration_and_scoring(self):
        """Test end-to-end integration and enhanced scoring."""
        self.logger.info("🎯 Testing integration and enhanced scoring...")
        
        test_result = {
            'test_name': 'Integration and Scoring',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Test full pipeline with one strategy
            strategy = RecentListingsStrategy(self.logger)
            
            # Execute with full enrichment pipeline
            tokens = await strategy.execute(self.birdeye_api)
            
            if tokens and len(tokens) > 0:
                sample_token = tokens[0]
                
                # Test 1: Check for enrichment data
                enrichment_fields = [
                    'is_trending', 'smart_money_detected', 'holder_analysis',
                    'trending_boost_applied', 'smart_money_boost_applied', 'holder_adjustment_factor'
                ]
                
                missing_fields = []
                for field in enrichment_fields:
                    if field not in sample_token:
                        missing_fields.append(field)
                
                if not missing_fields:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ All enrichment fields present")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append(f"❌ Missing enrichment fields: {missing_fields}")
                
                # Test 2: Check for enhanced scoring
                if 'enhanced_score' in sample_token and 'enhancement_summary' in sample_token:
                    test_result['tests_passed'] += 1
                    test_result['details'].append("✅ Enhanced scoring system working")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Enhanced scoring system not working")
                
                # Test 3: Check score enhancement factors
                if 'enhancement_factors' in sample_token:
                    test_result['tests_passed'] += 1
                    test_result['details'].append(f"✅ Enhancement factors tracked: {len(sample_token['enhancement_factors'])}")
                else:
                    test_result['tests_failed'] += 1
                    test_result['details'].append("❌ Enhancement factors not tracked")
            
            else:
                test_result['tests_failed'] += 1
                test_result['details'].append("❌ No tokens returned from strategy")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Integration test failed: {e}")
        
        self.test_results['integration_tests']['scoring_integration'] = test_result
        self.logger.info(f"🎯 Integration and Scoring: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    async def _test_performance_and_caching(self):
        """Test performance and caching functionality."""
        self.logger.info("⚡ Testing performance and caching...")
        
        test_result = {
            'test_name': 'Performance and Caching',
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        try:
            # Test caching with trending monitor
            trending_monitor = TrendingTokenMonitor(self.logger)
            
            # First call (cache miss)
            start_time = time.time()
            tokens1 = await trending_monitor.get_trending_tokens(self.birdeye_api, limit=5)
            first_call_time = time.time() - start_time
            
            # Second call (should be cache hit)
            start_time = time.time()
            tokens2 = await trending_monitor.get_trending_tokens(self.birdeye_api, limit=5)
            second_call_time = time.time() - start_time
            
            # Test cache effectiveness
            if second_call_time < first_call_time * 0.5:  # Second call should be much faster
                test_result['tests_passed'] += 1
                test_result['details'].append(f"✅ Caching effective: {first_call_time:.2f}s -> {second_call_time:.2f}s")
            else:
                test_result['tests_failed'] += 1
                test_result['details'].append(f"❌ Caching not effective: {first_call_time:.2f}s -> {second_call_time:.2f}s")
            
            # Test metrics collection
            metrics = trending_monitor.get_metrics()
            if metrics['cache_hits'] > 0:
                test_result['tests_passed'] += 1
                test_result['details'].append("✅ Cache hits tracked correctly")
            else:
                test_result['tests_failed'] += 1
                test_result['details'].append("❌ Cache hits not tracked")
            
        except Exception as e:
            test_result['tests_failed'] += 1
            test_result['details'].append(f"❌ Performance test failed: {e}")
        
        self.test_results['performance_tests']['caching'] = test_result
        self.logger.info(f"⚡ Performance and Caching: {test_result['tests_passed']} passed, {test_result['tests_failed']} failed")
    
    def _calculate_overall_success(self):
        """Calculate overall test success rate."""
        total_passed = 0
        total_failed = 0
        
        # Count all test results
        for category in ['services_tests', 'strategies_tests', 'integration_tests', 'performance_tests']:
            for test_name, test_data in self.test_results.get(category, {}).items():
                total_passed += test_data.get('tests_passed', 0)
                total_failed += test_data.get('tests_failed', 0)
        
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        self.test_results['total_tests'] = total_tests
        self.test_results['tests_passed'] = total_passed
        self.test_results['tests_failed'] = total_failed
        self.test_results['success_rate'] = success_rate
        self.test_results['overall_success'] = success_rate >= 80  # 80% success threshold
        
        self.logger.info(f"📊 Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests})")
    
    async def _generate_test_report(self):
        """Generate comprehensive test report."""
        self.logger.info("📋 Generating test report...")
        
        report_path = Path("scripts/results/enhanced_integration_test_results.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp and summary
        self.test_results['test_duration'] = time.time() - self.test_results['test_timestamp']
        self.test_results['test_summary'] = {
            'enhanced_services_working': len([t for t in self.test_results.get('services_tests', {}).values() if t['tests_passed'] > t['tests_failed']]),
            'enhanced_strategies_working': len([t for t in self.test_results.get('strategies_tests', {}).values() if t['tests_passed'] > t['tests_failed']]),
            'integration_working': len([t for t in self.test_results.get('integration_tests', {}).values() if t['tests_passed'] > t['tests_failed']]),
            'performance_working': len([t for t in self.test_results.get('performance_tests', {}).values() if t['tests_passed'] > t['tests_failed']])
        }
        
        # Save detailed results
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"📋 Test report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*80)
        print("🧪 ENHANCED ENDPOINT INTEGRATION TEST RESULTS")
        print("="*80)
        print(f"Overall Success: {'✅ PASS' if self.test_results['overall_success'] else '❌ FAIL'}")
        print(f"Success Rate: {self.test_results['success_rate']:.1f}%")
        print(f"Tests Passed: {self.test_results['tests_passed']}")
        print(f"Tests Failed: {self.test_results['tests_failed']}")
        print(f"Test Duration: {self.test_results['test_duration']:.2f} seconds")
        print("\n📊 Service Status:")
        
        for service_name, result in self.test_results.get('services_tests', {}).items():
            status = "✅" if result['tests_passed'] > result['tests_failed'] else "❌"
            print(f"  {status} {service_name}: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']}")
        
        print("\n🎯 Strategy Status:")
        for strategy_name, result in self.test_results.get('strategies_tests', {}).items():
            status = "✅" if result['tests_passed'] > result['tests_failed'] else "❌"
            print(f"  {status} {strategy_name}: {result['tests_passed']}/{result['tests_passed'] + result['tests_failed']}")
        
        print("="*80)


async def main():
    """Run the enhanced endpoint integration test suite."""
    tester = EnhancedEndpointIntegrationTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_success'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main()) 