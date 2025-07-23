#!/usr/bin/env python3
"""
Comprehensive Birdeye API Endpoints Test Suite

This script provides a thorough test of ALL Birdeye API endpoints used throughout the system.
It validates input parameters, response handling, error conditions, and critical issues.

Purpose:
- Test endpoint connectivity and authentication
- Validate request parameter handling
- Check response parsing and data extraction
- Identify critical errors and warnings
- Performance monitoring
- Rate limiting compliance 
"""

import asyncio
import logging
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup

@dataclass
class EndpointTestResult:
    """Test result for a single endpoint"""
    endpoint_name: str
    endpoint_path: str
    method_name: str
    status: str  # PASS, FAIL, WARNING, SKIP
    response_time_ms: float
    status_code: Optional[int]
    response_data_type: str
    response_data_size: int
    input_parameters: Dict[str, Any]
    error_message: Optional[str]
    critical_issues: List[str]
    warnings: List[str]
    data_validation: Dict[str, bool]
    timestamp: datetime

@dataclass 
class EndpointDefinition:
    """Definition of a Birdeye endpoint for testing"""
    name: str
    path: str
    method_name: str
    method_ref: Callable
    test_params: List[Dict[str, Any]]
    expected_response_type: str
    required_fields: List[str]
    optional_fields: List[str]
    rate_limit_group: str
    description: str

