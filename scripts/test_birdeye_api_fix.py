#!/usr/bin/env python3
"""
Test the Birdeye API fix with V1 fallback functionality.

This script tests:
1. V1 fallback when V3 access is restricted
2. Response standardization
3. High Trading Activity Strategy with fixed API
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import yaml

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from utils.env_loader import load_environment


class BirdeyeAPIFixTest:
    """Test the Birdeye API fix with V1 fallback."""
    
    def __init__(self):
        """Initialize the test."""
        load_environment()
        
        # Load config
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        from services.logger_setup import LoggerSetup
        
        # Setup logger
        logger_setup = LoggerSetup("BirdeyeAPIFix")
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
        
        # Initialize strategy
        self.strategy = HighTradingActivityStrategy(logger=self.logger)
        
        print("🔧 Birdeye API Fix Test")
        print("=" * 50)
        print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔑 API Key status: {'✅ Set' if os.environ.get('BIRDEYE_API_KEY') else '❌ Not Set'}")
        print()
    
    async def run_fix_tests(self):
        """Run comprehensive fix tests."""
        print("🚀 Testing Birdeye API Fix with V1 Fallback")
        print("=" * 50)
        
        # Test 1: Direct API fallback functionality
        await self._test_api_fallback()
        
        # Test 2: Response standardization
        await self._test_response_standardization()
        
        # Test 3: High Trading Activity Strategy
        await self._test_strategy_execution()
        
        # Test 4: Compare V1 vs V3 data quality
        await self._test_data_quality_comparison()
        
        print(f"\n🎉 API fix test completed!")
    
    async def _test_api_fallback(self):
        """Test the automatic V1 fallback functionality."""
        print(f"\n🔄 TEST 1: API Fallback Functionality")
        print("-" * 30)
        
        try:
            # Test with High Trading Activity parameters
            result = await self.birdeye_api.get_token_list(
                sort_by="trade_24h_count",
                sort_type="desc",
                min_liquidity=150000,
                min_volume_24h_usd=75000,
                min_holder=400,
                limit=10
            )
            
            if result:
                print("✅ API fallback: SUCCESS")
                print(f"📊 Response type: {type(result)}")
                print(f"🔑 Response keys: {list(result.keys())}")
                
                if result.get("success"):
                    data = result.get("data", {})
                    tokens = data.get("tokens", [])
                    endpoint_used = data.get("endpoint_used", "unknown")
                    
                    print(f"✅ Success: {result['success']}")
                    print(f"🪙 Tokens found: {len(tokens)}")
                    print(f"🔗 Endpoint used: {endpoint_used}")
                    
                    if tokens:
                        sample_token = tokens[0]
                        print(f"📝 Sample token: {sample_token.get('symbol', 'N/A')} - {sample_token.get('name', 'N/A')}")
                        print(f"💰 Market cap: ${sample_token.get('market_cap', 0):,.0f}")
                        print(f"📊 24h volume: ${sample_token.get('volume_24h_usd', 0):,.0f}")
                        print(f"🔢 24h trades: {sample_token.get('trade_24h_count', 0):,}")
                else:
                    print(f"❌ API returned unsuccessful response")
            else:
                print(f"❌ No response from API")
                
        except Exception as e:
            print(f"❌ API fallback test failed: {e}")
    
    async def _test_response_standardization(self):
        """Test response standardization between V1 and V3 formats."""
        print(f"\n📋 TEST 2: Response Standardization")
        print("-" * 30)
        
        try:
            # Test with simpler parameters to ensure we get data
            result = await self.birdeye_api.get_token_list(
                sort_by="volume_24h_usd",
                sort_type="desc",
                limit=5
            )
            
            if result and result.get("success"):
                data = result.get("data", {})
                tokens = data.get("tokens", [])
                
                print("✅ Response standardization: SUCCESS")
                print(f"📊 Standardized format confirmed")
                print(f"🪙 Tokens: {len(tokens)}")
                print(f"🔗 Endpoint: {data.get('endpoint_used', 'unknown')}")
                
                # Verify expected fields are present
                if tokens:
                    token = tokens[0]
                    expected_fields = ['address', 'symbol', 'name', 'market_cap', 'volume_24h_usd']
                    present_fields = [field for field in expected_fields if field in token]
                    
                    print(f"📝 Expected fields present: {len(present_fields)}/{len(expected_fields)}")
                    print(f"   Fields: {present_fields}")
                    
                    if len(present_fields) >= 3:
                        print("✅ Response format is compatible with strategies")
                    else:
                        print("⚠️  Response format may need additional mapping")
            else:
                print("❌ Response standardization failed")
                
        except Exception as e:
            print(f"❌ Response standardization test failed: {e}")
    
    async def _test_strategy_execution(self):
        """Test High Trading Activity Strategy execution with fixed API."""
        print(f"\n🎯 TEST 3: High Trading Activity Strategy Execution")
        print("-" * 30)
        
        try:
            # Execute the strategy
            print("🧪 Executing High Trading Activity Strategy...")
            tokens = await self.strategy.execute(self.birdeye_api)
            
            print(f"✅ Strategy execution: SUCCESS")
            print(f"🪙 Tokens discovered: {len(tokens)}")
            
            if tokens:
                print("🎯 Top discovered tokens:")
                for i, token in enumerate(tokens[:3]):
                    symbol = token.get('symbol', 'N/A')
                    name = token.get('name', 'N/A')
                    address = token.get('address', 'N/A')
                    market_cap = token.get('market_cap', 0)
                    volume = token.get('volume_24h_usd', 0)
                    trades = token.get('trade_24h_count', 0)
                    
                    print(f"   {i+1}. {symbol} ({name})")
                    print(f"      Address: {address[:8]}...{address[-8:] if len(address) > 16 else address}")
                    print(f"      Market Cap: ${market_cap:,.0f}")
                    print(f"      24h Volume: ${volume:,.0f}")
                    print(f"      24h Trades: {trades:,}")
                    print()
                
                # Verify tokens meet strategy criteria
                strategy_params = self.strategy.api_parameters
                min_liquidity = strategy_params.get('min_liquidity', 0)
                min_volume = strategy_params.get('min_volume_24h_usd', 0)
                min_holders = strategy_params.get('min_holder', 0)
                
                print(f"📋 Strategy criteria verification:")
                print(f"   Min liquidity: ${min_liquidity:,}")
                print(f"   Min volume: ${min_volume:,}")
                print(f"   Min holders: {min_holders:,}")
                
                qualifying_tokens = 0
                for token in tokens:
                    liquidity = token.get('liquidity', 0)
                    volume = token.get('volume_24h_usd', 0)
                    holders = token.get('holder', 0)
                    
                    if (liquidity >= min_liquidity and 
                        volume >= min_volume and 
                        holders >= min_holders):
                        qualifying_tokens += 1
                
                print(f"✅ Tokens meeting criteria: {qualifying_tokens}/{len(tokens)}")
                
            else:
                print("⚠️  No tokens discovered - may need to relax criteria")
                
        except Exception as e:
            print(f"❌ Strategy execution test failed: {e}")
    
    async def _test_data_quality_comparison(self):
        """Compare data quality between V1 and direct endpoint calls."""
        print(f"\n📊 TEST 4: Data Quality Comparison")
        print("-" * 30)
        
        try:
            # Test V1 endpoint directly
            print("🧪 Testing V1 endpoint directly...")
            v1_response = await self.birdeye_api._make_request("/defi/tokenlist", params={
                "sort_by": "v24hUSD",
                "sort_type": "desc",
                "limit": 5
            })
            
            if v1_response and v1_response.get("success"):
                v1_tokens = v1_response.get("data", {}).get("tokens", [])
                print(f"✅ V1 endpoint: {len(v1_tokens)} tokens")
                
                if v1_tokens:
                    v1_token = v1_tokens[0]
                    print(f"📝 V1 sample token fields: {list(v1_token.keys())}")
            else:
                print("❌ V1 endpoint failed")
            
            # Test standardized response
            print("\n🧪 Testing standardized response...")
            std_response = await self.birdeye_api.get_token_list(
                sort_by="volume_24h_usd",
                sort_type="desc",
                limit=5
            )
            
            if std_response and std_response.get("success"):
                std_tokens = std_response.get("data", {}).get("tokens", [])
                endpoint_used = std_response.get("data", {}).get("endpoint_used", "unknown")
                print(f"✅ Standardized response: {len(std_tokens)} tokens (using {endpoint_used})")
                
                if std_tokens:
                    std_token = std_tokens[0]
                    print(f"📝 Standardized token fields: {list(std_token.keys())}")
                    
                    # Compare field availability
                    if v1_tokens and std_tokens:
                        v1_fields = set(v1_tokens[0].keys())
                        std_fields = set(std_tokens[0].keys())
                        
                        common_fields = v1_fields.intersection(std_fields)
                        print(f"🔗 Common fields: {len(common_fields)}")
                        print(f"   Fields: {sorted(list(common_fields))}")
                        
                        if len(common_fields) >= 5:
                            print("✅ Good field compatibility between formats")
                        else:
                            print("⚠️  Limited field compatibility")
            else:
                print("❌ Standardized response failed")
                
        except Exception as e:
            print(f"❌ Data quality comparison failed: {e}")
    
    async def close(self):
        """Clean up resources."""
        if hasattr(self.birdeye_api, 'close'):
            await self.birdeye_api.close()


async def main():
    """Run the Birdeye API fix test."""
    test = BirdeyeAPIFixTest()
    try:
        await test.run_fix_tests()
    finally:
        await test.close()


if __name__ == "__main__":
    asyncio.run(main()) 