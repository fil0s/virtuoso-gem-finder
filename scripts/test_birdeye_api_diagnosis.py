#!/usr/bin/env python3
"""
BirdEye API Diagnostic Test

This script diagnoses the Birdeye API issues causing 0 tokens to be discovered
in the High Trading Activity Strategy optimization test.

Based on the Birdeye documentation at:
https://docs.birdeye.so/reference/get-defi-v3-token-list

The endpoint is: GET https://public-api.birdeye.so/defi/v3/token/list
Maximum of 100 tokens per call.
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
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from utils.env_loader import load_environment


class BirdeyeAPIDiagnosticTest:
    """Comprehensive diagnostic test for Birdeye API issues."""
    
    def __init__(self):
        """Initialize the diagnostic test."""
        load_environment()
        
        # Load config
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        from services.logger_setup import LoggerSetup
        
        # Setup logger
        logger_setup = LoggerSetup("BirdeyeDiagnostic")
        self.logger = logger_setup.logger
        
        # Initialize cache and rate limiter
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        # Initialize BirdeyeAPI
        birdeye_config = self.config.get('BIRDEYE_API', {})
        birdeye_config['api_key'] = os.environ.get('BIRDEYE_API_KEY')
        
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        # Initialize strategy for parameter testing
        self.strategy = HighTradingActivityStrategy(logger=self.logger)
        
        print("🔬 Birdeye API Diagnostic Test")
        print("=" * 50)
        print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Testing endpoint: /defi/v3/token/list")
        print(f"📋 API Key status: {'✅ Set' if os.environ.get('BIRDEYE_API_KEY') else '❌ Not Set'}")
        print()
    
    async def run_comprehensive_diagnosis(self):
        """Run comprehensive diagnostic tests."""
        print("🚀 Starting Birdeye API Comprehensive Diagnosis")
        print("=" * 50)
        
        # Test 1: API Key and Authentication
        await self._test_api_authentication()
        
        # Test 2: Basic API Connectivity
        await self._test_basic_connectivity()
        
        # Test 3: Token List Endpoint with Different Parameters
        await self._test_token_list_parameters()
        
        # Test 4: High Trading Activity Strategy Parameters
        await self._test_strategy_parameters()
        
        # Test 5: Alternative Endpoints
        await self._test_alternative_endpoints()
        
        # Test 6: Raw HTTP Request Test
        await self._test_raw_http_request()
        
        print(f"\n🎉 Diagnostic test completed!")
    
    async def _test_api_authentication(self):
        """Test API authentication and key validation."""
        print(f"\n🔐 TEST 1: API Authentication")
        print("-" * 30)
        
        api_key = os.environ.get('BIRDEYE_API_KEY')
        if not api_key:
            print("❌ CRITICAL: No API key found!")
            print("   Set BIRDEYE_API_KEY environment variable")
            return False
        
        # Mask API key for security
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***MASKED***"
        print(f"🔑 API Key: {masked_key}")
        print(f"📏 Key length: {len(api_key)} characters")
        
        # Test with a simple endpoint
        try:
            # Test with supported networks endpoint (should always work)
            response = await self.birdeye_api._make_request("/defi/supported_networks")
            if response:
                print("✅ API Authentication: SUCCESS")
                print(f"   Response type: {type(response)}")
                if isinstance(response, dict):
                    print(f"   Response keys: {list(response.keys())}")
                return True
            else:
                print("❌ API Authentication: FAILED - No response")
                return False
        except Exception as e:
            print(f"❌ API Authentication: FAILED - {e}")
            return False
    
    async def _test_basic_connectivity(self):
        """Test basic API connectivity."""
        print(f"\n🌐 TEST 2: Basic API Connectivity")
        print("-" * 30)
        
        try:
            # Test the base URL
            base_url = self.birdeye_api.base_url
            print(f"🔗 Base URL: {base_url}")
            
            # Test a simple endpoint
            response = await self.birdeye_api._make_request("/defi/supported_networks")
            if response and isinstance(response, dict):
                print("✅ Basic connectivity: SUCCESS")
                
                # Check if we get network data
                if 'data' in response:
                    networks = response['data']
                    print(f"   Supported networks: {len(networks) if isinstance(networks, list) else 'N/A'}")
                    if isinstance(networks, list) and networks:
                        print(f"   Sample networks: {[n.get('name', 'Unknown') for n in networks[:3]]}")
                return True
            else:
                print("❌ Basic connectivity: FAILED - Invalid response")
                return False
        except Exception as e:
            print(f"❌ Basic connectivity: FAILED - {e}")
            return False
    
    async def _test_token_list_parameters(self):
        """Test token list endpoint with different parameter combinations."""
        print(f"\n📋 TEST 3: Token List Endpoint Parameters")
        print("-" * 30)
        
        # Test configurations from simple to complex
        test_configs = [
            {
                "name": "Minimal Parameters",
                "params": {
                    "sort_by": "volume_24h_usd",
                    "sort_type": "desc",
                    "limit": 10
                }
            },
            {
                "name": "Basic Filtering",
                "params": {
                    "sort_by": "volume_24h_usd", 
                    "sort_type": "desc",
                    "min_liquidity": 100000,
                    "limit": 10
                }
            },
            {
                "name": "High Trading Activity (Original)",
                "params": {
                    "sort_by": "trade_24h_count",
                    "sort_type": "desc",
                    "min_liquidity": 150000,
                    "min_volume_24h_usd": 75000,
                    "min_holder": 400,
                    "limit": 30
                }
            },
            {
                "name": "Relaxed High Trading Activity",
                "params": {
                    "sort_by": "trade_24h_count",
                    "sort_type": "desc",
                    "min_liquidity": 50000,
                    "min_volume_24h_usd": 25000,
                    "limit": 20
                }
            }
        ]
        
        for config in test_configs:
            print(f"\n🧪 Testing: {config['name']}")
            print(f"   Parameters: {config['params']}")
            
            try:
                result = await self.birdeye_api.get_token_list(**config['params'])
                
                if result:
                    print(f"   ✅ SUCCESS: Response received")
                    print(f"   📊 Response type: {type(result)}")
                    
                    if isinstance(result, dict):
                        print(f"   🔑 Response keys: {list(result.keys())}")
                        
                        # Check for success field
                        if 'success' in result:
                            print(f"   ✅ Success field: {result['success']}")
                        
                        # Check for data field
                        if 'data' in result:
                            data = result['data']
                            print(f"   📊 Data type: {type(data)}")
                            
                            if isinstance(data, dict):
                                print(f"   🔑 Data keys: {list(data.keys())}")
                                
                                # Check for tokens
                                if 'tokens' in data:
                                    tokens = data['tokens']
                                    print(f"   🪙 Tokens found: {len(tokens) if isinstance(tokens, list) else 'N/A'}")
                                    
                                    if isinstance(tokens, list) and tokens:
                                        sample_token = tokens[0]
                                        print(f"   📝 Sample token keys: {list(sample_token.keys()) if isinstance(sample_token, dict) else 'N/A'}")
                                        if isinstance(sample_token, dict):
                                            print(f"   🏷️  Sample symbol: {sample_token.get('symbol', 'N/A')}")
                                            print(f"   💰 Sample market cap: {sample_token.get('marketCap', 'N/A')}")
                                else:
                                    print(f"   ⚠️  No 'tokens' field in data")
                            elif isinstance(data, list):
                                print(f"   🪙 Direct token list: {len(data)} tokens")
                        else:
                            print(f"   ⚠️  No 'data' field in response")
                else:
                    print(f"   ❌ FAILED: No response")
                    
            except Exception as e:
                print(f"   ❌ FAILED: {e}")
            
            # Small delay between tests
            await asyncio.sleep(1)
    
    async def _test_strategy_parameters(self):
        """Test the exact parameters used by High Trading Activity Strategy."""
        print(f"\n🎯 TEST 4: High Trading Activity Strategy Parameters")
        print("-" * 30)
        
        # Get the exact parameters from the strategy
        strategy_params = self.strategy.api_parameters.copy()
        print(f"📋 Strategy parameters: {strategy_params}")
        
        try:
            # Test using the strategy's execute method
            print(f"\n🧪 Testing strategy execution...")
            tokens = await self.strategy.execute(self.birdeye_api)
            
            print(f"✅ Strategy execution completed")
            print(f"🪙 Tokens discovered: {len(tokens)}")
            
            if tokens:
                sample_token = tokens[0]
                print(f"📝 Sample token: {sample_token.get('symbol', 'N/A')} - {sample_token.get('address', 'N/A')}")
            else:
                print(f"⚠️  No tokens discovered - investigating...")
                
                # Test the raw API call
                result = await self.birdeye_api.get_token_list(**strategy_params)
                print(f"📊 Raw API result: {type(result)}")
                
                if result:
                    print(f"🔍 Raw result structure: {json.dumps(result, indent=2)[:500]}...")
                
        except Exception as e:
            print(f"❌ Strategy test failed: {e}")
    
    async def _test_alternative_endpoints(self):
        """Test alternative endpoints that might work better."""
        print(f"\n🔄 TEST 5: Alternative Endpoints")
        print("-" * 30)
        
        # Test the scroll endpoint
        print(f"\n🧪 Testing /defi/v3/token/list/scroll endpoint...")
        try:
            scroll_response = await self.birdeye_api._make_request("/defi/v3/token/list/scroll", params={
                "sort_by": "volume_24h_usd",
                "sort_type": "desc",
                "limit": 10
            })
            
            if scroll_response:
                print(f"✅ Scroll endpoint: SUCCESS")
                print(f"📊 Response type: {type(scroll_response)}")
                if isinstance(scroll_response, dict):
                    print(f"🔑 Response keys: {list(scroll_response.keys())}")
            else:
                print(f"❌ Scroll endpoint: No response")
                
        except Exception as e:
            print(f"❌ Scroll endpoint failed: {e}")
        
        # Test the V1 endpoint
        print(f"\n🧪 Testing /defi/tokenlist endpoint...")
        try:
            v1_response = await self.birdeye_api._make_request("/defi/tokenlist", params={
                "sort_by": "v24hUSD",
                "sort_type": "desc",
                "limit": 10
            })
            
            if v1_response:
                print(f"✅ V1 endpoint: SUCCESS")
                print(f"📊 Response type: {type(v1_response)}")
                if isinstance(v1_response, dict):
                    print(f"🔑 Response keys: {list(v1_response.keys())}")
            else:
                print(f"❌ V1 endpoint: No response")
                
        except Exception as e:
            print(f"❌ V1 endpoint failed: {e}")
    
    async def _test_raw_http_request(self):
        """Test raw HTTP request to isolate issues."""
        print(f"\n🔧 TEST 6: Raw HTTP Request")
        print("-" * 30)
        
        import aiohttp
        
        api_key = os.environ.get('BIRDEYE_API_KEY')
        if not api_key:
            print("❌ No API key for raw test")
            return
        
        url = "https://public-api.birdeye.so/defi/v3/token/list"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        params = {
            "sort_by": "volume_24h_usd",
            "sort_type": "desc", 
            "limit": 5
        }
        
        print(f"🔗 URL: {url}")
        print(f"📋 Headers: {{'X-API-KEY': '***MASKED***', 'Content-Type': 'application/json'}}")
        print(f"📊 Params: {params}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"📊 Status Code: {response.status}")
                    print(f"📋 Response Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            print(f"✅ Raw HTTP: SUCCESS")
                            print(f"📊 Response type: {type(data)}")
                            if isinstance(data, dict):
                                print(f"🔑 Response keys: {list(data.keys())}")
                                print(f"🔍 Response preview: {json.dumps(data, indent=2)[:300]}...")
                        except Exception as json_error:
                            text = await response.text()
                            print(f"❌ JSON parsing failed: {json_error}")
                            print(f"📝 Raw text: {text[:200]}...")
                    else:
                        text = await response.text()
                        print(f"❌ HTTP Error {response.status}: {text[:200]}...")
                        
        except Exception as e:
            print(f"❌ Raw HTTP request failed: {e}")
    
    async def close(self):
        """Clean up resources."""
        if hasattr(self.birdeye_api, 'close'):
            await self.birdeye_api.close()


async def main():
    """Run the Birdeye API diagnostic test."""
    test = BirdeyeAPIDiagnosticTest()
    try:
        await test.run_comprehensive_diagnosis()
    finally:
        await test.close()


if __name__ == "__main__":
    asyncio.run(main()) 