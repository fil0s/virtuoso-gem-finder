#!/usr/bin/env python3
"""
Birdeye API Endpoints Test Suite

This script tests all the main Birdeye API methods to ensure they're working correctly
and using current endpoints. It provides a comprehensive health check for the API integration.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup

class BirdeyeEndpointTester:
    """Comprehensive tester for all Birdeye API endpoints"""
    
    def __init__(self):
        # Setup logging
        self.logger_setup = LoggerSetup('BirdeyeEndpointTester', log_level='INFO')
        self.logger = self.logger_setup.logger
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize services
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize Birdeye API
        birdeye_config = self.config.get('BIRDEYE_API', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Test data - using well-known Solana tokens
        self.test_tokens = {
            'SOL': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
            'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'BONK': '85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ'   # BONK (popular meme coin)
        }
        
        # Test wallet addresses (public wallets for testing)
        self.test_wallets = [
            '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',  # Known active wallet
            '3XLkRVg69AgwKAbnSjJpm3PB4QgVeXFEjiXfw5shWMBT'   # Another active wallet
        ]
        
        # Results tracking
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests and return comprehensive results"""
        
        self.logger.info("=" * 80)
        self.logger.info("STARTING BIRDEYE API ENDPOINTS TEST SUITE")
        self.logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test each category of endpoints
        await self._test_token_data_endpoints()
        await self._test_price_endpoints()
        await self._test_trading_endpoints()
        await self._test_wallet_endpoints()
        await self._test_security_endpoints()
        await self._test_discovery_endpoints()
        await self._test_analytics_endpoints()
        
        # Generate summary
        elapsed_time = time.time() - start_time
        await self._generate_test_summary(elapsed_time)
        
        return self.test_results
    
    async def _test_token_data_endpoints(self):
        """Test token data retrieval endpoints"""
        self.logger.info("\n🔍 TESTING TOKEN DATA ENDPOINTS")
        self.logger.info("-" * 50)
        
        test_token = self.test_tokens['BONK']
        
        # Test token overview
        await self._test_endpoint(
            "get_token_overview",
            self.birdeye_api.get_token_overview,
            test_token,
            expected_fields=['price', 'liquidity', 'volume']
        )
        
        # Test token creation info
        await self._test_endpoint(
            "get_token_creation_info", 
            self.birdeye_api.get_token_creation_info,
            test_token,
            expected_fields=['creator', 'blockTime']
        )
        
        # Test token holders
        await self._test_endpoint(
            "get_token_holders",
            lambda addr: self.birdeye_api.get_token_holders(addr, limit=10),
            test_token,
            expected_type=list,
            min_items=1
        )
    
    async def _test_price_endpoints(self):
        """Test price-related endpoints"""
        self.logger.info("\n💰 TESTING PRICE ENDPOINTS")
        self.logger.info("-" * 50)
        
        test_token = self.test_tokens['SOL']
        
        # Test historical price
        timestamp = int(time.time()) - 86400  # 24 hours ago
        await self._test_endpoint(
            "get_historical_price_at_timestamp",
            lambda addr: self.birdeye_api.get_historical_price_at_timestamp(addr, timestamp),
            test_token,
            expected_fields=['price', 'timestamp']
        )
        
        # Test multi price
        await self._test_endpoint(
            "get_multi_price",
            lambda: self.birdeye_api.get_multi_price([test_token]),
            expected_type=dict,
            min_items=1
        )
        
        # Test OHLCV data
        await self._test_endpoint(
            "get_ohlcv_data",
            lambda addr: self.birdeye_api.get_ohlcv_data(addr, time_frame='1h', limit=10),
            test_token,
            expected_type=list
        )
    
    async def _test_trading_endpoints(self):
        """Test trading-related endpoints"""
        self.logger.info("\n📊 TESTING TRADING ENDPOINTS")
        self.logger.info("-" * 50)
        
        test_token = self.test_tokens['BONK']
        
        # Test token trades
        await self._test_endpoint(
            "get_token_trades",
            lambda addr: self.birdeye_api.get_token_trades(addr, limit=10),
            test_token,
            expected_type=list
        )
        
        # Test token transactions
        await self._test_endpoint(
            "get_token_transactions",
            lambda addr: self.birdeye_api.get_token_transactions(addr, limit=10),
            test_token,
            expected_type=list
        )
        
        # Test top traders
        await self._test_endpoint(
            "get_token_top_traders",
            lambda addr: self.birdeye_api.get_token_top_traders(addr, limit=10),
            test_token,
            expected_type=list
        )
        
        # Test transaction volume calculation
        await self._test_endpoint(
            "get_token_transaction_volume",
            lambda addr: self.birdeye_api.get_token_transaction_volume(addr, limit=20),
            test_token,
            expected_type=(int, float),
            min_value=0
        )
    
    async def _test_wallet_endpoints(self):
        """Test wallet-related endpoints"""
        self.logger.info("\n👛 TESTING WALLET ENDPOINTS")
        self.logger.info("-" * 50)
        
        test_wallet = self.test_wallets[0]
        
        # Test wallet portfolio
        await self._test_endpoint(
            "get_wallet_portfolio",
            lambda addr: self.birdeye_api.get_wallet_portfolio(addr),
            test_wallet,
            expected_type=(dict, list)
        )
        
        # Test wallet transaction history
        await self._test_endpoint(
            "get_wallet_transaction_history",
            lambda addr: self.birdeye_api.get_wallet_transaction_history(addr, limit=10),
            test_wallet,
            expected_type=list
        )
        
        # Test trader gainers/losers
        await self._test_endpoint(
            "get_trader_gainers_losers",
            lambda: self.birdeye_api.get_trader_gainers_losers(timeframe="24h", limit=10),
            expected_type=list
        )
    
    async def _test_security_endpoints(self):
        """Test security-related endpoints"""
        self.logger.info("\n🔒 TESTING SECURITY ENDPOINTS")
        self.logger.info("-" * 50)
        
        test_token = self.test_tokens['USDC']  # USDC should be secure
        
        # Test token security
        await self._test_endpoint(
            "get_token_security",
            self.birdeye_api.get_token_security,
            test_token,
            expected_fields=['is_scam', 'is_risky']
        )
        
        # Test smart money detection
        await self._test_endpoint(
            "detect_smart_money_activity",
            lambda addr: self.birdeye_api.detect_smart_money_activity(addr, max_pages=1),
            test_token,
            expected_fields=['has_smart_money', 'smart_money_wallets']
        )
    
    async def _test_discovery_endpoints(self):
        """Test token discovery endpoints"""
        self.logger.info("\n🔎 TESTING DISCOVERY ENDPOINTS")
        self.logger.info("-" * 50)
        
        # Test trending tokens
        await self._test_endpoint(
            "get_trending_tokens",
            self.birdeye_api.get_trending_tokens,
            expected_type=list
        )
        
        # Test new listings
        await self._test_endpoint(
            "get_new_listings",
            self.birdeye_api.get_new_listings,
            expected_type=list
        )
        
        # Test top traders (general)
        test_token = self.test_tokens['SOL']
        await self._test_endpoint(
            "get_top_traders",
            self.birdeye_api.get_top_traders,
            test_token,
            expected_type=list
        )
        
        # Test gainers/losers
        await self._test_endpoint(
            "get_gainers_losers",
            lambda: self.birdeye_api.get_gainers_losers(timeframe="24h"),
            expected_type=list
        )
    
    async def _test_analytics_endpoints(self):
        """Test analytics and metrics endpoints"""
        self.logger.info("\n📈 TESTING ANALYTICS ENDPOINTS")
        self.logger.info("-" * 50)
        
        test_token = self.test_tokens['BONK']
        
        # Test token trade metrics
        await self._test_endpoint(
            "get_token_trade_metrics",
            self.birdeye_api.get_token_trade_metrics,
            test_token,
            expected_fields=['buy_sell_ratios', 'trade_frequency', 'trend_dynamics_score']
        )
        
        # Test historical trade data
        await self._test_endpoint(
            "get_historical_trade_data",
            lambda addr: self.birdeye_api.get_historical_trade_data(addr, [3600, 86400], limit=10),
            test_token,
            expected_type=dict
        )
    
    async def _test_endpoint(self, 
                           endpoint_name: str, 
                           endpoint_func, 
                           *args, 
                           expected_type=None, 
                           expected_fields=None, 
                           min_items=None, 
                           min_value=None):
        """Test a single endpoint with comprehensive validation"""
        
        self.total_tests += 1
        test_start = time.time()
        
        try:
            # Make the API call with timeout
            result = await asyncio.wait_for(endpoint_func(*args), timeout=30.0)
            
            # Basic validation
            if result is None:
                raise ValueError("Endpoint returned None")
            
            # Type validation
            if expected_type and not isinstance(result, expected_type):
                raise TypeError(f"Expected type {expected_type}, got {type(result)}")
            
            # Field validation for dictionaries
            if expected_fields and isinstance(result, dict):
                missing_fields = [field for field in expected_fields if field not in result]
                if missing_fields:
                    self.logger.warning(f"{endpoint_name}: Missing optional fields: {missing_fields}")
            
            # List validation
            if min_items and isinstance(result, list) and len(result) < min_items:
                self.logger.warning(f"{endpoint_name}: Got {len(result)} items, expected at least {min_items}")
            
            # Numeric validation
            if min_value is not None and isinstance(result, (int, float)) and result < min_value:
                raise ValueError(f"Expected value >= {min_value}, got {result}")
            
            # Record success
            elapsed = time.time() - test_start
            self.test_results[endpoint_name] = {
                'status': 'PASS',
                'response_time': round(elapsed, 3),
                'data_type': str(type(result).__name__),
                'data_size': len(result) if isinstance(result, (list, dict)) else 'N/A',
                'sample_data': self._get_sample_data(result)
            }
            
            self.passed_tests += 1
            self.logger.info(f"✅ {endpoint_name}: PASS ({elapsed:.3f}s)")
            
        except asyncio.TimeoutError:
            self.failed_tests += 1
            self.test_results[endpoint_name] = {
                'status': 'TIMEOUT',
                'error': 'Request timed out after 30 seconds'
            }
            self.logger.error(f"⏰ {endpoint_name}: TIMEOUT")
            
        except Exception as e:
            self.failed_tests += 1
            self.test_results[endpoint_name] = {
                'status': 'FAIL',
                'error': str(e),
                'error_type': type(e).__name__
            }
            self.logger.error(f"❌ {endpoint_name}: FAIL - {str(e)}")
        
        # Rate limiting - wait between requests
        await asyncio.sleep(1)
    
    def _get_sample_data(self, result) -> str:
        """Get a sample of the returned data for logging"""
        if isinstance(result, dict):
            keys = list(result.keys())[:3]
            return f"Keys: {keys}"
        elif isinstance(result, list):
            return f"Length: {len(result)}, Sample: {str(result[:2])[:100]}..."
        elif isinstance(result, (int, float)):
            return f"Value: {result}"
        else:
            return str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
    
    async def _generate_test_summary(self, elapsed_time: float):
        """Generate and display test summary"""
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("BIRDEYE API ENDPOINTS TEST SUMMARY")
        self.logger.info("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        self.logger.info(f"Total Tests: {self.total_tests}")
        self.logger.info(f"Passed: {self.passed_tests}")
        self.logger.info(f"Failed: {self.failed_tests}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"Total Time: {elapsed_time:.2f} seconds")
        
        # Show failed tests
        if self.failed_tests > 0:
            self.logger.info("\n❌ FAILED TESTS:")
            for endpoint, result in self.test_results.items():
                if result['status'] != 'PASS':
                    self.logger.error(f"  {endpoint}: {result.get('error', 'Unknown error')}")
        
        # Show successful tests with performance
        self.logger.info("\n✅ SUCCESSFUL TESTS:")
        passed_tests = [(name, data) for name, data in self.test_results.items() if data['status'] == 'PASS']
        
        # Sort by response time
        passed_tests.sort(key=lambda x: x[1]['response_time'])
        
        for endpoint, result in passed_tests:
            self.logger.info(f"  {endpoint}: {result['response_time']}s - {result['data_type']} ({result['data_size']} items)")
        
        # Overall assessment
        if success_rate >= 90:
            self.logger.info("\n🎉 EXCELLENT: Birdeye API integration is working very well!")
        elif success_rate >= 75:
            self.logger.info("\n✅ GOOD: Most Birdeye endpoints are working correctly.")
        elif success_rate >= 50:
            self.logger.info("\n⚠️  FAIR: Some issues detected with Birdeye endpoints.")
        else:
            self.logger.error("\n🚨 POOR: Significant issues with Birdeye API integration!")

async def main():
    """Main test runner"""
    tester = BirdeyeEndpointTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file for analysis
        import json
        results_file = Path(__file__).parent / f"birdeye_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        tester.logger.info(f"\n📁 Detailed results saved to: {results_file}")
        
        return results
        
    except KeyboardInterrupt:
        tester.logger.info("\n🛑 Test suite interrupted by user")
        return None
    except Exception as e:
        tester.logger.error(f"\n💥 Test suite failed with error: {e}")
        return None

if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main()) 