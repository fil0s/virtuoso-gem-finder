#!/usr/bin/env python3
"""
Test specific token address provided by user
Compare with documentation example to identify differences
"""

import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpecificTokenTester:
    def __init__(self):
        self.session = None
        self.price_api_base = "https://lite-api.jup.ag/price/v2"
        
        # Compare the two token addresses
        self.test_tokens = {
            "user_provided": "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg",  # User's token
            "docs_example": "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4BHqd9iL6bEFELvg",   # From docs screenshot (original)
            "known_working": "So11111111111111111111111111111111111111112"     # SOL for comparison
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_token_addresses(self):
        """Test the specific token addresses and analyze differences"""
        
        logger.info("🔍 Testing specific token addresses...")
        logger.info("=" * 80)
        
        # First, let's compare the addresses character by character
        user_token = self.test_tokens["user_provided"]
        docs_token = self.test_tokens["docs_example"]
        
        logger.info(f"User provided: {user_token}")
        logger.info(f"Docs example:  {docs_token}")
        
        # Find differences
        differences = []
        for i, (u_char, d_char) in enumerate(zip(user_token, docs_token)):
            if u_char != d_char:
                differences.append(f"Position {i}: '{u_char}' vs '{d_char}'")
        
        if differences:
            logger.info(f"🔍 Found {len(differences)} differences:")
            for diff in differences:
                logger.info(f"   {diff}")
        else:
            logger.info("✅ Token addresses are identical")
        
        logger.info("=" * 80)
        
        # Test each token
        results = {}
        
        for token_name, token_address in self.test_tokens.items():
            logger.info(f"\n📊 Testing {token_name}: {token_address}")
            
            try:
                params = {"ids": token_address}
                async with self.session.get(self.price_api_base, params=params) as response:
                    result = {
                        "token_name": token_name,
                        "token_address": token_address,
                        "status_code": response.status,
                        "success": response.status == 200,
                        "response_data": None,
                        "error": None,
                        "price_found": False,
                        "price_value": None
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            result["response_data"] = data
                            
                            # Check if price data exists
                            if isinstance(data, dict) and "data" in data:
                                token_data = data["data"].get(token_address)
                                if token_data and isinstance(token_data, dict) and "price" in token_data:
                                    result["price_found"] = True
                                    result["price_value"] = token_data["price"]
                                    logger.info(f"   ✅ Success: Price = ${token_data['price']}")
                                elif token_data is None:
                                    logger.info(f"   ⚠️ Token exists in response but price is null")
                                else:
                                    logger.info(f"   ⚠️ Unexpected token data structure: {type(token_data)}")
                            else:
                                logger.info(f"   ⚠️ Unexpected response structure")
                                
                        except Exception as e:
                            result["error"] = f"JSON parse error: {e}"
                            logger.error(f"   ❌ JSON parse error: {e}")
                    else:
                        error_text = await response.text()
                        result["error"] = error_text[:200] if error_text else "No error details"
                        logger.info(f"   ❌ HTTP {response.status}: {result['error']}")
                    
                    results[token_name] = result
                    
            except Exception as e:
                logger.error(f"   ❌ Request error: {e}")
                results[token_name] = {
                    "token_name": token_name,
                    "token_address": token_address,
                    "success": False,
                    "error": str(e)
                }
            
            await asyncio.sleep(1)  # Rate limiting
        
        return results

    async def test_with_additional_parameters(self, token_address: str):
        """Test the token with additional parameters to see if it helps"""
        
        logger.info(f"\n🔧 Testing {token_address} with additional parameters...")
        
        test_scenarios = [
            {
                "name": "Basic query",
                "params": {"ids": token_address}
            },
            {
                "name": "With showExtraInfo",
                "params": {"ids": token_address, "showExtraInfo": "true"}
            },
            {
                "name": "With vsToken (USDC)",
                "params": {"ids": token_address, "vsToken": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}
            },
            {
                "name": "With vsToken (SOL)",
                "params": {"ids": token_address, "vsToken": "So11111111111111111111111111111111111111112"}
            }
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            logger.info(f"   Testing: {scenario['name']}")
            
            try:
                async with self.session.get(self.price_api_base, params=scenario["params"]) as response:
                    result = {
                        "scenario": scenario["name"],
                        "params": scenario["params"],
                        "status_code": response.status,
                        "success": response.status == 200,
                        "has_price": False,
                        "response_data": None
                    }
                    
                    if response.status == 200:
                        data = await response.json()
                        result["response_data"] = data
                        
                        # Check for price
                        if isinstance(data, dict) and "data" in data:
                            token_data = data["data"].get(token_address)
                            if token_data and isinstance(token_data, dict) and "price" in token_data:
                                result["has_price"] = True
                                logger.info(f"      ✅ Price found: ${token_data['price']}")
                            else:
                                logger.info(f"      ⚠️ No price data (token_data: {type(token_data)})")
                    else:
                        logger.info(f"      ❌ HTTP {response.status}")
                    
                    results[scenario["name"]] = result
                    
            except Exception as e:
                logger.error(f"      ❌ Error: {e}")
                results[scenario["name"]] = {"error": str(e)}
            
            await asyncio.sleep(1)
        
        return results

    async def check_token_in_jupiter_lists(self, token_address: str):
        """Check if the token exists in Jupiter's token lists"""
        
        logger.info(f"\n📋 Checking if {token_address} exists in Jupiter token lists...")
        
        # Try both lite-api and regular API token lists
        endpoints = [
            "https://lite-api.jup.ag/tokens",
            "https://token.jup.ag/all"
        ]
        
        for endpoint in endpoints:
            logger.info(f"   Checking: {endpoint}")
            
            try:
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        tokens = await response.json()
                        
                        # Search for the token
                        found = False
                        if isinstance(tokens, list):
                            for token in tokens:
                                if isinstance(token, dict) and token.get("address") == token_address:
                                    found = True
                                    logger.info(f"      ✅ Found token: {token.get('name', 'Unknown')} ({token.get('symbol', 'Unknown')})")
                                    break
                        
                        if not found:
                            logger.info(f"      ❌ Token not found in {len(tokens) if isinstance(tokens, list) else 'unknown'} tokens")
                    else:
                        logger.info(f"      ❌ HTTP {response.status}")
                        
            except Exception as e:
                logger.error(f"      ❌ Error: {e}")
            
            await asyncio.sleep(1)

    async def run_comprehensive_test(self):
        """Run comprehensive test of the specific token"""
        
        logger.info("🚀 Starting Specific Token Test")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test token addresses
        address_results = await self.test_token_addresses()
        
        # Test user's token with additional parameters
        user_token = self.test_tokens["user_provided"]
        param_results = await self.test_with_additional_parameters(user_token)
        
        # Check token lists
        await self.check_token_in_jupiter_lists(user_token)
        
        total_duration = time.time() - start_time
        
        # Compile results
        test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_duration_seconds": round(total_duration, 2),
            "token_addresses": self.test_tokens,
            "address_comparison_results": address_results,
            "parameter_test_results": param_results,
            "summary": self._generate_summary(address_results, param_results)
        }
        
        # Save results
        results_file = f"scripts/tests/specific_token_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"\n📊 Specific Token Test Complete!")
        logger.info(f"Duration: {total_duration:.2f} seconds")
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        self._print_summary(test_results["summary"])
        
        return test_results

    def _generate_summary(self, address_results: dict, param_results: dict) -> dict:
        """Generate test summary"""
        
        user_result = address_results.get("user_provided", {})
        docs_result = address_results.get("docs_example", {})
        
        return {
            "user_token_success": user_result.get("success", False),
            "user_token_has_price": user_result.get("price_found", False),
            "docs_token_success": docs_result.get("success", False),
            "docs_token_has_price": docs_result.get("price_found", False),
            "addresses_identical": self.test_tokens["user_provided"] == self.test_tokens["docs_example"],
            "parameter_tests_with_price": sum(1 for result in param_results.values() 
                                            if isinstance(result, dict) and result.get("has_price", False)),
            "total_parameter_tests": len(param_results)
        }

    def _print_summary(self, summary: dict):
        """Print test summary"""
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 SPECIFIC TOKEN TEST SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"User token success: {summary['user_token_success']}")
        logger.info(f"User token has price: {summary['user_token_has_price']}")
        logger.info(f"Docs token success: {summary['docs_token_success']}")
        logger.info(f"Docs token has price: {summary['docs_token_has_price']}")
        logger.info(f"Addresses identical: {summary['addresses_identical']}")
        logger.info(f"Parameter tests with price: {summary['parameter_tests_with_price']}/{summary['total_parameter_tests']}")

async def main():
    """Main test function"""
    async with SpecificTokenTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 