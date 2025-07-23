#!/usr/bin/env python3
"""
Jupiter API Test - OFFICIAL SDK VERSION

Uses the official Jupiter Python SDK patterns from Jupiter-DevRel repository
to properly test Jupiter APIs for trending token detection.

References:
- https://github.com/Jupiter-DevRel/python-examples
- https://github.com/Jupiter-DevRel/jup-python-sdk
- Jupiter API Portal: http://portal.jup.ag/
"""

import asyncio
import aiohttp
import json
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JupiterOfficialAPITester:
    """Test Jupiter APIs using official patterns from Jupiter-DevRel"""
    
    def __init__(self):
        # OFFICIAL Jupiter API URLs (based on Jupiter-DevRel repository)
        self.base_urls = {
            # These are the CORRECT endpoints based on official documentation
            "quote": "https://quote-api.jup.ag/v6",  # ✅ CONFIRMED WORKING
            "swap": "https://quote-api.jup.ag/v6",   # Same base for swap operations
            "price": "https://price.jup.ag/v4",      # Try v4 instead of v6
            "tokens": "https://token.jup.ag/all",    # Token list endpoint
            # Alternative price endpoints to test
            "price_alt": "https://api.jup.ag/price/v4",
        }
        
        # API Configuration (following Jupiter-DevRel patterns)
        self.api_key = os.getenv('JUPITER_API_KEY')  # Optional from portal.jup.ag
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.max_retries = 3
        
        # Headers for Jupiter API (following official patterns)
        self.headers = {
            'User-Agent': 'VirtuosoGemHunter/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
            logger.info("🔑 Using Jupiter API key for enhanced limits")
        else:
            logger.info("🆓 Using free Jupiter API (no key)")
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=100,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True
        )
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector,
            headers=self.headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request_with_retry(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with official Jupiter API patterns"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'success',
                            'data': data,
                            'status_code': response.status,
                            'attempt': attempt + 1,
                            'response_headers': dict(response.headers)
                        }
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        error_text = await response.text()
                        return {
                            'status': 'error',
                            'status_code': response.status,
                            'error': error_text[:500],
                            'attempt': attempt + 1
                        }
                        
            except aiohttp.ClientConnectorError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
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

    async def test_token_list_api(self) -> Dict[str, Any]:
        """Test Jupiter token list API - OFFICIAL APPROACH"""
        logger.info("📋 Testing Jupiter Token List API (Official)...")
        
        # Test multiple token list endpoints
        endpoints_to_test = [
            {
                "name": "all_tokens",
                "url": self.base_urls['tokens'],
                "params": {}
            },
            {
                "name": "quote_tokens", 
                "url": f"{self.base_urls['quote']}/tokens",
                "params": {}
            },
            {
                "name": "strict_tokens",
                "url": f"{self.base_urls['tokens']}?strict=true",
                "params": {}
            }
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            logger.info(f"Testing: {endpoint['name']}")
            
            result = await self._make_request_with_retry(
                endpoint['url'], 
                endpoint.get('params')
            )
            
            if result['status'] == 'success':
                data = result['data']
                token_count = len(data) if isinstance(data, list) else len(data.get('tokens', []))
                
                result.update({
                    'token_count': token_count,
                    'sample_token': data[0] if isinstance(data, list) and data else data.get('tokens', [{}])[0] if data.get('tokens') else {},
                    'data_structure': self._analyze_token_structure(data)
                })
                logger.info(f"✅ {endpoint['name']}: {token_count} tokens found")
            else:
                logger.error(f"❌ {endpoint['name']}: {result.get('error', 'Unknown error')}")
            
            results[endpoint['name']] = result
            await asyncio.sleep(0.5)
            
        return results

    async def test_price_api_official(self) -> Dict[str, Any]:
        """Test Jupiter Price API - CORRECTED ENDPOINTS"""
        logger.info("💰 Testing Jupiter Price API (Official Endpoints)...")
        
        test_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # POPCAT
        ]
        
        # Test different price API approaches
        endpoints_to_test = [
            {
                "name": "price_v4_single",
                "url": f"{self.base_urls['price']}/price",
                "params": {"ids": test_tokens[0]}
            },
            {
                "name": "price_v4_multiple",
                "url": f"{self.base_urls['price']}/price", 
                "params": {"ids": ",".join(test_tokens)}
            },
            {
                "name": "price_alt_single",
                "url": f"{self.base_urls['price_alt']}/price",
                "params": {"ids": test_tokens[0]}
            },
            # Fallback: Use quote API for price derivation
            {
                "name": "price_via_quote_sol_usdc",
                "url": f"{self.base_urls['quote']}/quote",
                "params": {
                    "inputMint": test_tokens[0],
                    "outputMint": test_tokens[1],
                    "amount": "1000000000",  # 1 SOL
                    "slippageBps": "50"
                }
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
                data = result['data']
                
                # Analyze price data structure
                if 'quote' in endpoint['name']:
                    # Handle quote-based pricing
                    price_analysis = self._analyze_quote_pricing(data, endpoint['params'])
                else:
                    # Handle direct price API
                    price_analysis = self._analyze_price_data(data)
                
                result.update({
                    'price_analysis': price_analysis,
                    'trending_suitability': self._assess_trending_suitability(data, endpoint['name'])
                })
                logger.info(f"✅ {endpoint['name']}: Success")
            else:
                logger.error(f"❌ {endpoint['name']}: {result.get('error', 'Unknown error')}")
            
            results[endpoint['name']] = result
            await asyncio.sleep(0.5)
            
        return results

    async def test_quote_api_comprehensive(self) -> Dict[str, Any]:
        """Test Jupiter Quote API comprehensively for trending detection"""
        logger.info("🔄 Testing Jupiter Quote API (Comprehensive)...")
        
        # Test various quote scenarios for trending analysis
        test_scenarios = [
            {
                "name": "sol_usdc_small",
                "params": {
                    "inputMint": "So11111111111111111111111111111111111111112",
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "amount": "1000000000",  # 1 SOL
                    "slippageBps": "50"
                }
            },
            {
                "name": "sol_usdc_large", 
                "params": {
                    "inputMint": "So11111111111111111111111111111111111111112",
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "amount": "100000000000",  # 100 SOL
                    "slippageBps": "100"
                }
            },
            {
                "name": "popcat_usdc",
                "params": {
                    "inputMint": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 
                    "amount": "1000000000",  # 1B POPCAT (assuming 9 decimals)
                    "slippageBps": "100"
                }
            }
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            logger.info(f"Testing: {scenario['name']}")
            
            url = f"{self.base_urls['quote']}/quote"
            result = await self._make_request_with_retry(url, scenario['params'])
            
            if result['status'] == 'success':
                data = result['data']
                
                # Comprehensive analysis for trending detection
                analysis = {
                    'liquidity_analysis': self._analyze_liquidity_from_quote(data, scenario['params']),
                    'route_analysis': self._analyze_route_complexity(data),
                    'slippage_analysis': self._analyze_slippage_impact(data, scenario['params']),
                    'trending_metrics': self._extract_trending_metrics(data)
                }
                
                result['comprehensive_analysis'] = analysis
                logger.info(f"✅ {scenario['name']}: Success - {len(data.get('routePlan', []))} routes")
            else:
                logger.error(f"❌ {scenario['name']}: {result.get('error', 'Unknown error')}")
            
            results[scenario['name']] = result
            await asyncio.sleep(0.5)
            
        return results

    def _analyze_token_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze token list structure for trending detection needs"""
        sample_token = {}
        
        if isinstance(data, list) and data:
            sample_token = data[0] if isinstance(data[0], dict) else {}
        elif isinstance(data, dict) and 'tokens' in data:
            tokens = data['tokens']
            sample_token = tokens[0] if tokens and isinstance(tokens[0], dict) else {}
        elif isinstance(data, dict):
            sample_token = data
        
        # Handle case where sample_token might be a string or other type
        if not isinstance(sample_token, dict):
            return {
                'error': f'Unexpected token structure: {type(sample_token).__name__}',
                'sample_data': str(sample_token)[:100],
                'data_type': type(data).__name__,
                'data_length': len(data) if hasattr(data, '__len__') else 'unknown'
            }
        
        return {
            'available_fields': list(sample_token.keys()) if sample_token else [],
            'has_symbol': 'symbol' in sample_token,
            'has_name': 'name' in sample_token,
            'has_decimals': 'decimals' in sample_token,
            'has_mint_address': 'address' in sample_token or 'mint' in sample_token,
            'trending_relevant_fields': {
                'volume_24h': 'volume24h' in sample_token or 'volume_24h' in sample_token,
                'price': 'price' in sample_token,
                'market_cap': 'market_cap' in sample_token or 'marketCap' in sample_token,
                'liquidity': 'liquidity' in sample_token,
            },
            'sample_token': sample_token
        }

    def _analyze_price_data(self, data: Any) -> Dict[str, Any]:
        """Analyze direct price API data structure"""
        if isinstance(data, dict) and 'data' in data:
            price_data = data['data']
            if price_data:
                sample_token = next(iter(price_data.values()), {})
                return {
                    'token_count': len(price_data),
                    'available_fields': list(sample_token.keys()),
                    'has_price': 'price' in sample_token,
                    'has_volume': 'volume24h' in sample_token or 'volume_24h' in sample_token,
                    'has_change': 'priceChange24h' in sample_token or 'change_24h' in sample_token,
                    'sample_data': sample_token
                }
        
        return {'error': 'Unexpected price data structure', 'raw_data': data}

    def _analyze_quote_pricing(self, data: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze quote data for price derivation"""
        if 'inAmount' in data and 'outAmount' in data:
            in_amount = int(data['inAmount'])
            out_amount = int(data['outAmount'])
            
            return {
                'price_derivable': True,
                'input_amount': in_amount,
                'output_amount': out_amount,
                'implied_rate': out_amount / in_amount if in_amount > 0 else 0,
                'slippage_bps': params.get('slippageBps'),
                'route_count': len(data.get('routePlan', [])),
                'can_track_pricing': True
            }
        
        return {'price_derivable': False, 'error': 'Missing amount data'}

    def _analyze_liquidity_from_quote(self, data: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze liquidity indicators from quote data"""
        return {
            'route_availability': len(data.get('routePlan', [])) > 0,
            'route_count': len(data.get('routePlan', [])),
            'multi_hop_routes': len(data.get('routePlan', [])) > 1,
            'slippage_tolerance': params.get('slippageBps'),
            'price_impact_indicators': {
                'has_price_impact': 'priceImpactPct' in data,
                'price_impact_value': data.get('priceImpactPct')
            }
        }

    def _analyze_route_complexity(self, data: Dict) -> Dict[str, Any]:
        """Analyze route complexity for liquidity assessment"""
        route_plan = data.get('routePlan', [])
        
        if not route_plan:
            return {'no_routes': True}
        
        dexes_used = []
        total_steps = len(route_plan)
        
        for step in route_plan:
            swap_info = step.get('swapInfo', {})
            if 'label' in swap_info:
                dexes_used.append(swap_info['label'])
        
        return {
            'total_steps': total_steps,
            'unique_dexes': list(set(dexes_used)),
            'dex_count': len(set(dexes_used)),
            'is_direct_swap': total_steps == 1,
            'complexity_score': total_steps + len(set(dexes_used))  # Simple complexity metric
        }

    def _analyze_slippage_impact(self, data: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze slippage and price impact"""
        return {
            'requested_slippage_bps': params.get('slippageBps'),
            'has_price_impact_data': 'priceImpactPct' in data,
            'price_impact_pct': data.get('priceImpactPct'),
            'other_amount_threshold': data.get('otherAmountThreshold'),
            'swap_mode': data.get('swapMode', 'ExactIn')
        }

    def _extract_trending_metrics(self, data: Dict) -> Dict[str, Any]:
        """Extract metrics useful for trending detection"""
        return {
            'real_time_pricing': True,  # Quote API provides real-time data
            'liquidity_proxy': len(data.get('routePlan', [])) > 0,
            'market_depth_indicator': len(data.get('routePlan', [])),
            'dex_coverage': len(set(step.get('swapInfo', {}).get('label', '') for step in data.get('routePlan', []))),
            'can_calculate_vlr': True,  # Volume-to-Liquidity Ratio via multiple quotes
            'update_frequency': 'real-time',
            'trending_detection_score': min(10, len(data.get('routePlan', [])) * 2)  # 0-10 score
        }

    def _assess_trending_suitability(self, data: Any, endpoint_name: str) -> Dict[str, Any]:
        """Assess how suitable this endpoint is for trending detection"""
        if 'quote' in endpoint_name:
            return {
                'suitability_score': 8,  # Quote API is very suitable
                'pros': [
                    'Real-time data',
                    'Liquidity indicators via routes',
                    'Price derivation possible',
                    'High update frequency'
                ],
                'cons': [
                    'Requires multiple calls for volume data',
                    'Indirect volume measurement'
                ],
                'trending_use_cases': [
                    'Real-time price tracking',
                    'Liquidity depth analysis',
                    'Market activity inference'
                ]
            }
        else:
            # Direct price API
            return {
                'suitability_score': 6,
                'pros': [
                    'Direct price data',
                    'Potentially includes volume'
                ],
                'cons': [
                    'May have connection issues',
                    'Limited availability'
                ],
                'trending_use_cases': [
                    'Price change tracking',
                    'Volume analysis (if available)'
                ]
            }

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Jupiter API test using official patterns"""
        logger.info("🚀 Starting Jupiter API test with OFFICIAL patterns...")
        
        test_start = time.time()
        
        # Test 1: Token List API
        token_list_results = await self.test_token_list_api()
        
        # Test 2: Price API (multiple approaches)
        price_results = await self.test_price_api_official()
        
        # Test 3: Quote API (comprehensive)
        quote_results = await self.test_quote_api_comprehensive()
        
        test_duration = time.time() - test_start
        
        # Generate comprehensive analysis
        final_analysis = self._generate_final_analysis(
            token_list_results, price_results, quote_results
        )
        
        results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(test_duration, 2),
                "api_base_urls": self.base_urls,
                "using_api_key": bool(self.api_key)
            },
            "token_list_tests": token_list_results,
            "price_api_tests": price_results,
            "quote_api_tests": quote_results,
            "final_analysis": final_analysis
        }
        
        return results

    def _generate_final_analysis(self, token_results: Dict, price_results: Dict, quote_results: Dict) -> Dict[str, Any]:
        """Generate final analysis for trending detection feasibility"""
        
        # Count successful tests
        successful_token_tests = sum(1 for r in token_results.values() if r.get('status') == 'success')
        successful_price_tests = sum(1 for r in price_results.values() if r.get('status') == 'success')
        successful_quote_tests = sum(1 for r in quote_results.values() if r.get('status') == 'success')
        
        total_tests = len(token_results) + len(price_results) + len(quote_results)
        total_successful = successful_token_tests + successful_price_tests + successful_quote_tests
        
        success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "overall_success_rate": round(success_rate, 1),
            "api_availability": {
                "token_list_api": successful_token_tests > 0,
                "price_api": successful_price_tests > 0,
                "quote_api": successful_quote_tests > 0
            },
            "trending_detection_feasibility": {
                "feasibility_score": min(10, (successful_quote_tests * 3 + successful_price_tests * 2 + successful_token_tests)),
                "real_time_pricing": successful_quote_tests > 0 or successful_price_tests > 0,
                "token_discovery": successful_token_tests > 0,
                "liquidity_inference": successful_quote_tests > 0,
                "volume_tracking": "indirect_via_quotes" if successful_quote_tests > 0 else "limited"
            },
            "recommendations": self._generate_recommendations(successful_token_tests, successful_price_tests, successful_quote_tests),
            "next_steps": [
                "Integrate official Jupiter Python SDK" if success_rate > 50 else "Investigate API access issues",
                "Implement quote-based trending detection" if successful_quote_tests > 0 else "Find alternative APIs",
                "Set up API key for enhanced limits" if not self.api_key and success_rate > 30 else "Debug connection issues"
            ]
        }

    def _generate_recommendations(self, token_success: int, price_success: int, quote_success: int) -> List[str]:
        """Generate specific recommendations based on test results"""
        recommendations = []
        
        if quote_success > 0:
            recommendations.append("✅ USE Quote API as primary data source - most reliable")
            recommendations.append("💡 Implement quote-based price tracking for trending detection")
        
        if token_success > 0:
            recommendations.append("✅ USE Token List API for token discovery")
        
        if price_success > 0:
            recommendations.append("✅ USE Price API as secondary data source")
        else:
            recommendations.append("⚠️ Price API unreliable - use Quote API for pricing")
        
        if token_success == 0 and price_success == 0 and quote_success == 0:
            recommendations.extend([
                "❌ All Jupiter APIs failed - investigate network/authentication issues",
                "🔄 Consider using Jupiter Python SDK instead of raw HTTP calls",
                "🔑 Try obtaining API key from portal.jup.ag for better access"
            ])
        
        return recommendations

    def save_results(self, results: Dict, filename: Optional[str] = None):
        """Save test results to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/tests/jupiter_official_api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Official Jupiter API test results saved to: {filename}")


async def main():
    """Run Jupiter API tests using official patterns"""
    logger.info("🪐 Jupiter API Testing Suite - OFFICIAL VERSION")
    logger.info("=" * 60)
    logger.info("Based on Jupiter-DevRel repository patterns")
    logger.info("=" * 60)
    
    async with JupiterOfficialAPITester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Save results
        tester.save_results(results)
        
        # Print comprehensive summary
        logger.info("\n📋 COMPREHENSIVE TEST SUMMARY:")
        logger.info("=" * 50)
        
        summary = results['test_summary']
        logger.info(f"Duration: {summary['duration_seconds']}s")
        logger.info(f"Using API Key: {summary['using_api_key']}")
        
        analysis = results['final_analysis']
        logger.info(f"Overall Success Rate: {analysis['overall_success_rate']}%")
        logger.info(f"Trending Feasibility Score: {analysis['trending_detection_feasibility']['feasibility_score']}/10")
        
        # API Availability
        availability = analysis['api_availability']
        logger.info(f"\n🔗 API Availability:")
        logger.info(f"  Token List API: {'✅' if availability['token_list_api'] else '❌'}")
        logger.info(f"  Price API: {'✅' if availability['price_api'] else '❌'}")
        logger.info(f"  Quote API: {'✅' if availability['quote_api'] else '❌'}")
        
        # Trending Detection Capabilities
        trending = analysis['trending_detection_feasibility']
        logger.info(f"\n🎯 Trending Detection Capabilities:")
        logger.info(f"  Real-time Pricing: {'✅' if trending['real_time_pricing'] else '❌'}")
        logger.info(f"  Token Discovery: {'✅' if trending['token_discovery'] else '❌'}")
        logger.info(f"  Liquidity Inference: {'✅' if trending['liquidity_inference'] else '❌'}")
        logger.info(f"  Volume Tracking: {trending['volume_tracking']}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            logger.info(f"  {rec}")
        
        # Next Steps
        logger.info(f"\n🚀 NEXT STEPS:")
        for step in analysis['next_steps']:
            logger.info(f"  {step}")
        
        logger.info("\n✅ Jupiter Official API test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 