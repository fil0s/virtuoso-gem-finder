#!/usr/bin/env python3
"""
Comprehensive V3 Access Capabilities Test

This script tests all available V3 endpoints and features with the Starter package
to understand the full scope of API access we have.

Based on Birdeye documentation, we'll test:
- Token endpoints
- Market data endpoints  
- Trading data endpoints
- Filtering capabilities
- Rate limits and performance
"""

import asyncio
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from utils.env_loader import load_environment


class V3AccessCapabilitiesTest:
    """Test V3 API access capabilities with Starter package."""
    
    def __init__(self):
        """Initialize the test environment."""
        load_environment()
        self.api_key = os.getenv('BIRDEYE_API_KEY')
        if not self.api_key:
            raise ValueError("BIRDEYE_API_KEY not found in environment")
        
        # Test results storage
        self.test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "package_type": "Starter",
            "endpoints_tested": {},
            "capabilities_summary": {},
            "performance_metrics": {},
            "recommendations": []
        }
    
    async def run_comprehensive_test(self):
        """Run comprehensive V3 access test."""
        print("🔬 V3 Access Capabilities Test")
        print("=" * 50)
        print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔑 API Key status: {'✅ Set' if self.api_key else '❌ Missing'}")
        print()
        
        # Initialize BirdeyeAPI with proper parameters
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        import logging
        
        # Create minimal dependencies
        logger = logging.getLogger('V3Test')
        logger.setLevel(logging.INFO)
        
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        config = {
            'api_key': self.api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20
        }
        
        birdeye_api = BirdeyeAPI(
            config=config,
            logger=logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        try:
            # Test categories
            await self._test_token_endpoints(birdeye_api)
            await self._test_market_data_endpoints(birdeye_api)
            await self._test_trading_data_endpoints(birdeye_api)
            await self._test_filtering_capabilities(birdeye_api)
            await self._test_pagination_features(birdeye_api)
            await self._test_rate_limits(birdeye_api)
            
            # Generate summary
            self._generate_capabilities_summary()
            self._save_results()
            
            print("\n🎉 V3 Access Test Completed!")
            print(f"📊 Results saved to: scripts/results/v3_access_test_{int(time.time())}.json")
            
        finally:
            await birdeye_api.close()
    
    async def _test_token_endpoints(self, api: BirdeyeAPI):
        """Test V3 token-related endpoints."""
        print("🔄 TEST 1: Token Endpoints")
        print("-" * 30)
        
        endpoints_to_test = [
            {
                "name": "Token List",
                "endpoint": "/defi/v3/token/list",
                "method": "get_token_list",
                "params": {"limit": 5}
            },
            {
                "name": "Token Meta Data (Single)",
                "endpoint": "/defi/v3/token/meta-data/single",
                "method": "get_token_metadata",
                "params": {"address": "So11111111111111111111111111111111111111112"}  # SOL
            },
            {
                "name": "Token Market Data",
                "endpoint": "/defi/v3/token/market-data",
                "method": "get_token_market_data",
                "params": {"address": "So11111111111111111111111111111111111111112"}
            },
            {
                "name": "Token Trading Data (Single)",
                "endpoint": "/defi/v3/token/trading-data/single",
                "method": "get_token_trading_data",
                "params": {"address": "So11111111111111111111111111111111111111112"}
            }
        ]
        
        for endpoint_test in endpoints_to_test:
            await self._test_endpoint(api, endpoint_test)
        
        print("✅ Token endpoints test completed\n")
    
    async def _test_market_data_endpoints(self, api: BirdeyeAPI):
        """Test V3 market data endpoints."""
        print("🔄 TEST 2: Market Data Endpoints")
        print("-" * 30)
        
        endpoints_to_test = [
            {
                "name": "Token Holder List",
                "endpoint": "/defi/v3/token/holder",
                "method": "get_token_holders",
                "params": {"address": "So11111111111111111111111111111111111111112", "limit": 5}
            },
            {
                "name": "Token New Listing",
                "endpoint": "/defi/v2/tokens/new_listing",
                "method": "get_new_listings",
                "params": {"limit": 5}
            },
            {
                "name": "Token Trending",
                "endpoint": "/defi/token_trending",
                "method": "get_trending_tokens",
                "params": {"limit": 5}
            }
        ]
        
        for endpoint_test in endpoints_to_test:
            await self._test_endpoint(api, endpoint_test)
        
        print("✅ Market data endpoints test completed\n")
    
    async def _test_trading_data_endpoints(self, api: BirdeyeAPI):
        """Test V3 trading data endpoints."""
        print("🔄 TEST 3: Trading Data Endpoints")
        print("-" * 30)
        
        endpoints_to_test = [
            {
                "name": "Token Top Traders",
                "endpoint": "/defi/v2/tokens/top_traders",
                "method": "get_top_traders",
                "params": {"address": "So11111111111111111111111111111111111111112", "limit": 5}
            },
            {
                "name": "Token Trades",
                "endpoint": "/defi/txs/token",
                "method": "get_token_trades",
                "params": {"address": "So11111111111111111111111111111111111111112", "limit": 5}
            },
            {
                "name": "OHLCV Data",
                "endpoint": "/defi/ohlcv",
                "method": "get_ohlcv",
                "params": {"address": "So11111111111111111111111111111111111111112", "type": "1H"}
            }
        ]
        
        for endpoint_test in endpoints_to_test:
            await self._test_endpoint(api, endpoint_test)
        
        print("✅ Trading data endpoints test completed\n")
    
    async def _test_filtering_capabilities(self, api: BirdeyeAPI):
        """Test advanced filtering capabilities."""
        print("🔄 TEST 4: Advanced Filtering Capabilities")
        print("-" * 30)
        
        filter_tests = [
            {
                "name": "Liquidity Filtering",
                "params": {"min_liquidity": 1000000, "limit": 5}
            },
            {
                "name": "Volume Filtering", 
                "params": {"min_volume_24h_usd": 100000, "limit": 5}
            },
            {
                "name": "Holder Filtering",
                "params": {"min_holder": 1000, "limit": 5}
            },
            {
                "name": "Trade Count Filtering",
                "params": {"min_trade_24h_count": 1000, "limit": 5}
            },
            {
                "name": "Combined Filtering",
                "params": {
                    "min_liquidity": 500000,
                    "min_volume_24h_usd": 50000,
                    "min_holder": 500,
                    "sort_by": "trade_24h_count",
                    "sort_type": "desc",
                    "limit": 10
                }
            }
        ]
        
        for filter_test in filter_tests:
            print(f"🧪 Testing {filter_test['name']}...")
            start_time = time.time()
            
            try:
                result = await api.get_token_list(**filter_test['params'])
                end_time = time.time()
                
                if result and result.get('success'):
                    token_count = len(result.get('data', {}).get('tokens', []))
                    print(f"   ✅ Success: {token_count} tokens found")
                    print(f"   ⏱️  Response time: {(end_time - start_time)*1000:.0f}ms")
                    
                    self.test_results["endpoints_tested"][f"filtering_{filter_test['name'].lower().replace(' ', '_')}"] = {
                        "status": "success",
                        "tokens_found": token_count,
                        "response_time_ms": round((end_time - start_time) * 1000),
                        "params": filter_test['params']
                    }
                else:
                    print(f"   ❌ Failed: {result}")
                    self.test_results["endpoints_tested"][f"filtering_{filter_test['name'].lower().replace(' ', '_')}"] = {
                        "status": "failed",
                        "error": str(result)
                    }
                    
            except Exception as e:
                end_time = time.time()
                print(f"   ❌ Error: {str(e)}")
                self.test_results["endpoints_tested"][f"filtering_{filter_test['name'].lower().replace(' ', '_')}"] = {
                    "status": "error",
                    "error": str(e),
                    "response_time_ms": round((end_time - start_time) * 1000)
                }
            
            # Rate limiting delay
            await asyncio.sleep(1)
        
        print("✅ Filtering capabilities test completed\n")
    
    async def _test_pagination_features(self, api: BirdeyeAPI):
        """Test pagination capabilities."""
        print("🔄 TEST 5: Pagination Features")
        print("-" * 30)
        
        pagination_tests = [
            {"name": "Page 1", "params": {"limit": 10, "offset": 0}},
            {"name": "Page 2", "params": {"limit": 10, "offset": 10}},
            {"name": "Large Page", "params": {"limit": 50, "offset": 0}},
            {"name": "Max Page", "params": {"limit": 100, "offset": 0}}
        ]
        
        for page_test in pagination_tests:
            print(f"🧪 Testing {page_test['name']}...")
            start_time = time.time()
            
            try:
                result = await api.get_token_list(**page_test['params'])
                end_time = time.time()
                
                if result and result.get('success'):
                    data = result.get('data', {})
                    token_count = len(data.get('tokens', []))
                    has_next = data.get('has_next', False)
                    
                    print(f"   ✅ Success: {token_count} tokens")
                    print(f"   📄 Has next page: {has_next}")
                    print(f"   ⏱️  Response time: {(end_time - start_time)*1000:.0f}ms")
                    
                    self.test_results["endpoints_tested"][f"pagination_{page_test['name'].lower().replace(' ', '_')}"] = {
                        "status": "success",
                        "tokens_found": token_count,
                        "has_next": has_next,
                        "response_time_ms": round((end_time - start_time) * 1000),
                        "params": page_test['params']
                    }
                else:
                    print(f"   ❌ Failed: {result}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            await asyncio.sleep(1)
        
        print("✅ Pagination test completed\n")
    
    async def _test_rate_limits(self, api: BirdeyeAPI):
        """Test rate limiting behavior."""
        print("🔄 TEST 6: Rate Limiting Analysis")
        print("-" * 30)
        
        # Test rapid requests
        print("🧪 Testing rapid requests (10 requests in quick succession)...")
        request_times = []
        
        for i in range(10):
            start_time = time.time()
            try:
                result = await api.get_token_list(limit=5)
                end_time = time.time()
                request_times.append(end_time - start_time)
                print(f"   Request {i+1}: {(end_time - start_time)*1000:.0f}ms")
            except Exception as e:
                print(f"   Request {i+1}: Error - {str(e)}")
                break
        
        if request_times:
            avg_time = sum(request_times) / len(request_times)
            print(f"   📊 Average response time: {avg_time*1000:.0f}ms")
            print(f"   📊 Total requests completed: {len(request_times)}/10")
            
            self.test_results["performance_metrics"]["rate_limit_test"] = {
                "requests_completed": len(request_times),
                "average_response_time_ms": round(avg_time * 1000),
                "request_times_ms": [round(t * 1000) for t in request_times]
            }
        
        print("✅ Rate limiting test completed\n")
    
    async def _test_endpoint(self, api: BirdeyeAPI, endpoint_test: Dict):
        """Test individual endpoint."""
        print(f"🧪 Testing {endpoint_test['name']}...")
        start_time = time.time()
        
        try:
            # Try to call the method if it exists
            if hasattr(api, endpoint_test['method']):
                method = getattr(api, endpoint_test['method'])
                result = await method(**endpoint_test['params'])
            else:
                # Direct API call
                result = await api._make_request(endpoint_test['endpoint'], endpoint_test['params'])
            
            end_time = time.time()
            
            if result:
                print(f"   ✅ Success: {endpoint_test['endpoint']}")
                print(f"   ⏱️  Response time: {(end_time - start_time)*1000:.0f}ms")
                
                # Analyze response structure
                if isinstance(result, dict):
                    keys = list(result.keys())[:5]  # First 5 keys
                    print(f"   🔑 Response keys: {keys}")
                
                self.test_results["endpoints_tested"][endpoint_test['method']] = {
                    "endpoint": endpoint_test['endpoint'],
                    "status": "success",
                    "response_time_ms": round((end_time - start_time) * 1000),
                    "response_keys": keys if isinstance(result, dict) else None
                }
            else:
                print(f"   ❌ Failed: No response")
                self.test_results["endpoints_tested"][endpoint_test['method']] = {
                    "endpoint": endpoint_test['endpoint'],
                    "status": "failed",
                    "error": "No response"
                }
                
        except Exception as e:
            end_time = time.time()
            print(f"   ❌ Error: {str(e)}")
            self.test_results["endpoints_tested"][endpoint_test['method']] = {
                "endpoint": endpoint_test['endpoint'],
                "status": "error",
                "error": str(e),
                "response_time_ms": round((end_time - start_time) * 1000)
            }
        
        # Rate limiting delay
        await asyncio.sleep(1)
    
    def _generate_capabilities_summary(self):
        """Generate summary of V3 capabilities."""
        successful_endpoints = [
            name for name, result in self.test_results["endpoints_tested"].items()
            if result.get("status") == "success"
        ]
        
        failed_endpoints = [
            name for name, result in self.test_results["endpoints_tested"].items()
            if result.get("status") in ["failed", "error"]
        ]
        
        self.test_results["capabilities_summary"] = {
            "total_endpoints_tested": len(self.test_results["endpoints_tested"]),
            "successful_endpoints": len(successful_endpoints),
            "failed_endpoints": len(failed_endpoints),
            "success_rate": round(len(successful_endpoints) / len(self.test_results["endpoints_tested"]) * 100, 1),
            "working_endpoints": successful_endpoints,
            "blocked_endpoints": failed_endpoints
        }
        
        # Generate recommendations
        if len(successful_endpoints) > len(failed_endpoints):
            self.test_results["recommendations"].append(
                "Excellent V3 access! Most endpoints are working with Starter package."
            )
        
        if any("filtering" in ep for ep in successful_endpoints):
            self.test_results["recommendations"].append(
                "Advanced filtering capabilities available - leverage for precise token discovery."
            )
        
        if any("pagination" in ep for ep in successful_endpoints):
            self.test_results["recommendations"].append(
                "Pagination working - can access large datasets efficiently."
            )
    
    def _save_results(self):
        """Save test results to file."""
        results_dir = Path("scripts/results")
        results_dir.mkdir(exist_ok=True)
        
        filename = f"v3_access_test_{int(time.time())}.json"
        filepath = results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Also save a summary
        summary_filename = f"v3_access_summary_{int(time.time())}.txt"
        summary_filepath = results_dir / summary_filename
        
        with open(summary_filepath, 'w') as f:
            f.write("V3 Access Capabilities Test Summary\n")
            f.write("=" * 40 + "\n\n")
            
            summary = self.test_results["capabilities_summary"]
            f.write(f"Package Type: {self.test_results['package_type']}\n")
            f.write(f"Test Date: {self.test_results['test_timestamp']}\n\n")
            
            f.write(f"Total Endpoints Tested: {summary['total_endpoints_tested']}\n")
            f.write(f"Successful: {summary['successful_endpoints']}\n")
            f.write(f"Failed: {summary['failed_endpoints']}\n")
            f.write(f"Success Rate: {summary['success_rate']}%\n\n")
            
            f.write("Working Endpoints:\n")
            for ep in summary['working_endpoints']:
                f.write(f"  ✅ {ep}\n")
            
            f.write("\nBlocked Endpoints:\n")
            for ep in summary['blocked_endpoints']:
                f.write(f"  ❌ {ep}\n")
            
            f.write("\nRecommendations:\n")
            for rec in self.test_results['recommendations']:
                f.write(f"  • {rec}\n")


async def main():
    """Run the V3 access capabilities test."""
    test = V3AccessCapabilitiesTest()
    await test.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main()) 