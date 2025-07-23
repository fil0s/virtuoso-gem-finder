#!/usr/bin/env python3
"""
Jupiter Price API Test - Correct Implementation
Testing Jupiter's Price API with the correct endpoint and parameters from official docs
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

class CorrectJupiterPriceAPITester:
    def __init__(self):
        self.session = None
        
        # Correct Price API endpoint from documentation
        self.price_api_base = "https://lite-api.jup.ag/price/v2"
        
        # Test tokens (mix of different types)
        self.test_tokens = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "$michi": "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp",
            "BILLY": "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump",
            "USELESS": "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",
            "Example_from_docs": "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4BHqd9iL6bEFELvg"  # From the docs screenshot
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_basic_price_api(self) -> Dict[str, Any]:
        """Test basic Price API functionality with correct parameters"""
        
        logger.info("🔍 Testing basic Price API functionality...")
        
        test_scenarios = [
            {
                "name": "Single token (SOL)",
                "params": {"ids": self.test_tokens["SOL"]}
            },
            {
                "name": "Single token (USDC)",
                "params": {"ids": self.test_tokens["USDC"]}
            },
            {
                "name": "Single token (JUP)",
                "params": {"ids": self.test_tokens["JUP"]}
            },
            {
                "name": "Multiple tokens",
                "params": {"ids": f"{self.test_tokens['SOL']},{self.test_tokens['USDC']},{self.test_tokens['JUP']}"}
            },
            {
                "name": "Token with vsToken (SOL priced in USDC)",
                "params": {
                    "ids": self.test_tokens["SOL"],
                    "vsToken": self.test_tokens["USDC"]
                }
            },
            {
                "name": "Token with showExtraInfo",
                "params": {
                    "ids": self.test_tokens["SOL"],
                    "showExtraInfo": "true"
                }
            },
            {
                "name": "Meme token ($michi)",
                "params": {"ids": self.test_tokens["$michi"]}
            },
            {
                "name": "Pump.fun token (BILLY)",
                "params": {"ids": self.test_tokens["BILLY"]}
            },
            {
                "name": "Unlisted token (USELESS)",
                "params": {"ids": self.test_tokens["USELESS"]}
            },
            {
                "name": "Example from docs",
                "params": {"ids": self.test_tokens["Example_from_docs"]}
            }
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            logger.info(f"   Testing: {scenario['name']}")
            
            try:
                async with self.session.get(self.price_api_base, params=scenario["params"]) as response:
                    result = {
                        "scenario_name": scenario["name"],
                        "params": scenario["params"],
                        "status_code": response.status,
                        "success": response.status == 200,
                        "content_type": response.headers.get('content-type', 'unknown'),
                        "response_data": None,
                        "error": None,
                        "price_info": {}
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            result["response_data"] = data
                            
                            # Extract price information
                            if isinstance(data, dict) and "data" in data:
                                price_data = data["data"]
                                result["price_info"] = self._extract_price_info(price_data)
                                
                                logger.info(f"     ✅ Success: {len(price_data) if isinstance(price_data, dict) else 'N/A'} tokens")
                                
                                # Log price details
                                if isinstance(price_data, dict):
                                    for token_id, token_data in price_data.items():
                                        if isinstance(token_data, dict) and "price" in token_data:
                                            logger.info(f"        {token_id[:8]}...: ${token_data['price']}")
                            else:
                                logger.info(f"     ✅ Success: Unexpected data structure")
                                
                        except Exception as e:
                            result["error"] = f"JSON parse error: {e}"
                            result["response_text"] = await response.text()
                            logger.warning(f"     ⚠️ JSON parse error: {e}")
                    else:
                        error_text = await response.text()
                        result["error"] = error_text[:300] if error_text else "No error details"
                        logger.info(f"     ❌ Failed: {response.status}")
                    
                    results[scenario["name"]] = result
                    
            except Exception as e:
                logger.error(f"     ❌ Error: {e}")
                results[scenario["name"]] = {
                    "scenario_name": scenario["name"],
                    "params": scenario["params"],
                    "success": False,
                    "error": str(e)
                }
            
            await asyncio.sleep(1)  # Rate limiting
        
        return results

    def _extract_price_info(self, price_data: Dict) -> Dict[str, Any]:
        """Extract and analyze price information from API response"""
        
        price_info = {
            "token_count": 0,
            "successful_prices": 0,
            "price_summary": {},
            "data_structure": "unknown"
        }
        
        if isinstance(price_data, dict):
            price_info["token_count"] = len(price_data)
            price_info["data_structure"] = "token_dict"
            
            for token_id, token_data in price_data.items():
                if isinstance(token_data, dict):
                    if "price" in token_data:
                        price_info["successful_prices"] += 1
                        price_info["price_summary"][token_id[:8]] = {
                            "price": token_data.get("price"),
                            "type": token_data.get("type"),
                            "id": token_data.get("id", "")[:8]
                        }
        
        return price_info

    async def run_comprehensive_test(self):
        """Run comprehensive Price API test with correct implementation"""
        
        logger.info("🚀 Starting Comprehensive Jupiter Price API Test (Correct Implementation)")
        logger.info("=" * 80)
        logger.info(f"Using endpoint: {self.price_api_base}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test basic Price API functionality
        logger.info("\n📊 Testing Price API with correct parameters...")
        price_results = await self.test_basic_price_api()
        
        total_duration = time.time() - start_time
        
        # Compile results
        test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_duration_seconds": round(total_duration, 2),
            "price_api_endpoint": self.price_api_base,
            "price_api_results": price_results,
            "summary": self._generate_summary(price_results)
        }
        
        # Save results
        results_file = f"scripts/tests/correct_price_api_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"\n📊 Price API Test Complete!")
        logger.info(f"Duration: {total_duration:.2f} seconds")
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        self._print_summary(test_results["summary"])
        
        return test_results

    def _generate_summary(self, price_results: Dict) -> Dict[str, Any]:
        """Generate test summary"""
        
        total_scenarios = len(price_results)
        successful_scenarios = sum(1 for result in price_results.values() if result.get("success", False))
        
        # Token analysis
        tokens_with_prices = 0
        for result in price_results.values():
            if result.get("success", False):
                price_info = result.get("price_info", {})
                tokens_with_prices += price_info.get("successful_prices", 0)
        
        return {
            "price_api_performance": {
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": round(successful_scenarios / total_scenarios * 100, 1),
                "tokens_with_prices": tokens_with_prices
            },
            "key_findings": self._identify_findings(price_results),
            "recommendations": self._generate_recommendations(price_results)
        }

    def _identify_findings(self, price_results: Dict) -> List[str]:
        """Identify key findings"""
        
        findings = []
        
        successful_count = sum(1 for result in price_results.values() if result.get("success", False))
        
        if successful_count == 0:
            findings.append("Price API is not functional with current parameters")
        elif successful_count == len(price_results):
            findings.append("Price API works for all tested scenarios")
        else:
            findings.append(f"Price API works for {successful_count}/{len(price_results)} scenarios")
        
        return findings

    def _generate_recommendations(self, price_results: Dict) -> List[str]:
        """Generate recommendations"""
        
        recommendations = []
        
        successful_count = sum(1 for result in price_results.values() if result.get("success", False))
        
        if successful_count > 0:
            recommendations.append("Price API is functional and can be used for pricing")
        else:
            recommendations.append("Price API needs further investigation or different parameters")
        
        return recommendations

    def _print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 JUPITER PRICE API TEST SUMMARY")
        logger.info("=" * 80)
        
        # Price API performance
        perf = summary["price_api_performance"]
        logger.info(f"\n📊 Price API Performance:")
        logger.info(f"   Scenarios tested: {perf['total_scenarios']}")
        logger.info(f"   Successful scenarios: {perf['successful_scenarios']}")
        logger.info(f"   Success rate: {perf['success_rate']}%")
        logger.info(f"   Tokens with prices: {perf['tokens_with_prices']}")
        
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
    async with CorrectJupiterPriceAPITester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 