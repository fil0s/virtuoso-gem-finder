#!/usr/bin/env python3
"""
Jupiter Lite-API Investigation
Comprehensive analysis of what data and capabilities are available from lite-api.jup.ag
"""

import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiteAPIInvestigator:
    def __init__(self):
        self.session = None
        self.lite_api_base = "https://lite-api.jup.ag"
        self.main_api_base = "https://quote-api.jup.ag"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_endpoint_availability(self, base_url: str, endpoint_name: str) -> Dict[str, Any]:
        """Test if an endpoint is available and what it returns"""
        
        endpoints_to_test = [
            "/v6/quote",
            "/v6/swap",
            "/v6/swap-instructions",
            "/v1/quote",
            "/price",
            "/tokens",
            "/stats",
            "/health",
            "/",
            "/docs",
            "/api-docs"
        ]
        
        logger.info(f"🔍 Testing {endpoint_name} ({base_url}) endpoint availability...")
        
        results = {}
        
        for endpoint in endpoints_to_test:
            url = f"{base_url}{endpoint}"
            
            try:
                async with self.session.get(url) as response:
                    result = {
                        "endpoint": endpoint,
                        "url": url,
                        "status_code": response.status,
                        "content_type": response.headers.get('content-type', 'unknown'),
                        "content_length": response.headers.get('content-length', 'unknown'),
                        "accessible": response.status < 400,
                        "response_preview": None,
                        "error": None
                    }
                    
                    if response.status < 400:
                        try:
                            # Try to get a preview of the response
                            text = await response.text()
                            if len(text) > 500:
                                result["response_preview"] = text[:500] + "..."
                            else:
                                result["response_preview"] = text
                            
                            # Try to parse as JSON if it looks like JSON
                            if 'json' in result["content_type"] or text.strip().startswith('{'):
                                try:
                                    json_data = json.loads(text)
                                    result["is_json"] = True
                                    result["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else None
                                except:
                                    result["is_json"] = False
                            
                            logger.info(f"   ✅ {endpoint}: {response.status} ({result['content_type']})")
                        except Exception as e:
                            result["error"] = f"Error reading response: {e}"
                            logger.warning(f"   ⚠️ {endpoint}: {response.status} but error reading response")
                    else:
                        error_text = await response.text()
                        result["error"] = error_text[:200] if error_text else "No error details"
                        logger.info(f"   ❌ {endpoint}: {response.status}")
                    
                    results[endpoint] = result
                    
            except Exception as e:
                logger.error(f"   ❌ {endpoint}: Connection error - {e}")
                results[endpoint] = {
                    "endpoint": endpoint,
                    "url": url,
                    "accessible": False,
                    "error": str(e)
                }
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        return results

    async def test_quote_endpoint_differences(self) -> Dict[str, Any]:
        """Compare quote endpoint behavior between lite-api and main API"""
        
        logger.info("🔍 Comparing quote endpoint behavior...")
        
        # Test with different token scenarios
        test_scenarios = [
            {
                "name": "Major Token (SOL->USDC)",
                "params": {
                    "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000000"  # 1 SOL
                }
            },
            {
                "name": "Popular Token (JUP->USDC)",
                "params": {
                    "inputMint": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # JUP
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000"  # 1 JUP
                }
            },
            {
                "name": "Meme Token ($michi->USDC)",
                "params": {
                    "inputMint": "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp",  # $michi
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000"
                }
            },
            {
                "name": "Pump.fun Token (BILLY->USDC)",
                "params": {
                    "inputMint": "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump",  # BILLY
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000"
                }
            },
            {
                "name": "Unlisted Token (USELESS->USDC)",
                "params": {
                    "inputMint": "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",  # USELESS
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000"
                }
            }
        ]
        
        comparison_results = {}
        
        for scenario in test_scenarios:
            logger.info(f"   Testing scenario: {scenario['name']}")
            
            scenario_results = {
                "scenario_name": scenario["name"],
                "params": scenario["params"],
                "lite_api_result": None,
                "main_api_result": None,
                "comparison": {}
            }
            
            # Test lite-api
            lite_url = f"{self.lite_api_base}/v6/quote"
            try:
                async with self.session.get(lite_url, params=scenario["params"]) as response:
                    lite_result = {
                        "status_code": response.status,
                        "success": response.status == 200,
                        "response_data": None,
                        "error": None
                    }
                    
                    if response.status == 200:
                        lite_result["response_data"] = await response.json()
                        logger.info(f"     Lite-API: ✅ Success")
                    else:
                        lite_result["error"] = await response.text()
                        logger.info(f"     Lite-API: ❌ {response.status}")
                    
                    scenario_results["lite_api_result"] = lite_result
                    
            except Exception as e:
                scenario_results["lite_api_result"] = {"error": str(e), "success": False}
                logger.error(f"     Lite-API: ❌ Error - {e}")
            
            await asyncio.sleep(1)  # Rate limiting
            
            # Test main API
            main_url = f"{self.main_api_base}/v6/quote"
            try:
                async with self.session.get(main_url, params=scenario["params"]) as response:
                    main_result = {
                        "status_code": response.status,
                        "success": response.status == 200,
                        "response_data": None,
                        "error": None
                    }
                    
                    if response.status == 200:
                        main_result["response_data"] = await response.json()
                        logger.info(f"     Main-API: ✅ Success")
                    else:
                        main_result["error"] = await response.text()
                        logger.info(f"     Main-API: ❌ {response.status}")
                    
                    scenario_results["main_api_result"] = main_result
                    
            except Exception as e:
                scenario_results["main_api_result"] = {"error": str(e), "success": False}
                logger.error(f"     Main-API: ❌ Error - {e}")
            
            # Compare results
            lite_success = scenario_results["lite_api_result"]["success"]
            main_success = scenario_results["main_api_result"]["success"]
            
            scenario_results["comparison"] = {
                "both_work": lite_success and main_success,
                "only_main_works": main_success and not lite_success,
                "only_lite_works": lite_success and not main_success,
                "neither_works": not lite_success and not main_success,
                "data_differences": self._compare_quote_data(
                    scenario_results["lite_api_result"].get("response_data"),
                    scenario_results["main_api_result"].get("response_data")
                )
            }
            
            comparison_results[scenario["name"]] = scenario_results
            
            await asyncio.sleep(1)  # Rate limiting
        
        return comparison_results

    def _compare_quote_data(self, lite_data: Optional[Dict], main_data: Optional[Dict]) -> Dict[str, Any]:
        """Compare quote response data between APIs"""
        
        if not lite_data or not main_data:
            return {"comparable": False, "reason": "One or both responses missing"}
        
        comparison = {
            "comparable": True,
            "price_difference": None,
            "route_differences": {},
            "field_differences": {}
        }
        
        try:
            # Compare output amounts (price proxy)
            lite_out = float(lite_data.get("outAmount", 0))
            main_out = float(main_data.get("outAmount", 0))
            
            if lite_out > 0 and main_out > 0:
                price_diff_percent = abs(lite_out - main_out) / main_out * 100
                comparison["price_difference"] = {
                    "lite_amount": lite_out,
                    "main_amount": main_out,
                    "difference_percent": round(price_diff_percent, 2)
                }
            
            # Compare route plans
            lite_routes = len(lite_data.get("routePlan", []))
            main_routes = len(main_data.get("routePlan", []))
            
            comparison["route_differences"] = {
                "lite_route_count": lite_routes,
                "main_route_count": main_routes,
                "route_complexity_difference": abs(lite_routes - main_routes)
            }
            
            # Compare key fields
            key_fields = ["priceImpactPct", "slippageBps", "timeTaken"]
            for field in key_fields:
                lite_val = lite_data.get(field)
                main_val = main_data.get(field)
                if lite_val is not None and main_val is not None:
                    comparison["field_differences"][field] = {
                        "lite": lite_val,
                        "main": main_val,
                        "same": lite_val == main_val
                    }
        
        except Exception as e:
            comparison["comparison_error"] = str(e)
        
        return comparison

    async def investigate_lite_api_token_support(self) -> Dict[str, Any]:
        """Investigate what tokens are supported by lite-api"""
        
        logger.info("🔍 Investigating lite-api token support...")
        
        # Try to find token list endpoints
        token_endpoints = [
            "/tokens",
            "/v1/tokens",
            "/token-list",
            "/supported-tokens"
        ]
        
        token_support_info = {
            "token_list_endpoints": {},
            "supported_token_sample": [],
            "unsupported_token_sample": []
        }
        
        # Test token list endpoints
        for endpoint in token_endpoints:
            url = f"{self.lite_api_base}{endpoint}"
            
            try:
                async with self.session.get(url) as response:
                    result = {
                        "status_code": response.status,
                        "accessible": response.status < 400,
                        "content_type": response.headers.get('content-type', 'unknown')
                    }
                    
                    if response.status < 400:
                        try:
                            data = await response.json()
                            result["data_type"] = type(data).__name__
                            if isinstance(data, list):
                                result["token_count"] = len(data)
                                result["sample_tokens"] = data[:5] if data else []
                            elif isinstance(data, dict):
                                result["data_keys"] = list(data.keys())
                            logger.info(f"   ✅ {endpoint}: Found data")
                        except:
                            text = await response.text()
                            result["text_preview"] = text[:200]
                            logger.info(f"   ✅ {endpoint}: Non-JSON response")
                    else:
                        logger.info(f"   ❌ {endpoint}: {response.status}")
                    
                    token_support_info["token_list_endpoints"][endpoint] = result
                    
            except Exception as e:
                logger.error(f"   ❌ {endpoint}: Error - {e}")
                token_support_info["token_list_endpoints"][endpoint] = {"error": str(e)}
            
            await asyncio.sleep(0.5)
        
        return token_support_info

    async def run_comprehensive_investigation(self):
        """Run comprehensive lite-api investigation"""
        
        logger.info("🚀 Starting Comprehensive Lite-API Investigation")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test endpoint availability
        logger.info("\n📡 Testing Lite-API Endpoint Availability")
        lite_endpoints = await self.test_endpoint_availability(self.lite_api_base, "Lite-API")
        
        logger.info("\n📡 Testing Main-API Endpoint Availability (for comparison)")
        main_endpoints = await self.test_endpoint_availability(self.main_api_base, "Main-API")
        
        # Compare quote endpoints
        logger.info("\n🔄 Comparing Quote Endpoint Behavior")
        quote_comparison = await self.test_quote_endpoint_differences()
        
        # Investigate token support
        logger.info("\n🪙 Investigating Token Support")
        token_support = await self.investigate_lite_api_token_support()
        
        total_duration = time.time() - start_time
        
        # Compile comprehensive results
        investigation_results = {
            "investigation_timestamp": datetime.now().isoformat(),
            "investigation_duration_seconds": round(total_duration, 2),
            "lite_api_endpoints": lite_endpoints,
            "main_api_endpoints": main_endpoints,
            "quote_endpoint_comparison": quote_comparison,
            "token_support_investigation": token_support,
            "summary": self._generate_investigation_summary(lite_endpoints, main_endpoints, quote_comparison, token_support)
        }
        
        # Save results
        results_file = f"scripts/tests/lite_api_investigation_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(investigation_results, f, indent=2)
        
        logger.info(f"\n📊 Investigation Complete!")
        logger.info(f"Duration: {total_duration:.2f} seconds")
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        self._print_investigation_summary(investigation_results["summary"])
        
        return investigation_results

    def _generate_investigation_summary(self, lite_endpoints: Dict, main_endpoints: Dict, 
                                      quote_comparison: Dict, token_support: Dict) -> Dict[str, Any]:
        """Generate investigation summary"""
        
        # Endpoint availability comparison
        lite_accessible = sum(1 for ep in lite_endpoints.values() if ep.get("accessible", False))
        main_accessible = sum(1 for ep in main_endpoints.values() if ep.get("accessible", False))
        
        # Quote endpoint success rates
        quote_scenarios = len(quote_comparison)
        lite_successes = sum(1 for result in quote_comparison.values() 
                           if result["lite_api_result"]["success"])
        main_successes = sum(1 for result in quote_comparison.values() 
                           if result["main_api_result"]["success"])
        
        # Token support analysis
        both_work = sum(1 for result in quote_comparison.values() 
                       if result["comparison"]["both_work"])
        only_main_works = sum(1 for result in quote_comparison.values() 
                            if result["comparison"]["only_main_works"])
        
        return {
            "endpoint_availability": {
                "lite_api_accessible_endpoints": lite_accessible,
                "main_api_accessible_endpoints": main_accessible,
                "total_endpoints_tested": len(lite_endpoints)
            },
            "quote_performance": {
                "scenarios_tested": quote_scenarios,
                "lite_api_success_rate": round(lite_successes / quote_scenarios * 100, 1),
                "main_api_success_rate": round(main_successes / quote_scenarios * 100, 1),
                "both_apis_work": both_work,
                "only_main_api_works": only_main_works
            },
            "key_findings": self._identify_key_findings(lite_endpoints, quote_comparison),
            "recommendations": self._generate_recommendations(quote_comparison)
        }

    def _identify_key_findings(self, lite_endpoints: Dict, quote_comparison: Dict) -> List[str]:
        """Identify key findings from the investigation"""
        
        findings = []
        
        # Check if quote endpoint exists
        quote_accessible = lite_endpoints.get("/v6/quote", {}).get("accessible", False)
        if not quote_accessible:
            findings.append("Lite-API /v6/quote endpoint is not accessible or returns errors")
        
        # Check token support differences
        only_main_works_count = sum(1 for result in quote_comparison.values() 
                                  if result["comparison"]["only_main_works"])
        
        if only_main_works_count > 0:
            findings.append(f"{only_main_works_count} tokens work only with main API, not lite-api")
        
        # Check for specific token types
        meme_token_results = [result for name, result in quote_comparison.items() 
                            if "meme" in name.lower() or "pump" in name.lower() or "BILLY" in name]
        
        if meme_token_results:
            meme_failures = sum(1 for result in meme_token_results 
                              if not result["lite_api_result"]["success"])
            if meme_failures > 0:
                findings.append(f"Lite-API struggles with meme/pump.fun tokens ({meme_failures} failures)")
        
        return findings

    def _generate_recommendations(self, quote_comparison: Dict) -> List[str]:
        """Generate recommendations based on investigation"""
        
        recommendations = []
        
        # Analyze success patterns
        lite_success_rate = sum(1 for result in quote_comparison.values() 
                              if result["lite_api_result"]["success"]) / len(quote_comparison)
        
        if lite_success_rate < 0.5:
            recommendations.append("Use main API (quote-api.jup.ag) for comprehensive token support")
        elif lite_success_rate < 1.0:
            recommendations.append("Use hybrid approach: try lite-api first, fallback to main API")
        else:
            recommendations.append("Lite-API appears sufficient for tested token types")
        
        # Check for specific use cases
        major_tokens_work = any(result["lite_api_result"]["success"] 
                              for name, result in quote_comparison.items() 
                              if "SOL" in name or "JUP" in name)
        
        if major_tokens_work:
            recommendations.append("Lite-API suitable for major tokens (SOL, JUP, etc.)")
        
        return recommendations

    def _print_investigation_summary(self, summary: Dict[str, Any]):
        """Print investigation summary"""
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 LITE-API INVESTIGATION SUMMARY")
        logger.info("=" * 80)
        
        # Endpoint availability
        endpoint_info = summary["endpoint_availability"]
        logger.info(f"\n📡 Endpoint Availability:")
        logger.info(f"   Lite-API accessible endpoints: {endpoint_info['lite_api_accessible_endpoints']}")
        logger.info(f"   Main-API accessible endpoints: {endpoint_info['main_api_accessible_endpoints']}")
        
        # Quote performance
        quote_info = summary["quote_performance"]
        logger.info(f"\n🔄 Quote Performance:")
        logger.info(f"   Scenarios tested: {quote_info['scenarios_tested']}")
        logger.info(f"   Lite-API success rate: {quote_info['lite_api_success_rate']}%")
        logger.info(f"   Main-API success rate: {quote_info['main_api_success_rate']}%")
        logger.info(f"   Both APIs work: {quote_info['both_apis_work']} scenarios")
        logger.info(f"   Only Main-API works: {quote_info['only_main_api_works']} scenarios")
        
        # Key findings
        if summary["key_findings"]:
            logger.info(f"\n🔍 Key Findings:")
            for finding in summary["key_findings"]:
                logger.info(f"   • {finding}")
        
        # Recommendations
        if summary["recommendations"]:
            logger.info(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                logger.info(f"   • {rec}")

async def main():
    """Main investigation function"""
    async with LiteAPIInvestigator() as investigator:
        await investigator.run_comprehensive_investigation()

if __name__ == "__main__":
    asyncio.run(main()) 