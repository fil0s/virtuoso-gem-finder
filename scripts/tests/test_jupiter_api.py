#!/usr/bin/env python3
"""
Jupiter API Test Script - IMPROVED VERSION

Tests Jupiter's APIs to understand token data structure
and evaluate suitability for short-term trending token detection.

FIXES:
- Updated API endpoints based on current Jupiter documentation
- Added retry logic and better error handling
- Added timeout configurations
- Added alternative endpoint testing
- Improved DNS resolution handling
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JupiterAPITester:
    """Test and analyze Jupiter API endpoints - IMPROVED VERSION"""
    
    def __init__(self):
        # CORRECTED Jupiter API URLs based on investigation and documentation
        self.base_urls = {
            # ISSUE FOUND: price.jup.ag domain doesn't exist (DNS resolution fails)
            # Using quote-api.jup.ag as the main working endpoint
            "quote": "https://quote-api.jup.ag/v6",  # ✅ CONFIRMED WORKING
            "stats": "https://stats.jup.ag",  # ✅ DNS resolves (may have 522 errors)
            # Alternative approaches since price.jup.ag doesn't exist:
            "tokens_via_quote": "https://quote-api.jup.ag/v6",  # Use quote API for tokens
            # Backup endpoints to test
            "api_base": "https://api.jup.ag",  # Test if price API is here
            "jup_base": "https://jup.ag/api"  # Alternative base
        }
        self.session = None
        self.test_results = {}
        # Add timeout and retry configuration
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.max_retries = 3
        
    async def __aenter__(self):
        # Configure session with timeout and DNS resolution
        connector = aiohttp.TCPConnector(
            limit=100,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True
        )
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request_with_retry(self, url: str, params: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic and better error handling"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'success',
                            'data': data,
                            'status_code': response.status,
                            'response_time': response.headers.get('X-Response-Time', 'unknown'),
                            'attempt': attempt + 1
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'status': 'error',
                            'status_code': response.status,
                            'error': error_text[:500],  # Truncate long errors
                            'attempt': attempt + 1
                        }
                        
            except aiohttp.ClientConnectorError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except asyncio.TimeoutError as e:
                last_error = f"Timeout error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} timed out: {last_error}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
        
        return {
            'status': 'exception',
            'error': last_error,
            'attempts': self.max_retries
        }

    async def test_price_api_endpoints(self) -> Dict[str, Any]:
        """Test Jupiter's price data access - FIXED for DNS issues"""
        logger.info("💰 Testing Jupiter Price Data Access (CORRECTED)...")
        
        test_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # POPCAT
            "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh"   # WBTC
        ]
        
        # CORRECTED: Only test working endpoints (price.jup.ag doesn't exist)
        endpoints_to_test = [
            # ❌ REMOVED: price.jup.ag endpoints (DNS resolution fails)
            # ✅ WORKING: Use quote API to derive price data
            {
                "name": "price_via_quote_sol_usdc",
                "url": f"{self.base_urls['quote']}/quote",
                "params": {
                    "inputMint": test_tokens[0],  # SOL
                    "outputMint": test_tokens[1],  # USDC
                    "amount": "1000000000",  # 1 SOL
                    "slippageBps": "50"
                }
            },
            {
                "name": "price_via_quote_reverse",
                "url": f"{self.base_urls['quote']}/quote", 
                "params": {
                    "inputMint": test_tokens[1],  # USDC
                    "outputMint": test_tokens[0],  # SOL
                    "amount": "100000000",  # 100 USDC
                    "slippageBps": "50"
                }
            },
            # Test token list from quote API
            {
                "name": "available_tokens",
                "url": f"{self.base_urls['quote']}/tokens",
                "params": {}
            },
            # Test alternative API bases if they exist
            {
                "name": "test_api_base_tokens",
                "url": f"{self.base_urls['api_base']}/tokens",
                "params": {}
            },
            {
                "name": "test_jup_base_price",
                "url": f"{self.base_urls['jup_base']}/price",
                "params": {"ids": test_tokens[0]}
            }
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            logger.info(f"Testing: {endpoint['name']}")
            
            result = await self._make_request_with_retry(
                endpoint['url'], 
                endpoint['params']
            )
            
            if result['status'] == 'success':
                # Add data analysis for successful responses
                data = result['data']
                result.update({
                    'data_keys': list(data.keys()) if isinstance(data, dict) else 'list',
                    'sample_size': len(data) if isinstance(data, (dict, list)) else 1
                })
                logger.info(f"✅ {endpoint['name']}: Success ({result.get('sample_size', 'unknown')} items)")
            else:
                logger.error(f"❌ {endpoint['name']}: {result.get('error', 'Unknown error')}")
            
            results[endpoint['name']] = result
            await asyncio.sleep(0.5)  # Rate limiting
            
        return results
    
    async def test_stats_api_endpoints(self) -> Dict[str, Any]:
        """Test Jupiter's stats API endpoints - handling 522 timeout errors"""
        logger.info("📊 Testing Jupiter Stats API (with 522 error handling)...")
        
        # Test stats endpoints with better error tolerance
        endpoints_to_test = [
            {
                "name": "stats_root",
                "url": f"{self.base_urls['stats']}",
                "params": {}
            },
            {
                "name": "volume_stats",
                "url": f"{self.base_urls['stats']}/volume",
                "params": {}
            },
            {
                "name": "volume_24h",
                "url": f"{self.base_urls['stats']}/volume/24h",
                "params": {}
            },
            {
                "name": "token_volume",
                "url": f"{self.base_urls['stats']}/token",
                "params": {"mint": "So11111111111111111111111111111111111111112"}
            },
            {
                "name": "top_tokens",
                "url": f"{self.base_urls['stats']}/tokens/top",
                "params": {}
            },
            {
                "name": "trending_tokens",
                "url": f"{self.base_urls['stats']}/trending",
                "params": {}
            }
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            logger.info(f"Testing: {endpoint['name']}")
            
            result = await self._make_request_with_retry(
                endpoint['url'], 
                endpoint['params']
            )
            
            if result['status'] == 'success':
                result['data_structure'] = self._analyze_data_structure(result['data'])
                logger.info(f"✅ {endpoint['name']}: Success")
            else:
                logger.error(f"❌ {endpoint['name']}: {result.get('error', 'Unknown error')}")
            
            results[endpoint['name']] = result
            await asyncio.sleep(0.5)
            
        return results
    
    async def test_quote_api_for_liquidity(self) -> Dict[str, Any]:
        """Test Jupiter's quote API to understand liquidity data"""
        logger.info("💧 Testing Jupiter Quote API for liquidity insights...")
        
        # Test swaps to understand liquidity
        test_swaps = [
            {
                "name": "sol_to_usdc_small",
                "params": {
                    "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000000",  # 1 SOL
                    "slippageBps": "50"  # 0.5% slippage
                }
            },
            {
                "name": "sol_to_usdc_large",
                "params": {
                    "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "100000000000",  # 100 SOL
                    "slippageBps": "100"  # 1% slippage
                }
            }
        ]
        
        results = {}
        
        for swap in test_swaps:
            try:
                logger.info(f"Testing: {swap['name']}")
                
                url = f"{self.base_urls['quote']}/quote"
                async with self.session.get(url, params=swap['params']) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Analyze quote for liquidity insights
                        analysis = self._analyze_quote_for_liquidity(data, swap['params'])
                        
                        results[swap['name']] = {
                            'status': 'success',
                            'data': data,
                            'liquidity_analysis': analysis,
                            'response_time': response.headers.get('X-Response-Time', 'unknown')
                        }
                        logger.info(f"✅ {swap['name']}: Success")
                    else:
                        error_text = await response.text()
                        results[swap['name']] = {
                            'status': 'error',
                            'status_code': response.status,
                            'error': error_text
                        }
                        logger.error(f"❌ {swap['name']}: HTTP {response.status}")
                        
            except Exception as e:
                results[swap['name']] = {
                    'status': 'exception',
                    'error': str(e)
                }
                logger.error(f"❌ {swap['name']}: Exception - {e}")
                
            await asyncio.sleep(0.5)
            
        return results
    
    def _analyze_data_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of API response data"""
        if isinstance(data, dict):
            return {
                "type": "dict",
                "keys": list(data.keys()),
                "sample_values": {k: type(v).__name__ for k, v in list(data.items())[:5]}
            }
        elif isinstance(data, list):
            return {
                "type": "list",
                "length": len(data),
                "sample_item": data[0] if data else None,
                "item_type": type(data[0]).__name__ if data else None
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:100]  # First 100 chars
            }
    
    def _analyze_quote_for_liquidity(self, quote_data: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze quote data for liquidity insights"""
        analysis = {
            "input_amount": params.get('amount'),
            "slippage_bps": params.get('slippageBps'),
            "has_route_plan": 'routePlan' in quote_data,
            "routes_found": len(quote_data.get('routePlan', [])),
            "price_impact": None,
            "effective_liquidity": None
        }
        
        # Calculate price impact if data is available
        if 'inAmount' in quote_data and 'outAmount' in quote_data:
            in_amount = int(quote_data['inAmount'])
            out_amount = int(quote_data['outAmount'])
            
            # Simple price impact calculation (this would need market price for accuracy)
            analysis['amounts'] = {
                'in_amount': in_amount,
                'out_amount': out_amount,
                'ratio': out_amount / in_amount if in_amount > 0 else 0
            }
        
        # Analyze route complexity
        if 'routePlan' in quote_data:
            route_plan = quote_data['routePlan']
            analysis['route_complexity'] = {
                'total_steps': len(route_plan),
                'dexes_used': list(set(step.get('swapInfo', {}).get('label', 'unknown') for step in route_plan)),
                'multi_hop': len(route_plan) > 1
            }
        
        return analysis
    
    async def test_trending_detection_feasibility(self) -> Dict[str, Any]:
        """Test Jupiter's suitability for trending detection with improved analysis"""
        logger.info("🎯 Testing Jupiter trending detection feasibility...")
        
        analysis = {
            "volume_data_availability": False,
            "liquidity_inference": False,
            "real_time_pricing": False,
            "token_discovery": False,
            "historical_data": False,
            "rate_limits": "unknown",
            "trending_metrics": {},
            "alternative_approaches": {}
        }
        
        # Test volume data from multiple endpoints
        volume_endpoints = [
            f"{self.base_urls['stats']}/volume",
            f"{self.base_urls['stats_alt']}/volume",
            f"{self.base_urls['stats']}/daily"
        ]
        
        for i, url in enumerate(volume_endpoints):
            try:
                result = await self._make_request_with_retry(url)
                if result['status'] == 'success':
                    analysis["volume_data_availability"] = True
                    analysis["trending_metrics"][f"volume_endpoint_{i+1}"] = {
                        "available": True,
                        "url": url,
                        "data_structure": self._analyze_data_structure(result['data'])
                    }
                    break
            except Exception as e:
                analysis["trending_metrics"][f"volume_endpoint_{i+1}"] = {
                    "available": False,
                    "url": url,
                    "error": str(e)
                }
        
        # Test token discovery from multiple endpoints  
        token_endpoints = [
            f"{self.base_urls['price']}/tokens",
            f"{self.base_urls['price_alt']}/tokens"
        ]
        
        for i, url in enumerate(token_endpoints):
            try:
                result = await self._make_request_with_retry(url)
                if result['status'] == 'success':
                    data = result['data']
                    analysis["token_discovery"] = True
                    analysis["trending_metrics"][f"token_list_{i+1}"] = {
                        "available": True,
                        "url": url,
                        "token_count": len(data) if isinstance(data, list) else "unknown",
                        "sample_token": data[0] if isinstance(data, list) and data else None
                    }
                    break
            except Exception as e:
                analysis["trending_metrics"][f"token_list_{i+1}"] = {
                    "available": False,
                    "url": url,
                    "error": str(e)
                }
        
        # Test real-time pricing from multiple endpoints
        price_endpoints = [
            (f"{self.base_urls['price']}/price", {"ids": "So11111111111111111111111111111111111111112"}),
            (f"{self.base_urls['price_alt']}/price", {"ids": "So11111111111111111111111111111111111111112"})
        ]
        
        for i, (url, params) in enumerate(price_endpoints):
            try:
                result = await self._make_request_with_retry(url, params)
                if result['status'] == 'success':
                    analysis["real_time_pricing"] = True
                    analysis["trending_metrics"][f"pricing_{i+1}"] = {
                        "available": True,
                        "url": url,
                        "response_time": result.get('response_time', 'unknown'),
                        "data_freshness": "real-time"
                    }
                    break
            except Exception as e:
                analysis["trending_metrics"][f"pricing_{i+1}"] = {
                    "available": False,
                    "url": url,
                    "error": str(e)
                }
        
        # Test liquidity inference through quotes (this works!)
        try:
            url = f"{self.base_urls['quote']}/quote"
            params = {
                "inputMint": "So11111111111111111111111111111111111111112",
                "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "amount": "1000000000",
                "slippageBps": "50"
            }
            result = await self._make_request_with_retry(url, params)
            if result['status'] == 'success':
                analysis["liquidity_inference"] = True
                analysis["trending_metrics"]["liquidity"] = {
                    "available": True,
                    "method": "quote_analysis",
                    "route_complexity": len(result['data'].get('routePlan', []))
                }
        except Exception as e:
            analysis["trending_metrics"]["liquidity"] = {
                "available": False,
                "error": str(e)
            }
        
        # Add alternative approaches analysis
        analysis["alternative_approaches"] = {
            "quote_api_for_pricing": {
                "feasible": analysis["liquidity_inference"],
                "description": "Use quote API to infer pricing and liquidity",
                "pros": ["Working API", "Real-time data", "Route analysis"],
                "cons": ["Indirect pricing", "Higher API calls needed"]
            },
            "meteora_integration": {
                "feasible": True,
                "description": "Focus on Meteora for pool data, use Jupiter for liquidity",
                "pros": ["Meteora has volume/TVL data", "Jupiter quote API works"],
                "cons": ["Two API dependencies", "Data reconciliation needed"]
            },
            "fallback_apis": {
                "feasible": True,
                "description": "Use Birdeye/Dexscreener as backup for Jupiter data",
                "pros": ["Proven working APIs", "Comprehensive data"],
                "cons": ["API costs", "Rate limiting"]
            }
        }
        
        return analysis
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of Jupiter APIs"""
        logger.info("🚀 Starting comprehensive Jupiter API test...")
        
        test_start = time.time()
        
        # Test 1: Price API
        price_results = await self.test_price_api_endpoints()
        
        # Test 2: Stats API
        stats_results = await self.test_stats_api_endpoints()
        
        # Test 3: Quote API for liquidity
        quote_results = await self.test_quote_api_for_liquidity()
        
        # Test 4: Trending detection feasibility
        trending_feasibility = await self.test_trending_detection_feasibility()
        
        test_duration = time.time() - test_start
        
        results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(test_duration, 2),
                "api_base_urls": self.base_urls
            },
            "price_api_tests": price_results,
            "stats_api_tests": stats_results,
            "quote_api_tests": quote_results,
            "trending_detection_feasibility": trending_feasibility
        }
        
        self.test_results = results
        return results
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/tests/jupiter_api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"💾 Test results saved to: {filename}")


async def main():
    """Run Jupiter API tests"""
    logger.info("🪐 Jupiter API Testing Suite")
    logger.info("=" * 50)
    
    async with JupiterAPITester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Save results
        tester.save_results()
        
        # Print summary
        logger.info("\n📋 TEST SUMMARY:")
        logger.info(f"Duration: {results['test_summary']['duration_seconds']}s")
        
        # Price API results
        price_results = results.get('price_api_tests', {})
        successful_price = sum(1 for r in price_results.values() if r.get('status') == 'success')
        logger.info(f"Price API queries: {successful_price}/{len(price_results)} successful")
        
        # Stats API results
        stats_results = results.get('stats_api_tests', {})
        successful_stats = sum(1 for r in stats_results.values() if r.get('status') == 'success')
        logger.info(f"Stats API queries: {successful_stats}/{len(stats_results)} successful")
        
        # Quote API results
        quote_results = results.get('quote_api_tests', {})
        successful_quotes = sum(1 for r in quote_results.values() if r.get('status') == 'success')
        logger.info(f"Quote API queries: {successful_quotes}/{len(quote_results)} successful")
        
        # Trending feasibility
        trending = results.get('trending_detection_feasibility', {})
        logger.info(f"Volume data available: {trending.get('volume_data_availability', False)}")
        logger.info(f"Real-time pricing: {trending.get('real_time_pricing', False)}")
        logger.info(f"Liquidity inference: {trending.get('liquidity_inference', False)}")
        logger.info(f"Token discovery: {trending.get('token_discovery', False)}")
        
        logger.info("\n✅ Jupiter API test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 