class ComprehensiveBirdeyeEndpointTester:
    """Comprehensive tester for ALL Birdeye API endpoints"""
    
    def __init__(self):
        # Setup logging
        self.logger_setup = LoggerSetup('ComprehensiveBirdeyeTest', log_level='INFO')
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
        
        # Test data - using well-known tokens and wallets
        self.test_tokens = {
            'SOL': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
            'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'BONK': '85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ',   # BONK
            'PUMP': '4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg'    # Popular pump token
        }
        
        self.test_wallets = [
            '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',  # Known active wallet
            '3XLkRVg69AgwKAbnSjJpm3PB4QgVeXFEjiXfw5shWMBT',   # Another active wallet
            'HXbkqrNqMjDsku4J5v7Wzks4Uz9NooNZQDWQ3MkLrTZD'    # High volume wallet
        ]
        
        # Results tracking
        self.test_results: List[EndpointTestResult] = []
        self.endpoint_definitions = self._define_all_endpoints()
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warning_tests = 0
        self.skipped_tests = 0
        self.critical_issues = []
        self.all_warnings = []
        
    def _define_all_endpoints(self) -> List[EndpointDefinition]:
        """Define all Birdeye endpoints used in the system with test parameters"""
        endpoints = []
        
        # TOKEN DATA ENDPOINTS
        endpoints.extend([
            EndpointDefinition(
                name="get_token_overview",
                path="/defi/token_overview",
                method_name="get_token_overview",
                method_ref=self.birdeye_api.get_token_overview,
                test_params=[
                    {"token_address": self.test_tokens['SOL']},
                    {"token_address": self.test_tokens['BONK']},
                    {"token_address": self.test_tokens['USDC']},
                    {"token_address": "invalid_address"},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["price", "symbol", "address"],
                optional_fields=["liquidity", "volume", "marketCap", "holders"],
                rate_limit_group="birdeye",
                description="Get comprehensive token information"
            ),
            
            EndpointDefinition(
                name="get_token_creation_info",
                path="/defi/token_creation_info", 
                method_name="get_token_creation_info",
                method_ref=self.birdeye_api.get_token_creation_info,
                test_params=[
                    {"token_address": self.test_tokens['BONK']},
                    {"token_address": self.test_tokens['PUMP']},
                    {"token_address": "invalid_address"},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["creator", "blockTime"],
                optional_fields=["transactionHash", "createdTime"],
                rate_limit_group="birdeye",
                description="Get token creation information"
            ),
            
            EndpointDefinition(
                name="get_token_holders",
                path="/defi/v3/token/holder",
                method_name="get_token_holders", 
                method_ref=self.birdeye_api.get_token_holders,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "limit": 10},
                    {"token_address": self.test_tokens['BONK'], "offset": 0, "limit": 20},
                    {"token_address": self.test_tokens['USDC'], "limit": 50},
                    {"token_address": "invalid_address", "limit": 10},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["items", "total"],
                optional_fields=["hasNext", "hasPrev"],
                rate_limit_group="birdeye",
                description="Get token holder distribution"
            ),
            
            EndpointDefinition(
                name="get_token_security",
                path="/defi/token_security",
                method_name="get_token_security",
                method_ref=self.birdeye_api.get_token_security,
                test_params=[
                    {"token_address": self.test_tokens['USDC']},  # Should be secure
                    {"token_address": self.test_tokens['BONK']},
                    {"token_address": self.test_tokens['PUMP']},
                    {"token_address": "invalid_address"},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["is_scam", "is_risky"],
                optional_fields=["risk_score", "security_score"],
                rate_limit_group="birdeye",
                description="Get token security analysis"
            ),
        ])
        
        # PRICE DATA ENDPOINTS
        endpoints.extend([
            EndpointDefinition(
                name="get_historical_price_at_timestamp",
                path="/defi/historical_price_unix",
                method_name="get_historical_price_at_timestamp",
                method_ref=self.birdeye_api.get_historical_price_at_timestamp,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "unix_timestamp": int(time.time()) - 86400},
                    {"token_address": self.test_tokens['BONK'], "unix_timestamp": int(time.time()) - 3600},
                    {"token_address": "invalid_address", "unix_timestamp": int(time.time())},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["price", "timestamp"],
                optional_fields=["priceChange", "volume"],
                rate_limit_group="birdeye",
                description="Get historical price at specific timestamp"
            ),
            
            EndpointDefinition(
                name="get_multi_price",
                path="/defi/multi_price",
                method_name="get_multi_price",
                method_ref=self.birdeye_api.get_multi_price,
                test_params=[
                    {"addresses": [self.test_tokens['SOL']], "include_liquidity": True},
                    {"addresses": [self.test_tokens['SOL'], self.test_tokens['USDC']], "include_liquidity": False},
                    {"addresses": list(self.test_tokens.values())[:3], "include_liquidity": True},
                    {"addresses": ["invalid_address"], "include_liquidity": True},  # Error case
                ],
                expected_response_type="dict",
                required_fields=[],  # Keys are token addresses
                optional_fields=["liquidity", "price"],
                rate_limit_group="birdeye",
                description="Get prices for multiple tokens"
            ),
            
            EndpointDefinition(
                name="get_ohlcv_data",
                path="/defi/v3/ohlcv",
                method_name="get_ohlcv_data",
                method_ref=self.birdeye_api.get_ohlcv_data,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "time_frame": "1h", "limit": 24},
                    {"token_address": self.test_tokens['BONK'], "time_frame": "5m", "limit": 12},
                    {"token_address": self.test_tokens['USDC'], "time_frame": "1d", "limit": 7},
                    {"token_address": "invalid_address", "time_frame": "1h", "limit": 10},  # Error case
                ],
                expected_response_type="list",
                required_fields=["open", "high", "low", "close", "volume"],
                optional_fields=["timestamp", "trades"],
                rate_limit_group="birdeye",
                description="Get OHLCV candle data"
            ),
        ])
        
        # TRADING DATA ENDPOINTS  
        endpoints.extend([
            EndpointDefinition(
                name="get_token_transactions",
                path="/defi/txs/token",
                method_name="get_token_transactions",
                method_ref=self.birdeye_api.get_token_transactions,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "limit": 10, "sort_type": "desc"},
                    {"token_address": self.test_tokens['BONK'], "limit": 20, "max_pages": 2},
                    {"token_address": self.test_tokens['PUMP'], "limit": 15, "sort_type": "asc"},
                    {"token_address": "invalid_address", "limit": 10},  # Error case
                ],
                expected_response_type="list",
                required_fields=["time", "side"],
                optional_fields=["volume", "price", "owner", "txHash"],
                rate_limit_group="birdeye",
                description="Get token transaction history"
            ),
            
            EndpointDefinition(
                name="get_top_traders",
                path="/defi/v2/tokens/top_traders",
                method_name="get_top_traders",
                method_ref=self.birdeye_api.get_top_traders,
                test_params=[
                    {"token_address": self.test_tokens['SOL']},
                    {"token_address": self.test_tokens['BONK']},
                    {"token_address": self.test_tokens['PUMP']},
                    {"token_address": "invalid_address"},  # Error case
                ],
                expected_response_type="list",
                required_fields=["address"],
                optional_fields=["volume", "trades", "pnl"],
                rate_limit_group="birdeye",
                description="Get top traders for token"
            ),
            
            EndpointDefinition(
                name="get_top_traders_optimized",
                path="/defi/v2/tokens/top_traders",
                method_name="get_top_traders_optimized",
                method_ref=self.birdeye_api.get_top_traders_optimized,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "time_frame": "24h", "sort_by": "volume", "limit": 10},
                    {"token_address": self.test_tokens['BONK'], "time_frame": "1h", "sort_by": "trade", "limit": 5},
                    {"token_address": self.test_tokens['PUMP'], "time_frame": "12h", "sort_by": "volume", "limit": 15},
                    {"token_address": "invalid_address", "time_frame": "24h", "sort_by": "volume", "limit": 10},  # Error case
                ],
                expected_response_type="list",
                required_fields=["address"],
                optional_fields=["volume", "trades", "query_timeframe"],
                rate_limit_group="birdeye",
                description="Get optimized top traders with parameters"
            ),
        ])
        
        # WALLET ENDPOINTS
        endpoints.extend([
            EndpointDefinition(
                name="get_wallet_transaction_history",
                path="/v1/wallet/tx_list",
                method_name="get_wallet_transaction_history",
                method_ref=self.birdeye_api.get_wallet_transaction_history,
                test_params=[
                    {"wallet_address": self.test_wallets[0], "chain": "solana", "limit": 10},
                    {"wallet_address": self.test_wallets[1], "chain": "solana", "offset": 0, "limit": 20},
                    {"wallet_address": "invalid_wallet", "chain": "solana", "limit": 10},  # Error case
                ],
                expected_response_type="list",
                required_fields=["txHash", "time"],
                optional_fields=["status", "mainAction", "side"],
                rate_limit_group="birdeye_wallet",
                description="Get wallet transaction history"
            ),
            
            EndpointDefinition(
                name="get_wallet_portfolio",
                path="/v1/wallet/token_list",
                method_name="get_wallet_portfolio",
                method_ref=self.birdeye_api.get_wallet_portfolio,
                test_params=[
                    {"wallet_address": self.test_wallets[0], "chain": "solana"},
                    {"wallet_address": self.test_wallets[1], "chain": "solana"},
                    {"wallet_address": "invalid_wallet", "chain": "solana"},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["wallet", "totalUsd"],
                optional_fields=["items", "tokensCount"],
                rate_limit_group="birdeye_wallet",
                description="Get wallet token portfolio"
            ),
            
            EndpointDefinition(
                name="get_trader_gainers_losers",
                path="/defi/v2/trader_gainers_losers",
                method_name="get_trader_gainers_losers",
                method_ref=self.birdeye_api.get_trader_gainers_losers,
                test_params=[
                    {"timeframe": "24h", "sort_by": "pnl", "limit": 10},
                    {"timeframe": "1h", "sort_by": "volume", "limit": 20, "offset": 10},
                    {"timeframe": "7d", "sort_by": "pnl", "limit": 5},
                ],
                expected_response_type="list",
                required_fields=["address"],
                optional_fields=["pnl", "volume", "winRate"],
                rate_limit_group="birdeye",
                description="Get top gaining/losing traders"
            ),
        ])
        
        # DISCOVERY ENDPOINTS
        endpoints.extend([
            EndpointDefinition(
                name="get_trending_tokens",
                path="/defi/token_trending",
                method_name="get_trending_tokens",
                method_ref=self.birdeye_api.get_trending_tokens,
                test_params=[
                    {},  # No parameters
                ],
                expected_response_type="list",
                required_fields=[],  # Token addresses
                optional_fields=[],
                rate_limit_group="birdeye",
                description="Get trending token addresses"
            ),
            
            EndpointDefinition(
                name="get_new_listings",
                path="/defi/v2/tokens/new_listing",
                method_name="get_new_listings",
                method_ref=self.birdeye_api.get_new_listings,
                test_params=[
                    {},  # No parameters
                ],
                expected_response_type="list",
                required_fields=["address"],
                optional_fields=["symbol", "name", "listingTime"],
                rate_limit_group="birdeye",
                description="Get newly listed tokens"
            ),
            
            EndpointDefinition(
                name="get_gainers_losers",
                path="/defi/v2/tokens/gainers_losers",
                method_name="get_gainers_losers",
                method_ref=self.birdeye_api.get_gainers_losers,
                test_params=[
                    {"timeframe": "24h"},
                    {"timeframe": "1h"},
                    {"timeframe": "7d"},
                ],
                expected_response_type="list",
                required_fields=["address"],
                optional_fields=["priceChange", "volume", "symbol"],
                rate_limit_group="birdeye",
                description="Get top gaining/losing tokens"
            ),
            
            EndpointDefinition(
                name="get_token_list",
                path="/defi/v3/token/list",
                method_name="get_token_list",
                method_ref=self.birdeye_api.get_token_list,
                test_params=[
                    {"sort_by": "volume_24h_usd", "sort_type": "desc", "limit": 10},
                    {"sort_by": "liquidity", "sort_type": "desc", "min_liquidity": 100000, "limit": 20},
                    {"sort_by": "volume_24h_usd", "min_volume_24h_usd": 50000, "limit": 15},
                    {"sort_by": "invalid_sort", "limit": 10},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["success", "data"],
                optional_fields=["total", "hasNext"],
                rate_limit_group="birdeye",
                description="Get filtered token list"
            ),
        ])
        
        # BATCH ENDPOINTS
        endpoints.extend([
            EndpointDefinition(
                name="get_price_volume_multi",
                path="/defi/price_volume/multi",
                method_name="get_price_volume_multi",
                method_ref=self.birdeye_api.get_price_volume_multi,
                test_params=[
                    {"addresses": [self.test_tokens['SOL'], self.test_tokens['USDC']], "time_range": "24h"},
                    {"addresses": list(self.test_tokens.values())[:3], "time_range": "1h"},
                    {"addresses": ["invalid_address"], "time_range": "24h"},  # Error case
                ],
                expected_response_type="dict",
                required_fields=[],  # Keys are token addresses
                optional_fields=["price", "volume"],
                rate_limit_group="birdeye",
                description="Get price and volume for multiple tokens"
            ),
            
            EndpointDefinition(
                name="get_token_metadata_multiple",
                path="/defi/v3/token/meta-data/multiple",
                method_name="get_token_metadata_multiple",
                method_ref=self.birdeye_api.get_token_metadata_multiple,
                test_params=[
                    {"addresses": [self.test_tokens['SOL'], self.test_tokens['USDC']]},
                    {"addresses": list(self.test_tokens.values())[:3]},
                    {"addresses": ["invalid_address"]},  # Error case
                ],
                expected_response_type="dict",
                required_fields=[],  # Keys are token addresses
                optional_fields=["symbol", "name", "decimals"],
                rate_limit_group="birdeye",
                description="Get metadata for multiple tokens"
            ),
        ])
        
        # ANALYTICS ENDPOINTS
        endpoints.extend([
            EndpointDefinition(
                name="get_token_transaction_volume",
                path="/defi/txs/token",  # Derived from transactions
                method_name="get_token_transaction_volume",
                method_ref=self.birdeye_api.get_token_transaction_volume,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "limit": 20, "max_pages": 2},
                    {"token_address": self.test_tokens['BONK'], "limit": 30, "max_pages": 1},
                    {"token_address": "invalid_address", "limit": 10},  # Error case
                ],
                expected_response_type="float",
                required_fields=[],  # Single float value
                optional_fields=[],
                rate_limit_group="birdeye", 
                description="Calculate token trading volume from transactions"
            ),
            
            EndpointDefinition(
                name="detect_smart_money_activity",
                path="/defi/txs/token",  # Derived from transactions
                method_name="detect_smart_money_activity",
                method_ref=self.birdeye_api.detect_smart_money_activity,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "max_pages": 2},
                    {"token_address": self.test_tokens['BONK'], "max_pages": 1},
                    {"token_address": "invalid_address", "max_pages": 1},  # Error case
                ],
                expected_response_type="dict",
                required_fields=["has_smart_money", "smart_money_wallets"],
                optional_fields=["smart_money_buy_count", "total_smart_money_volume_usd"],
                rate_limit_group="birdeye",
                description="Detect smart money wallet activity"
            ),
            
            EndpointDefinition(
                name="get_historical_trade_data",
                path="/defi/txs/token",  # Multi-interval analysis
                method_name="get_historical_trade_data",
                method_ref=self.birdeye_api.get_historical_trade_data,
                test_params=[
                    {"token_address": self.test_tokens['SOL'], "time_intervals": [3600, 86400], "limit": 20},
                    {"token_address": self.test_tokens['BONK'], "time_intervals": [300, 1800], "limit": 15},
                    {"token_address": "invalid_address", "time_intervals": [3600], "limit": 10},  # Error case
                ],
                expected_response_type="dict",
                required_fields=[],  # Keys are interval values
                optional_fields=[],
                rate_limit_group="birdeye",
                description="Get historical trade data across time intervals"
            ),
        ])
        
        return endpoints
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all endpoints"""
        self.logger.info("=" * 100)
        self.logger.info("🔍 STARTING COMPREHENSIVE BIRDEYE API ENDPOINTS TEST SUITE")
        self.logger.info("=" * 100)
        
        start_time = time.time()
        
        # Display test overview
        self.logger.info(f"📊 Test Overview:")
        self.logger.info(f"   • Total Endpoints: {len(self.endpoint_definitions)}")
        self.logger.info(f"   • Total Test Cases: {sum(len(ep.test_params) for ep in self.endpoint_definitions)}")
        self.logger.info(f"   • API Base URL: {self.birdeye_api.base_url}")
        self.logger.info(f"   • API Key Status: {'✅ Set' if self.birdeye_api.api_key else '❌ Missing'}")
        self.logger.info("")
        
        # Run tests by category
        await self._test_authentication_and_connectivity()
        await self._test_all_endpoints()
        
        # Generate comprehensive summary
        elapsed_time = time.time() - start_time
        summary = await self._generate_comprehensive_summary(elapsed_time)
        
        return summary
    
    async def _test_authentication_and_connectivity(self):
        """Test basic authentication and API connectivity"""
        self.logger.info("🔐 TESTING AUTHENTICATION AND CONNECTIVITY")
        self.logger.info("-" * 60)
        
        # Test 1: API Key validation
        if not self.birdeye_api.api_key:
            self.critical_issues.append("❌ CRITICAL: No API key configured")
            self.logger.error("❌ CRITICAL: No API key configured")
        else:
            self.logger.info(f"✅ API key configured: {self.birdeye_api.api_key[:8]}...")
            
        # Test 2: Base URL connectivity
        try:
            # Simple endpoint test
            response = await self.birdeye_api.get_multi_price([self.test_tokens['SOL']])
            if response:
                self.logger.info("✅ API connectivity confirmed")
            else:
                self.critical_issues.append("❌ CRITICAL: API not responding")
                self.logger.error("❌ CRITICAL: API not responding")
        except Exception as e:
            self.critical_issues.append(f"❌ CRITICAL: API connection failed: {e}")
            self.logger.error(f"❌ CRITICAL: API connection failed: {e}")
            
        # Test 3: Rate limiting configuration
        rate_limit_config = self.rate_limiter.get_rate_limit_info("birdeye")
        self.logger.info(f"⚡ Rate Limit Config: {rate_limit_config}")
        
        self.logger.info("")
    
    async def _test_all_endpoints(self):
        """Test all defined endpoints systematically"""
        self.logger.info("🔍 TESTING ALL ENDPOINTS")
        self.logger.info("-" * 60)
        
        for endpoint_def in self.endpoint_definitions:
            self.logger.info(f"\n📍 Testing {endpoint_def.name}")
            self.logger.info(f"   Path: {endpoint_def.path}")
            self.logger.info(f"   Description: {endpoint_def.description}")
            
            # Test each parameter set for this endpoint
            for param_set in endpoint_def.test_params:
                await self._test_single_endpoint(endpoint_def, param_set)
                
                # Rate limiting compliance
                await asyncio.sleep(0.2)  # Small delay between tests
    
    async def _test_single_endpoint(self, endpoint_def: EndpointDefinition, test_params: Dict[str, Any]):
        """Test a single endpoint with specific parameters"""
        self.total_tests += 1
        start_time = time.time()
        
        result = EndpointTestResult(
            endpoint_name=endpoint_def.name,
            endpoint_path=endpoint_def.path,
            method_name=endpoint_def.method_name,
            status="UNKNOWN",
            response_time_ms=0.0,
            status_code=None,
            response_data_type="unknown",
            response_data_size=0,
            input_parameters=test_params.copy(),
            error_message=None,
            critical_issues=[],
            warnings=[],
            data_validation={},
            timestamp=datetime.now()
        )
        
        try:
            # Make the API call
            if test_params:
                response = await endpoint_def.method_ref(**test_params)
            else:
                response = await endpoint_def.method_ref()
                
            # Calculate response time
            result.response_time_ms = (time.time() - start_time) * 1000
            
            # Analyze response
            if response is None:
                result.status = "WARNING"
                result.warnings.append("Response is None")
                result.response_data_type = "NoneType"
                self.warning_tests += 1
            else:
                result.status = "PASS"
                result.response_data_type = type(response).__name__
                
                # Validate response type
                expected_type = endpoint_def.expected_response_type
                if expected_type == "dict" and not isinstance(response, dict):
                    result.warnings.append(f"Expected dict, got {type(response).__name__}")
                elif expected_type == "list" and not isinstance(response, list):
                    result.warnings.append(f"Expected list, got {type(response).__name__}")
                elif expected_type == "float" and not isinstance(response, (int, float)):
                    result.warnings.append(f"Expected float, got {type(response).__name__}")
                
                # Calculate data size
                if isinstance(response, (list, dict)):
                    result.response_data_size = len(response)
                else:
                    result.response_data_size = 1
                    
                # Validate required fields
                if isinstance(response, dict):
                    for field in endpoint_def.required_fields:
                        if field in response:
                            result.data_validation[f"has_{field}"] = True
                        else:
                            result.data_validation[f"has_{field}"] = False
                            result.warnings.append(f"Missing required field: {field}")
                            
                elif isinstance(response, list) and response:
                    # Check first item for required fields
                    first_item = response[0]
                    if isinstance(first_item, dict):
                        for field in endpoint_def.required_fields:
                            if field in first_item:
                                result.data_validation[f"has_{field}"] = True
                            else:
                                result.data_validation[f"has_{field}"] = False
                                result.warnings.append(f"Missing required field in list items: {field}")
                
                # Check for special error conditions
                if "invalid" in str(test_params) and response:
                    result.warnings.append("Expected error case but got valid response")
                    
                self.passed_tests += 1
                
        except Exception as e:
            result.status = "FAIL"
            result.error_message = str(e)
            result.response_time_ms = (time.time() - start_time) * 1000
            
            # Categorize errors
            error_str = str(e).lower()
            if "401" in error_str or "authentication" in error_str:
                result.critical_issues.append("Authentication failure")
            elif "429" in error_str or "rate limit" in error_str:
                result.critical_issues.append("Rate limit exceeded")
            elif "404" in error_str:
                result.warnings.append("Endpoint not found (404)")
            elif "timeout" in error_str:
                result.critical_issues.append("Request timeout")
            elif "connection" in error_str:
                result.critical_issues.append("Connection error")
            else:
                result.warnings.append(f"Unexpected error: {e}")
                
            self.failed_tests += 1
        
        # Log result
        status_emoji = {
            "PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "SKIP": "⏭️"
        }.get(result.status, "❓")
        
        param_str = ", ".join([f"{k}={v}" for k, v in test_params.items()]) if test_params else "no params"
        self.logger.info(f"   {status_emoji} {result.status}: {param_str} "
                        f"({result.response_time_ms:.0f}ms, {result.response_data_type}, "
                        f"{result.response_data_size} items)")
        
        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(f"      ⚠️  {warning}")
                self.all_warnings.append(f"{endpoint_def.name}: {warning}")
                
        if result.critical_issues:
            for issue in result.critical_issues:
                self.logger.error(f"      ❌ {issue}")
                self.critical_issues.append(f"{endpoint_def.name}: {issue}")
        
        # Store result
        self.test_results.append(result)
    
    async def _generate_comprehensive_summary(self, elapsed_time: float) -> Dict[str, Any]:
        """Generate comprehensive test summary with detailed analysis"""
        self.logger.info("\n" + "=" * 100)
        self.logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        self.logger.info("=" * 100)
        
        # Overall statistics
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        self.logger.info(f"📈 OVERALL RESULTS:")
        self.logger.info(f"   • Total Tests: {self.total_tests}")
        self.logger.info(f"   • Passed: {self.passed_tests}")
        self.logger.info(f"   • Failed: {self.failed_tests}")
        self.logger.info(f"   • Warnings: {self.warning_tests}")
        self.logger.info(f"   • Success Rate: {success_rate:.1f}%")
        self.logger.info(f"   • Total Time: {elapsed_time:.2f} seconds")
        
        # Critical issues summary
        if self.critical_issues:
            self.logger.info(f"\n🚨 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                self.logger.error(f"   ❌ {issue}")
        else:
            self.logger.info(f"\n✅ NO CRITICAL ISSUES FOUND")
            
        # Warnings summary
        if self.all_warnings:
            self.logger.info(f"\n⚠️  WARNINGS ({len(self.all_warnings)}):")
            for warning in self.all_warnings[:10]:  # Show first 10
                self.logger.warning(f"   ⚠️  {warning}")
            if len(self.all_warnings) > 10:
                self.logger.warning(f"   ... and {len(self.all_warnings) - 10} more warnings")
        
        # Performance analysis
        response_times = [r.response_time_ms for r in self.test_results if r.response_time_ms > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            self.logger.info(f"\n⚡ PERFORMANCE ANALYSIS:")
            self.logger.info(f"   • Average Response Time: {avg_response_time:.1f}ms")
            self.logger.info(f"   • Fastest Response: {min_response_time:.1f}ms")
            self.logger.info(f"   • Slowest Response: {max_response_time:.1f}ms")
            
            # Identify slow endpoints
            slow_endpoints = [r for r in self.test_results if r.response_time_ms > 5000]
            if slow_endpoints:
                self.logger.info(f"\n🐌 SLOW ENDPOINTS (>5s):")
                for endpoint in slow_endpoints:
                    self.logger.warning(f"   ⚠️  {endpoint.endpoint_name}: {endpoint.response_time_ms:.0f}ms")
        
        # Endpoint success rates
        endpoint_stats = {}
        for result in self.test_results:
            if result.endpoint_name not in endpoint_stats:
                endpoint_stats[result.endpoint_name] = {"total": 0, "passed": 0, "failed": 0}
            
            endpoint_stats[result.endpoint_name]["total"] += 1
            if result.status == "PASS":
                endpoint_stats[result.endpoint_name]["passed"] += 1
            elif result.status == "FAIL":
                endpoint_stats[result.endpoint_name]["failed"] += 1
        
        # Show endpoint success rates
        self.logger.info(f"\n📋 ENDPOINT SUCCESS RATES:")
        for endpoint, stats in endpoint_stats.items():
            success_rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            status_emoji = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
            self.logger.info(f"   {status_emoji} {endpoint}: {success_rate:.0f}% "
                           f"({stats['passed']}/{stats['total']} passed)")
        
        # API call statistics from Birdeye API
        api_stats = self.birdeye_api.get_api_call_statistics()
        self.logger.info(f"\n📞 API USAGE STATISTICS:")
        self.logger.info(f"   • Total API Calls: {api_stats['total_api_calls']}")
        self.logger.info(f"   • Cache Hit Rate: {api_stats['cache_hit_rate_percent']:.1f}%")
        self.logger.info(f"   • Average API Response: {api_stats['average_response_time_ms']:.0f}ms")
        
        # Overall assessment
        self.logger.info(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 95 and not self.critical_issues:
            self.logger.info("   🎉 EXCELLENT: All Birdeye endpoints working perfectly!")
        elif success_rate >= 85 and len(self.critical_issues) < 2:
            self.logger.info("   ✅ GOOD: Most endpoints working well with minor issues.")
        elif success_rate >= 70:
            self.logger.info("   ⚠️  FAIR: Some endpoints have issues that need attention.")
        else:
            self.logger.error("   🚨 POOR: Significant issues detected requiring immediate attention!")
        
        # Recommendations
        recommendations = []
        if self.critical_issues:
            recommendations.append("🔧 Fix critical authentication or connectivity issues")
        if len(self.all_warnings) > 20:
            recommendations.append("🔍 Review endpoint response handling for missing fields")
        if any(r.response_time_ms > 10000 for r in self.test_results):
            recommendations.append("⚡ Optimize slow endpoint calls or implement timeout handling")
        if api_stats['cache_hit_rate_percent'] < 50:
            recommendations.append("📋 Improve caching strategy to reduce API calls")
            
        if recommendations:
            self.logger.info(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                self.logger.info(f"   {rec}")
        
        # Create summary object
        summary = {
            "test_overview": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "warning_tests": self.warning_tests,
                "success_rate_percent": success_rate,
                "elapsed_time_seconds": elapsed_time
            },
            "critical_issues": self.critical_issues,
            "warnings": self.all_warnings,
            "endpoint_stats": endpoint_stats,
            "api_stats": api_stats,
            "recommendations": recommendations,
            "test_results": [asdict(result) for result in self.test_results]
        }
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"scripts/results/comprehensive_birdeye_test_{timestamp}.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        self.logger.info(f"\n💾 Detailed results saved to: {results_file}")
        self.logger.info("=" * 100)
        
        return summary

async def main():
    """Run the comprehensive Birdeye endpoint test"""
    tester = ComprehensiveBirdeyeEndpointTester()
    
    try:
        summary = await tester.run_comprehensive_test()
        
        # Exit with appropriate code
        if summary["critical_issues"]:
            sys.exit(1)  # Critical issues found
        elif summary["test_overview"]["success_rate_percent"] < 80:
            sys.exit(2)  # Low success rate
        else:
            sys.exit(0)  # All good
            
    except KeyboardInterrupt:
        tester.logger.info("\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        tester.logger.error(f"💥 Test suite failed with error: {e}")
        tester.logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup
        try:
            await tester.birdeye_api.close_session()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 