#!/usr/bin/env python3
"""
Test API Parameter Fixes

This script tests the Liquidity Growth and Recent Listings strategies
after fixing the API parameter errors to ensure they work correctly.
"""

import os
import sys
import asyncio
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from core.strategies import LiquidityGrowthStrategy, RecentListingsStrategy


class APIParameterFixTester:
    """Test the fixed API parameters for Liquidity Growth and Recent Listings strategies."""
    
    def __init__(self):
        """Initialize the tester."""
        self.logger_setup = LoggerSetup("APIParameterFixTest")
        self.logger = self.logger_setup.logger
        self.test_results = {}
        self.test_timestamp = int(time.time())
        
    async def run_tests(self):
        """Run all API parameter fix tests."""
        self.logger.info("🔧 Starting API Parameter Fix Tests")
        self.logger.info("=" * 60)
        
        # Initialize Birdeye API
        birdeye_api = await self._initialize_birdeye_api()
        scan_id = f"api_fix_test_{self.test_timestamp}"
        
        try:
            # Test Liquidity Growth Strategy
            await self._test_liquidity_growth_strategy(birdeye_api, scan_id)
            
            # Test Recent Listings Strategy  
            await self._test_recent_listings_strategy(birdeye_api, scan_id)
            
            # Generate summary report
            await self._generate_summary_report()
            
        except Exception as e:
            self.logger.error(f"❌ Error in API parameter fix tests: {e}")
            raise
        finally:
            # Clean up
            if birdeye_api:
                await birdeye_api.close()
    
    async def _initialize_birdeye_api(self) -> BirdeyeAPI:
        """Initialize BirdeyeAPI with required dependencies."""
        import os
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        # Check API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY environment variable not set")
        
        # Initialize services
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        # Create config for BirdeyeAPI
        config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        # Create logger for BirdeyeAPI
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        
        birdeye_api = BirdeyeAPI(config, birdeye_logger.logger, cache_manager, rate_limiter)
        
        self.logger.info("✅ BirdeyeAPI initialized successfully")
        return birdeye_api
    
    async def _test_liquidity_growth_strategy(self, birdeye_api: BirdeyeAPI, scan_id: str):
        """Test the fixed Liquidity Growth Strategy."""
        self.logger.info("🧪 Testing Liquidity Growth Strategy (Fixed API Parameters)")
        
        test_result = {
            "strategy_name": "Liquidity Growth Strategy",
            "test_timestamp": self.test_timestamp,
            "execution_successful": False,
            "tokens_found": 0,
            "execution_time": 0,
            "api_calls_made": 0,
            "errors": [],
            "market_cap_filtering": {
                "tokens_before_filter": 0,
                "tokens_after_filter": 0,
                "tokens_filtered_out": 0
            },
            "api_parameters_used": {},
            "market_cap_filters_used": {}
        }
        
        try:
            # Initialize strategy
            strategy = LiquidityGrowthStrategy(logger=self.logger)
            
            # Record API parameters used
            test_result["api_parameters_used"] = strategy.api_parameters.copy()
            test_result["market_cap_filters_used"] = strategy.market_cap_filters.copy()
            
            self.logger.info(f"📊 API Parameters: {strategy.api_parameters}")
            self.logger.info(f"🎯 Market Cap Filters: {strategy.market_cap_filters}")
            
            # Get API stats before execution
            pre_stats = birdeye_api.get_api_call_statistics()
            
            # Execute strategy
            start_time = time.time()
            tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_liquidity_growth")
            execution_time = time.time() - start_time
            
            # Get API stats after execution
            post_stats = birdeye_api.get_api_call_statistics()
            api_calls_made = post_stats['total_api_calls'] - pre_stats['total_api_calls']
            
            # Record results
            test_result["execution_successful"] = True
            test_result["tokens_found"] = len(tokens)
            test_result["execution_time"] = execution_time
            test_result["api_calls_made"] = api_calls_made
            
            self.logger.info(f"✅ Liquidity Growth Strategy executed successfully!")
            self.logger.info(f"   📊 Tokens found: {len(tokens)}")
            self.logger.info(f"   ⏱️  Execution time: {execution_time:.2f}s")
            self.logger.info(f"   📡 API calls made: {api_calls_made}")
            
            # Analyze market cap filtering effectiveness
            if tokens:
                market_caps = [t.get("marketCap", 0) for t in tokens]
                valid_market_caps = [mc for mc in market_caps if mc > 0]
                
                if valid_market_caps:
                    min_mc = min(valid_market_caps)
                    max_mc = max(valid_market_caps)
                    avg_mc = sum(valid_market_caps) / len(valid_market_caps)
                    
                    self.logger.info(f"   💰 Market Cap Range: ${min_mc:,.0f} - ${max_mc:,.0f}")
                    self.logger.info(f"   💰 Average Market Cap: ${avg_mc:,.0f}")
                    
                    # Check if filtering is working
                    min_filter = strategy.market_cap_filters["min_market_cap"]
                    max_filter = strategy.market_cap_filters["max_market_cap"]
                    
                    tokens_below_min = len([mc for mc in valid_market_caps if mc < min_filter])
                    tokens_above_max = len([mc for mc in valid_market_caps if mc > max_filter])
                    
                    if tokens_below_min == 0 and tokens_above_max == 0:
                        self.logger.info("   ✅ Market cap filtering working correctly - all tokens within range")
                    else:
                        self.logger.warning(f"   ⚠️  Market cap filtering issue: {tokens_below_min} below min, {tokens_above_max} above max")
                
                # Log sample tokens
                self.logger.info("   📋 Sample tokens found:")
                for i, token in enumerate(tokens[:3]):
                    symbol = token.get("symbol", "Unknown")
                    market_cap = token.get("marketCap", 0)
                    liquidity = token.get("liquidity", 0)
                    self.logger.info(f"     {i+1}. {symbol} - MC: ${market_cap:,.0f}, Liquidity: ${liquidity:,.0f}")
            
        except Exception as e:
            test_result["execution_successful"] = False
            test_result["errors"].append(str(e))
            self.logger.error(f"❌ Liquidity Growth Strategy test failed: {e}")
        
        self.test_results["liquidity_growth"] = test_result
    
    async def _test_recent_listings_strategy(self, birdeye_api: BirdeyeAPI, scan_id: str):
        """Test the fixed Recent Listings Strategy."""
        self.logger.info("🧪 Testing Recent Listings Strategy (Fixed API Parameters)")
        
        test_result = {
            "strategy_name": "Recent Listings Strategy",
            "test_timestamp": self.test_timestamp,
            "execution_successful": False,
            "tokens_found": 0,
            "execution_time": 0,
            "api_calls_made": 0,
            "errors": [],
            "new_listings_detection": {
                "new_listings_endpoint_called": False,
                "new_listings_found": 0,
                "cross_referenced_tokens": 0
            },
            "api_parameters_used": {}
        }
        
        try:
            # Initialize strategy
            strategy = RecentListingsStrategy(logger=self.logger)
            
            # Record API parameters used
            test_result["api_parameters_used"] = strategy.api_parameters.copy()
            
            self.logger.info(f"📊 API Parameters: {strategy.api_parameters}")
            
            # Get API stats before execution
            pre_stats = birdeye_api.get_api_call_statistics()
            
            # Execute strategy
            start_time = time.time()
            tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_recent_listings")
            execution_time = time.time() - start_time
            
            # Get API stats after execution
            post_stats = birdeye_api.get_api_call_statistics()
            api_calls_made = post_stats['total_api_calls'] - pre_stats['total_api_calls']
            
            # Record results
            test_result["execution_successful"] = True
            test_result["tokens_found"] = len(tokens)
            test_result["execution_time"] = execution_time
            test_result["api_calls_made"] = api_calls_made
            
            self.logger.info(f"✅ Recent Listings Strategy executed successfully!")
            self.logger.info(f"   📊 Tokens found: {len(tokens)}")
            self.logger.info(f"   ⏱️  Execution time: {execution_time:.2f}s")
            self.logger.info(f"   📡 API calls made: {api_calls_made}")
            
            # Analyze new listings detection
            if tokens:
                new_listing_matches = len([t for t in tokens if t.get("new_listing_match")])
                holder_velocity_tokens = len([t for t in tokens if t.get("holder_velocity_analysis", {}).get("velocity_score", 0) > 0])
                
                test_result["new_listings_detection"]["new_listings_found"] = new_listing_matches
                test_result["new_listings_detection"]["cross_referenced_tokens"] = new_listing_matches
                
                self.logger.info(f"   🆕 New listing matches: {new_listing_matches}")
                self.logger.info(f"   👥 Holder velocity analysis: {holder_velocity_tokens} tokens")
                
                # Log sample tokens
                self.logger.info("   📋 Sample tokens found:")
                for i, token in enumerate(tokens[:3]):
                    symbol = token.get("symbol", "Unknown")
                    liquidity = token.get("liquidity", 0)
                    is_new_listing = token.get("new_listing_match", False)
                    velocity_score = token.get("holder_velocity_analysis", {}).get("velocity_score", 0)
                    self.logger.info(f"     {i+1}. {symbol} - Liquidity: ${liquidity:,.0f}, New: {is_new_listing}, Velocity: {velocity_score:.2f}")
            
        except Exception as e:
            test_result["execution_successful"] = False
            test_result["errors"].append(str(e))
            self.logger.error(f"❌ Recent Listings Strategy test failed: {e}")
        
        self.test_results["recent_listings"] = test_result
    
    async def _generate_summary_report(self):
        """Generate a summary report of the test results."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 API PARAMETER FIX TEST SUMMARY")
        self.logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results.values() if r["execution_successful"]])
        
        self.logger.info(f"🎯 Tests Run: {total_tests}")
        self.logger.info(f"✅ Successful: {successful_tests}")
        self.logger.info(f"❌ Failed: {total_tests - successful_tests}")
        
        # Strategy-specific results
        for strategy_key, result in self.test_results.items():
            strategy_name = result["strategy_name"]
            success = result["execution_successful"]
            tokens_found = result["tokens_found"]
            
            status_emoji = "✅" if success else "❌"
            self.logger.info(f"\n{status_emoji} {strategy_name}:")
            self.logger.info(f"   📊 Tokens Found: {tokens_found}")
            self.logger.info(f"   ⏱️  Execution Time: {result['execution_time']:.2f}s")
            self.logger.info(f"   📡 API Calls: {result['api_calls_made']}")
            
            if result["errors"]:
                self.logger.info(f"   ❌ Errors: {', '.join(result['errors'])}")
        
        # Overall assessment
        if successful_tests == total_tests:
            self.logger.info("\n🎉 ALL TESTS PASSED! API parameter fixes are working correctly.")
        else:
            self.logger.warning(f"\n⚠️  {total_tests - successful_tests} tests failed. Review errors above.")
        
        # Save detailed results
        await self._save_test_results()
    
    async def _save_test_results(self):
        """Save detailed test results to file."""
        try:
            results_dir = Path("scripts/results")
            results_dir.mkdir(exist_ok=True)
            
            timestamp_str = datetime.fromtimestamp(self.test_timestamp).strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"api_parameter_fix_test_{timestamp_str}.json"
            
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            self.logger.info(f"📄 Detailed results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving test results: {e}")


async def main():
    """Main function to run API parameter fix tests."""
    print("🔧 Starting API Parameter Fix Tests")
    print("=" * 60)
    
    try:
        tester = APIParameterFixTester()
        await tester.run_tests()
        
        print("\n✅ API Parameter Fix Tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 