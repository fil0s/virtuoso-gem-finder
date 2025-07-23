#!/usr/bin/env python3
"""
Jupiter Price API Test
Comprehensive testing of Jupiter's Price API based on official documentation
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

class JupiterPriceAPITester:
    def __init__(self):
        self.session = None
        
        # Price API endpoints to test
        self.price_endpoints = [
            "https://price.jup.ag/v4/price",
            "https://price.jup.ag/v1/price", 
            "https://price.jup.ag/price",
            "https://api.jup.ag/price/v4/price",
            "https://api.jup.ag/price",
            "https://quote-api.jup.ag/price"
        ]
        
        # Test tokens (mix of different types)
        self.test_tokens = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "$michi": "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp",
            "BILLY": "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump",
            "USELESS": "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk"
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_endpoint_discovery(self) -> Dict[str, Any]:
        """Test different possible Price API endpoints"""
        
        logger.info("🔍 Testing Price API endpoint discovery...")
        
        endpoint_results = {}
        
        for endpoint in self.price_endpoints:
            logger.info(f"   Testing: {endpoint}")
            
            try:
                # Test basic endpoint availability
                async with self.session.get(endpoint) as response:
                    result = {
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "content_type": response.headers.get('content-type', 'unknown'),
                        "accessible": response.status < 500,
                        "response_preview": None,
                        "error": None
                    }
                    
                    if response.status < 500:
                        try:
                            text = await response.text()
                            result["response_preview"] = text[:300] if text else "Empty response"
                            
                            if response.status == 200:
                                logger.info(f"     ✅ Success: {response.status}")
                            else:
                                logger.info(f"     ⚠️ Accessible but needs params: {response.status}")
                        except Exception as e:
                            result["error"] = f"Error reading response: {e}"
                            logger.warning(f"     ⚠️ Response read error: {e}")
                    else:
                        error_text = await response.text()
                        result["error"] = error_text[:200] if error_text else "Server error"
                        logger.info(f"     ❌ Server error: {response.status}")
                    
                    endpoint_results[endpoint] = result
                    
            except Exception as e:
                logger.error(f"     ❌ Connection error: {e}")
                endpoint_results[endpoint] = {
                    "endpoint": endpoint,
                    "accessible": False,
                    "error": str(e)
                }
            
            await asyncio.sleep(0.5)  # Rate limiting
        
        return endpoint_results

    async def test_price_api_parameters(self, base_endpoint: str) -> Dict[str, Any]:
        """Test different parameter combinations for Price API"""
        
        logger.info(f"🔍 Testing Price API parameters for {base_endpoint}...")
        
        # Different parameter combinations to test
        test_scenarios = [
            {
                "name": "Single token by address",
                "params": {"ids": self.test_tokens["SOL"]}
            },
            {
                "name": "Multiple tokens by address",
                "params": {"ids": f"{self.test_tokens['SOL']},{self.test_tokens['USDC']},{self.test_tokens['JUP']}"}
            },
            {
                "name": "Single token with vs currency",
                "params": {"ids": self.test_tokens["SOL"], "vsToken": self.test_tokens["USDC"]}
            },
            {
                "name": "Token with vs SOL",
                "params": {"ids": self.test_tokens["USDC"], "vsToken": self.test_tokens["SOL"]}
            },
            {
                "name": "Meme token pricing",
                "params": {"ids": self.test_tokens["$michi"]}
            },
            {
                "name": "Pump.fun token pricing", 
                "params": {"ids": self.test_tokens["BILLY"]}
            },
            {
                "name": "Unlisted token pricing",
                "params": {"ids": self.test_tokens["USELESS"]}
            },
            {
                "name": "Alternative parameter names",
                "params": {"id": self.test_tokens["SOL"]}
            },
            {
                "name": "Token symbols instead of addresses",
                "params": {"ids": "SOL,USDC,JUP"}
            }
        ]
        
        scenario_results = {}
        
        for scenario in test_scenarios:
            logger.info(f"   Testing: {scenario['name']}")
            
            try:
                async with self.session.get(base_endpoint, params=scenario["params"]) as response:
                    result = {
                        "scenario_name": scenario["name"],
                        "params": scenario["params"],
                        "status_code": response.status,
                        "success": response.status == 200,
                        "content_type": response.headers.get('content-type', 'unknown'),
                        "response_data": None,
                        "error": None
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            result["response_data"] = data
                            result["data_type"] = type(data).__name__
                            
                            # Analyze response structure
                            if isinstance(data, dict):
                                result["response_keys"] = list(data.keys())
                                result["token_count"] = len(data.get("data", data))
                            elif isinstance(data, list):
                                result["token_count"] = len(data)
                            
                            logger.info(f"     ✅ Success: {result.get('token_count', 0)} tokens")
                            
                        except Exception as e:
                            result["error"] = f"JSON parse error: {e}"
                            result["response_text"] = await response.text()
                            logger.warning(f"     ⚠️ JSON parse error: {e}")
                    else:
                        error_text = await response.text()
                        result["error"] = error_text[:300] if error_text else "No error details"
                        logger.info(f"     ❌ Failed: {response.status}")
                    
                    scenario_results[scenario["name"]] = result
                    
            except Exception as e:
                logger.error(f"     ❌ Error: {e}")
                scenario_results[scenario["name"]] = {
                    "scenario_name": scenario["name"],
                    "params": scenario["params"],
                    "success": False,
                    "error": str(e)
                }
            
            await asyncio.sleep(1)  # Rate limiting
        
        return scenario_results

    async def compare_price_vs_quote_api(self, price_endpoint: str) -> Dict[str, Any]:
        """Compare Price API results with Quote API results"""
        
        logger.info("🔄 Comparing Price API vs Quote API...")
        
        quote_endpoint = "https://quote-api.jup.ag/v6/quote"
        comparison_results = {}
        
        for token_name, token_address in self.test_tokens.items():
            logger.info(f"   Comparing pricing for {token_name}...")
            
            comparison = {
                "token_name": token_name,
                "token_address": token_address,
                "price_api_result": None,
                "quote_api_result": None,
                "comparison_analysis": {}
            }
            
            # Test Price API
            try:
                price_params = {"ids": token_address}
                async with self.session.get(price_endpoint, params=price_params) as response:
                    price_result = {
                        "status_code": response.status,
                        "success": response.status == 200,
                        "response_data": None,
                        "error": None
                    }
                    
                    if response.status == 200:
                        price_result["response_data"] = await response.json()
                        logger.info(f"     Price API: ✅ Success")
                    else:
                        price_result["error"] = await response.text()
                        logger.info(f"     Price API: ❌ {response.status}")
                    
                    comparison["price_api_result"] = price_result
                    
            except Exception as e:
                comparison["price_api_result"] = {"error": str(e), "success": False}
                logger.error(f"     Price API: ❌ Error - {e}")
            
            await asyncio.sleep(1)
            
            # Test Quote API (for comparison)
            try:
                quote_params = {
                    "inputMint": token_address,
                    "outputMint": self.test_tokens["USDC"],
                    "amount": "1000000"
                }
                async with self.session.get(quote_endpoint, params=quote_params) as response:
                    quote_result = {
                        "status_code": response.status,
                        "success": response.status == 200,
                        "response_data": None,
                        "error": None
                    }
                    
                    if response.status == 200:
                        quote_result["response_data"] = await response.json()
                        logger.info(f"     Quote API: ✅ Success")
                    else:
                        quote_result["error"] = await response.text()
                        logger.info(f"     Quote API: ❌ {response.status}")
                    
                    comparison["quote_api_result"] = quote_result
                    
            except Exception as e:
                comparison["quote_api_result"] = {"error": str(e), "success": False}
                logger.error(f"     Quote API: ❌ Error - {e}")
            
            # Analyze comparison
            comparison["comparison_analysis"] = self._analyze_price_comparison(
                comparison["price_api_result"],
                comparison["quote_api_result"]
            )
            
            comparison_results[token_name] = comparison
            await asyncio.sleep(1)
        
        return comparison_results

    def _analyze_price_comparison(self, price_result: Dict, quote_result: Dict) -> Dict[str, Any]:
        """Analyze differences between Price API and Quote API results"""
        
        analysis = {
            "both_successful": False,
            "price_api_advantages": [],
            "quote_api_advantages": [],
            "data_differences": {}
        }
        
        price_success = price_result.get("success", False)
        quote_success = quote_result.get("success", False)
        
        analysis["both_successful"] = price_success and quote_success
        
        if price_success and not quote_success:
            analysis["price_api_advantages"].append("Works when Quote API fails")
        elif quote_success and not price_success:
            analysis["quote_api_advantages"].append("Works when Price API fails")
        
        if price_success and quote_success:
            # Compare response structures and data
            price_data = price_result.get("response_data", {})
            quote_data = quote_result.get("response_data", {})
            
            # Extract pricing information
            if isinstance(price_data, dict):
                if "data" in price_data:
                    analysis["data_differences"]["price_api_structure"] = "Has 'data' wrapper"
                else:
                    analysis["data_differences"]["price_api_structure"] = "Direct price data"
            
            if isinstance(quote_data, dict):
                if "outAmount" in quote_data:
                    analysis["data_differences"]["quote_api_structure"] = "Has swap amount calculation"
        
        return analysis

    async def run_comprehensive_price_api_test(self):
        """Run comprehensive Price API testing"""
        
        logger.info("🚀 Starting Comprehensive Jupiter Price API Test")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test endpoint discovery
        logger.info("\n📡 Phase 1: Endpoint Discovery")
        endpoint_results = await self.test_endpoint_discovery()
        
        # Find working endpoint
        working_endpoint = None
        for endpoint, result in endpoint_results.items():
            if result.get("accessible", False) and result.get("status_code", 500) < 500:
                working_endpoint = endpoint
                logger.info(f"✅ Found working endpoint: {endpoint}")
                break
        
        parameter_results = {}
        comparison_results = {}
        
        if working_endpoint:
            # Test parameters
            logger.info(f"\n🔧 Phase 2: Parameter Testing")
            parameter_results = await self.test_price_api_parameters(working_endpoint)
            
            # Compare with Quote API
            logger.info(f"\n🔄 Phase 3: Price vs Quote API Comparison")
            comparison_results = await self.compare_price_vs_quote_api(working_endpoint)
        else:
            logger.warning("❌ No working Price API endpoint found, skipping parameter and comparison tests")
        
        total_duration = time.time() - start_time
        
        # Compile results
        test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_duration_seconds": round(total_duration, 2),
            "endpoint_discovery": endpoint_results,
            "parameter_testing": parameter_results,
            "price_vs_quote_comparison": comparison_results,
            "working_endpoint": working_endpoint,
            "summary": self._generate_test_summary(endpoint_results, parameter_results, comparison_results)
        }
        
        # Save results
        results_file = f"scripts/tests/jupiter_price_api_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"\n📊 Price API Test Complete!")
        logger.info(f"Duration: {total_duration:.2f} seconds")
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        self._print_test_summary(test_results["summary"])
        
        return test_results

    def _generate_test_summary(self, endpoint_results: Dict, parameter_results: Dict, 
                             comparison_results: Dict) -> Dict[str, Any]:
        """Generate test summary"""
        
        # Endpoint analysis
        accessible_endpoints = [ep for ep, result in endpoint_results.items() 
                              if result.get("accessible", False)]
        
        # Parameter analysis
        successful_scenarios = [scenario for scenario, result in parameter_results.items() 
                              if result.get("success", False)]
        
        # Comparison analysis
        price_api_wins = 0
        quote_api_wins = 0
        both_work = 0
        
        for token, comparison in comparison_results.items():
            price_success = comparison.get("price_api_result", {}).get("success", False)
            quote_success = comparison.get("quote_api_result", {}).get("success", False)
            
            if price_success and quote_success:
                both_work += 1
            elif price_success and not quote_success:
                price_api_wins += 1
            elif quote_success and not price_success:
                quote_api_wins += 1
        
        return {
            "endpoint_discovery": {
                "total_endpoints_tested": len(endpoint_results),
                "accessible_endpoints": len(accessible_endpoints),
                "working_endpoints": accessible_endpoints
            },
            "parameter_testing": {
                "total_scenarios_tested": len(parameter_results),
                "successful_scenarios": len(successful_scenarios),
                "success_rate": round(len(successful_scenarios) / len(parameter_results) * 100, 1) if parameter_results else 0
            },
            "api_comparison": {
                "tokens_tested": len(comparison_results),
                "both_apis_work": both_work,
                "price_api_only": price_api_wins,
                "quote_api_only": quote_api_wins,
                "price_api_advantage": price_api_wins > quote_api_wins
            },
            "key_findings": self._identify_key_findings(endpoint_results, parameter_results, comparison_results),
            "recommendations": self._generate_recommendations(endpoint_results, parameter_results, comparison_results)
        }

    def _identify_key_findings(self, endpoint_results: Dict, parameter_results: Dict, 
                             comparison_results: Dict) -> List[str]:
        """Identify key findings from the test"""
        
        findings = []
        
        # Endpoint findings
        accessible_count = sum(1 for result in endpoint_results.values() if result.get("accessible", False))
        if accessible_count == 0:
            findings.append("No Price API endpoints are accessible")
        elif accessible_count == 1:
            findings.append("Only one Price API endpoint is accessible")
        else:
            findings.append(f"{accessible_count} Price API endpoints are accessible")
        
        # Parameter findings
        if parameter_results:
            successful_scenarios = sum(1 for result in parameter_results.values() if result.get("success", False))
            if successful_scenarios == 0:
                findings.append("No parameter combinations work with Price API")
            else:
                findings.append(f"{successful_scenarios} parameter combinations work with Price API")
        
        # Comparison findings
        if comparison_results:
            price_only_wins = sum(1 for comp in comparison_results.values() 
                                if comp.get("price_api_result", {}).get("success", False) 
                                and not comp.get("quote_api_result", {}).get("success", False))
            
            if price_only_wins > 0:
                findings.append(f"Price API works for {price_only_wins} tokens that Quote API cannot handle")
        
        return findings

    def _generate_recommendations(self, endpoint_results: Dict, parameter_results: Dict, 
                                comparison_results: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        # Check if Price API is viable
        accessible_endpoints = [ep for ep, result in endpoint_results.items() if result.get("accessible", False)]
        
        if not accessible_endpoints:
            recommendations.append("Price API is not currently accessible - continue using Quote API")
        else:
            successful_scenarios = sum(1 for result in parameter_results.values() if result.get("success", False))
            
            if successful_scenarios > 0:
                recommendations.append("Price API is functional and could be used for pricing")
                
                # Compare with Quote API
                if comparison_results:
                    price_wins = sum(1 for comp in comparison_results.values() 
                                   if comp.get("price_api_result", {}).get("success", False) 
                                   and not comp.get("quote_api_result", {}).get("success", False))
                    
                    if price_wins > 0:
                        recommendations.append("Price API could serve as fallback when Quote API fails")
                    else:
                        recommendations.append("Quote API appears more reliable than Price API")
            else:
                recommendations.append("Price API endpoints accessible but parameter combinations need refinement")
        
        return recommendations

    def _print_test_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 JUPITER PRICE API TEST SUMMARY")
        logger.info("=" * 80)
        
        # Endpoint discovery
        endpoint_info = summary["endpoint_discovery"]
        logger.info(f"\n📡 Endpoint Discovery:")
        logger.info(f"   Endpoints tested: {endpoint_info['total_endpoints_tested']}")
        logger.info(f"   Accessible endpoints: {endpoint_info['accessible_endpoints']}")
        if endpoint_info['working_endpoints']:
            logger.info(f"   Working endpoints:")
            for endpoint in endpoint_info['working_endpoints']:
                logger.info(f"     • {endpoint}")
        
        # Parameter testing
        param_info = summary["parameter_testing"]
        logger.info(f"\n🔧 Parameter Testing:")
        logger.info(f"   Scenarios tested: {param_info['total_scenarios_tested']}")
        logger.info(f"   Successful scenarios: {param_info['successful_scenarios']}")
        logger.info(f"   Success rate: {param_info['success_rate']}%")
        
        # API comparison
        comparison_info = summary["api_comparison"]
        logger.info(f"\n🔄 API Comparison:")
        logger.info(f"   Tokens tested: {comparison_info['tokens_tested']}")
        logger.info(f"   Both APIs work: {comparison_info['both_apis_work']}")
        logger.info(f"   Price API only: {comparison_info['price_api_only']}")
        logger.info(f"   Quote API only: {comparison_info['quote_api_only']}")
        
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
    """Main test function"""
    async with JupiterPriceAPITester() as tester:
        await tester.run_comprehensive_price_api_test()

if __name__ == "__main__":
    asyncio.run(main()) 