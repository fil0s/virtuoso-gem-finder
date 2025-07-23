#!/usr/bin/env python3
"""
Direct Endpoint Access Test

This script tests the endpoints that showed "Method not implemented" errors
by calling them directly to determine if they're actually accessible with
the Starter package or if it was just a method signature issue.
"""

import asyncio
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from utils.env_loader import load_environment
import logging


class DirectEndpointTest:
    """Test direct endpoint access for supposedly blocked endpoints."""
    
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
            "direct_endpoint_tests": {},
            "method_tests": {},
            "summary": {}
        }
    
    async def run_direct_endpoint_test(self):
        """Run direct endpoint access test."""
        print("🔬 Direct Endpoint Access Test")
        print("=" * 50)
        print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔑 API Key status: {'✅ Set' if self.api_key else '❌ Missing'}")
        print()
        
        # Initialize BirdeyeAPI
        logger = logging.getLogger('DirectEndpointTest')
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
            # Test the "blocked" endpoints directly
            await self._test_direct_endpoints(birdeye_api)
            await self._test_method_implementations(birdeye_api)
            
            # Generate summary
            self._generate_summary()
            self._save_results()
            
            print("\\n🎉 Direct Endpoint Test Completed!")
            print(f"📊 Results saved to: scripts/results/direct_endpoint_test_{int(time.time())}.json")
            
        finally:
            await birdeye_api.close()
    
    async def _test_direct_endpoints(self, api: BirdeyeAPI):
        """Test endpoints directly via _make_request."""
        print("🔄 TEST 1: Direct Endpoint Calls")
        print("-" * 30)
        
        # Test token (SOL) for consistency
        test_token = "So11111111111111111111111111111111111111112"
        
        endpoints_to_test = [
            {
                "name": "Token Holders",
                "endpoint": "/defi/v3/token/holder",
                "params": {"address": test_token, "limit": 5}
            },
            {
                "name": "New Listings",
                "endpoint": "/defi/v2/tokens/new_listing", 
                "params": {"limit": 5}
            },
            {
                "name": "Trending Tokens",
                "endpoint": "/defi/token_trending",
                "params": {"limit": 5}
            },
            {
                "name": "Top Traders",
                "endpoint": "/defi/v2/tokens/top_traders",
                "params": {"address": test_token, "limit": 5}
            },
            {
                "name": "Token Trading Data Single",
                "endpoint": "/defi/v3/token/trading-data/single",
                "params": {"address": test_token}
            }
        ]
        
        for endpoint_test in endpoints_to_test:
            await self._test_direct_endpoint(api, endpoint_test)
        
        print("✅ Direct endpoint tests completed\\n")
    
    async def _test_method_implementations(self, api: BirdeyeAPI):
        """Test the actual method implementations with correct parameters."""
        print("🔄 TEST 2: Method Implementation Tests")
        print("-" * 30)
        
        test_token = "So11111111111111111111111111111111111111112"
        
        method_tests = [
            {
                "name": "get_token_holders",
                "method": "get_token_holders",
                "params": {"token_address": test_token, "limit": 5}
            },
            {
                "name": "get_new_listings", 
                "method": "get_new_listings",
                "params": {}
            },
            {
                "name": "get_trending_tokens",
                "method": "get_trending_tokens", 
                "params": {}
            },
            {
                "name": "get_top_traders",
                "method": "get_top_traders",
                "params": {"token_address": test_token}
            }
        ]
        
        for method_test in method_tests:
            await self._test_method_implementation(api, method_test)
        
        print("✅ Method implementation tests completed\\n")
    
    async def _test_direct_endpoint(self, api: BirdeyeAPI, endpoint_test: Dict):
        """Test individual endpoint directly."""
        print(f"🧪 Testing {endpoint_test['name']} directly...")
        start_time = time.time()
        
        try:
            result = await api._make_request(endpoint_test['endpoint'], endpoint_test['params'])
            end_time = time.time()
            
            if result:
                print(f"   ✅ Success: {endpoint_test['endpoint']}")
                print(f"   ⏱️  Response time: {(end_time - start_time)*1000:.0f}ms")
                
                # Analyze response structure
                if isinstance(result, dict):
                    keys = list(result.keys())[:5]  # First 5 keys
                    print(f"   🔑 Response keys: {keys}")
                    
                    # Check for data content
                    if 'data' in result:
                        data = result['data']
                        if isinstance(data, list):
                            print(f"   📊 Data: {len(data)} items")
                        elif isinstance(data, dict):
                            print(f"   📊 Data: object with {len(data)} keys")
                
                self.test_results["direct_endpoint_tests"][endpoint_test['name']] = {
                    "endpoint": endpoint_test['endpoint'],
                    "status": "success",
                    "response_time_ms": round((end_time - start_time) * 1000),
                    "response_keys": keys if isinstance(result, dict) else None,
                    "has_data": 'data' in result if isinstance(result, dict) else False
                }
            else:
                print(f"   ❌ Failed: No response")
                self.test_results["direct_endpoint_tests"][endpoint_test['name']] = {
                    "endpoint": endpoint_test['endpoint'],
                    "status": "failed",
                    "error": "No response"
                }
                
        except Exception as e:
            end_time = time.time()
            error_msg = str(e)
            print(f"   ❌ Error: {error_msg}")
            
            # Check if it's a specific error type
            if "401" in error_msg:
                print(f"   🔐 Authentication issue")
            elif "404" in error_msg:
                print(f"   🚫 Endpoint not found")
            elif "403" in error_msg:
                print(f"   🚫 Access forbidden (package limitation)")
            elif "429" in error_msg:
                print(f"   ⏰ Rate limit hit")
            
            self.test_results["direct_endpoint_tests"][endpoint_test['name']] = {
                "endpoint": endpoint_test['endpoint'],
                "status": "error",
                "error": error_msg,
                "response_time_ms": round((end_time - start_time) * 1000)
            }
        
        # Rate limiting delay
        await asyncio.sleep(1)
    
    async def _test_method_implementation(self, api: BirdeyeAPI, method_test: Dict):
        """Test method implementation."""
        print(f"🧪 Testing {method_test['name']} method...")
        start_time = time.time()
        
        try:
            method = getattr(api, method_test['method'])
            result = await method(**method_test['params'])
            end_time = time.time()
            
            if result:
                print(f"   ✅ Success: {method_test['method']}")
                print(f"   ⏱️  Response time: {(end_time - start_time)*1000:.0f}ms")
                
                # Analyze response
                if isinstance(result, list):
                    print(f"   📊 Data: {len(result)} items")
                elif isinstance(result, dict):
                    print(f"   📊 Data: object with {len(result)} keys")
                
                self.test_results["method_tests"][method_test['name']] = {
                    "method": method_test['method'],
                    "status": "success",
                    "response_time_ms": round((end_time - start_time) * 1000),
                    "data_type": type(result).__name__,
                    "data_size": len(result) if isinstance(result, (list, dict)) else None
                }
            else:
                print(f"   ❌ Failed: No response")
                self.test_results["method_tests"][method_test['name']] = {
                    "method": method_test['method'],
                    "status": "failed",
                    "error": "No response"
                }
                
        except Exception as e:
            end_time = time.time()
            error_msg = str(e)
            print(f"   ❌ Error: {error_msg}")
            
            self.test_results["method_tests"][method_test['name']] = {
                "method": method_test['method'],
                "status": "error",
                "error": error_msg,
                "response_time_ms": round((end_time - start_time) * 1000)
            }
        
        # Rate limiting delay
        await asyncio.sleep(1)
    
    def _generate_summary(self):
        """Generate test summary."""
        direct_success = len([t for t in self.test_results["direct_endpoint_tests"].values() if t.get("status") == "success"])
        direct_total = len(self.test_results["direct_endpoint_tests"])
        
        method_success = len([t for t in self.test_results["method_tests"].values() if t.get("status") == "success"])
        method_total = len(self.test_results["method_tests"])
        
        self.test_results["summary"] = {
            "direct_endpoints": {
                "total": direct_total,
                "successful": direct_success,
                "success_rate": round(direct_success / direct_total * 100, 1) if direct_total > 0 else 0
            },
            "method_implementations": {
                "total": method_total,
                "successful": method_success,
                "success_rate": round(method_success / method_total * 100, 1) if method_total > 0 else 0
            }
        }
        
        print("\\n📊 TEST SUMMARY:")
        print(f"Direct Endpoints: {direct_success}/{direct_total} working ({self.test_results['summary']['direct_endpoints']['success_rate']}%)")
        print(f"Method Implementations: {method_success}/{method_total} working ({self.test_results['summary']['method_implementations']['success_rate']}%)")
    
    def _save_results(self):
        """Save test results to file."""
        results_dir = Path("scripts/results")
        results_dir.mkdir(exist_ok=True)
        
        filename = f"direct_endpoint_test_{int(time.time())}.json"
        filepath = results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.test_results, f, indent=2)


async def main():
    """Run the direct endpoint access test."""
    test = DirectEndpointTest()
    await test.run_direct_endpoint_test()


if __name__ == "__main__":
    asyncio.run(main()) 